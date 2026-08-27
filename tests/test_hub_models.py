import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from orville_core.hub_models import DownloadJobManager, HubModelError, HuggingFaceHubClient, MachineCapabilities, check_runtime_compatibility
from orville_core.local_models import LocalModelCatalog, LocalModelRecord


class FakeHub(HuggingFaceHubClient):
    def __init__(self, payload):
        super().__init__(token="test")
        self.payload = payload

    def _request(self, path, params=None):
        if path == "api/models":
            return self.payload
        return self.payload[0]

    def details(self, repo_id, *, machine=None):
        self._validate_repo_id(repo_id)
        return self._decorate(self.payload[0], machine or MachineCapabilities("test", 8, 32 * 1024**3, 100 * 1024**3))


class HubModelTests(unittest.TestCase):
    def setUp(self):
        self.machine = MachineCapabilities("test", 8, 32 * 1024**3, 100 * 1024**3)

    def test_search_infers_capabilities_and_supported_filter(self):
        payload = [{"id": "org/CodeModel", "pipeline_tag": "text-generation", "tags": ["code"], "safetensors": {"total": 4 * 1024**3}, "cardData": {"license": "apache-2.0"}}]
        result = FakeHub(payload).search("code", machine=self.machine, supported_only=True)
        self.assertEqual(result[0]["capabilities"], ["code", "text"])
        self.assertTrue(result[0]["supported"])
        self.assertEqual(result[0]["license"], "apache-2.0")

    def test_large_model_is_hidden_by_supported_only(self):
        payload = [{"id": "org/Large", "pipeline_tag": "text-generation", "safetensors": {"total": 64 * 1024**3}}]
        result = FakeHub(payload).search(machine=self.machine, supported_only=True)
        self.assertEqual(result, [])
        unrestricted = FakeHub(payload).search(machine=self.machine, supported_only=False)
        self.assertFalse(unrestricted[0]["supported"])

    def test_repo_id_is_validated_before_details_request(self):
        with self.assertRaises(HubModelError):
            FakeHub([]).details("../../unsafe")

    def test_download_registers_hub_metadata_without_executing_repository_code(self):
        class Response:
            status = 200
            def __init__(self, body): self.body, self.offset = body, 0
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, size=-1):
                if self.offset >= len(self.body): return b""
                chunk = self.body[self.offset:self.offset + (size if size > 0 else len(self.body))]
                self.offset += len(chunk)
                return chunk
        with tempfile.TemporaryDirectory() as temp:
            payload = [{"id": "org/Model", "pipeline_tag": "text-generation", "safetensors": {"total": 10}, "cardData": {"license": "mit"}, "siblings": [{"rfilename": "config.json", "size": 2}, {"rfilename": "model.safetensors", "size": 6}, {"rfilename": "unsafe.py", "size": 4}]}]
            client = FakeHub(payload)
            def fake_urlopen(request, timeout=30):
                return Response(b"{}" if request.full_url.endswith("config.json?download=true") else b"model!")
            with patch("orville_core.hub_models.urlopen", fake_urlopen):
                catalog = LocalModelCatalog(Path(temp) / "catalog.json")
                progress = []
                record = client.download("org/Model", temp, catalog=catalog, machine=self.machine, progress=lambda done, total: progress.append((done, total)))
            self.assertEqual(record.model_id, "org/Model")
            self.assertEqual(record.license, "mit")
            self.assertEqual(record.metadata["hub_repo_id"], "org/Model")
            self.assertIn("text", record.capabilities)
            self.assertTrue(progress)
            self.assertFalse((Path(temp) / "org__Model" / "unsafe.py").exists())

    def test_runtime_checks_detect_gguf_and_transformers_require_config(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            gguf = root / "model.gguf"
            gguf.write_bytes(b"gguf")
            gguf_record = {"model_id": "org/gguf", "source_path": str(gguf), "file_format": "gguf", "capabilities": ["text"], "metadata": {"size_bytes": 4}}
            ollama = check_runtime_compatibility(gguf_record, "ollama", self.machine)
            self.assertTrue(ollama["compatible"])
            transformer_dir = root / "transformer"
            transformer_dir.mkdir()
            (transformer_dir / "model.safetensors").write_bytes(b"model")
            transformer = check_runtime_compatibility({"model_id": "org/t", "source_path": str(transformer_dir), "file_format": "safetensors", "capabilities": ["text"], "metadata": {}}, "transformers", self.machine)
            self.assertFalse(transformer["compatible"])
            self.assertIn("config.json", " ".join(transformer["reasons"]))

    def test_download_manager_retries_transient_failures_and_records_telemetry(self):
        import time
        from orville_core.hub_models import DownloadRetryableError
        class FakeClient:
            def __init__(self): self.calls = 0
            def details(self, repo_id, *, machine=None): return {"size_bytes": 1, "size_gb": 0.01}
            def _validate_repo_id(self, repo_id): return repo_id
            def download(self, repo_id, destination, **kwargs):
                self.calls += 1
                if self.calls < 3: raise DownloadRetryableError("temporary upstream failure")
                return LocalModelRecord(repo_id, repo_id, str(destination), "directory", "gguf", "abc", capabilities=["text"])
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            client = FakeClient()
            manager = DownloadJobManager(root / "downloads.json", client, LocalModelCatalog(root / "catalog.json"), root / "models")
            job = manager.start("org/retry", max_retries=3)
            for _ in range(80):
                if manager.get(job.job_id).status == "completed": break
                time.sleep(0.1)
            result = manager.get(job.job_id)
            self.assertEqual(result.status, "completed", result.error)
            self.assertEqual(client.calls, 3)
            self.assertEqual(result.retry_count, 2)
            self.assertEqual([item["delay_seconds"] for item in result.retry_telemetry], [1.0, 2.0])
            self.assertIsNone(result.next_retry_at)
            persisted = json.loads((root / "downloads.json").read_text(encoding="utf-8"))["jobs"][0]
            self.assertEqual(persisted["retry_count"], 2)
            self.assertEqual(len(persisted["retry_telemetry"]), 2)

    def test_download_manager_pauses_and_resumes_without_resetting_progress(self):
        import time
        from orville_core.hub_models import DownloadPaused
        class FakeClient:
            def details(self, repo_id, *, machine=None): return {"size_bytes": 100, "size_gb": 0.01}
            def _validate_repo_id(self, repo_id): return repo_id
            def download(self, repo_id, destination, **kwargs):
                callback, pause_event = kwargs["progress"], kwargs["pause_event"]
                for done in range(0, 101, 10):
                    if pause_event.is_set(): raise DownloadPaused()
                    callback(done, 100)
                    time.sleep(0.01)
                raise AssertionError("test should pause before completion")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manager = DownloadJobManager(root / "downloads.json", FakeClient(), LocalModelCatalog(root / "catalog.json"), root / "models")
            job = manager.start("org/model")
            for _ in range(40):
                if manager.get(job.job_id).downloaded_bytes > 0: break
                time.sleep(0.01)
            before = manager.get(job.job_id).downloaded_bytes
            manager.pause(job.job_id)
            for _ in range(40):
                if manager.get(job.job_id).status == "paused": break
                time.sleep(0.01)
            self.assertEqual(manager.get(job.job_id).status, "paused")
            self.assertGreaterEqual(manager.get(job.job_id).downloaded_bytes, before)
            manager.resume(job.job_id)
            for _ in range(40):
                if manager.get(job.job_id).status == "failed": break
                time.sleep(0.01)
            self.assertEqual(manager.get(job.job_id).status, "failed")
            self.assertGreaterEqual(manager.get(job.job_id).downloaded_bytes, before)

    def test_download_manager_persists_progress_and_cancellation(self):
        import time
        class FakeClient:
            def details(self, repo_id, *, machine=None): return {"size_bytes": 100, "size_gb": 0.01}
            def _validate_repo_id(self, repo_id): return repo_id
            def download(self, repo_id, destination, **kwargs):
                callback, cancel_event = kwargs["progress"], kwargs["cancel_event"]
                for done in range(0, 101, 10):
                    if cancel_event.is_set(): raise InterruptedError("cancelled")
                    callback(done, 100)
                    time.sleep(0.01)
                raise AssertionError("test should cancel before completion")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manager = DownloadJobManager(root / "downloads.json", FakeClient(), LocalModelCatalog(root / "catalog.json"), root / "models")
            job = manager.start("org/model")
            for _ in range(30):
                if manager.get(job.job_id).status == "running": break
                time.sleep(0.01)
            for _ in range(40):
                if manager.get(job.job_id).downloaded_bytes > 0: break
                time.sleep(0.01)
            manager.cancel(job.job_id)
            for _ in range(40):
                if manager.get(job.job_id).status == "cancelled": break
                time.sleep(0.01)
            self.assertEqual(manager.get(job.job_id).status, "cancelled")
            self.assertGreater(manager.get(job.job_id).downloaded_bytes, 0)
            restarted = DownloadJobManager(root / "downloads.json", FakeClient(), LocalModelCatalog(root / "catalog.json"), root / "models")
            self.assertEqual(restarted.get(job.job_id).status, "cancelled")


if __name__ == "__main__":
    unittest.main()
