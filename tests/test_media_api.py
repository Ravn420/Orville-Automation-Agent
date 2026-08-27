import time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from orville_core.api import create_app
from orville_core.providers import MediaResponse
from orville_core.local_models import LocalModelCatalog, LocalModelRecord


class FakeMediaProvider:
    def __init__(self, config):
        self.config = config

    def generate(self, request):
        raise AssertionError("text path should not be used")

    def stream(self, request):
        raise AssertionError("stream path should not be used")

    def embed(self, inputs):
        raise AssertionError("embedding path should not be used")

    def health_check(self):
        return {"ok": True, "provider_id": self.config.provider_id, "model": self.config.model}

    def generate_media(self, request):
        return MediaResponse(self.config.provider_id, self.config.model, request.modality, [{"type": request.modality, "url": "https://cdn.example.test/asset"}], {"fixture": True})


class FakeHubClient:
    def __init__(self, **kwargs):
        self.token = kwargs.get("token")
    def _validate_repo_id(self, repo_id):
        return repo_id
    def details(self, repo_id, **kwargs):
        return {"model_id": repo_id, "size_bytes": 1, "size_gb": 0.01}
    def search(self, query, **kwargs):
        return [{"model_id": "org/Small", "supported": True, "capabilities": ["text"], "size_gb": 1.0}]
    def download(self, repo_id, destination, **kwargs):
        return LocalModelRecord(repo_id, repo_id, str(destination), "directory", "safetensors", "abc", capabilities=["text"], license="mit", metadata={"hub_repo_id": repo_id})


def test_hub_routes_report_machine_and_gate_downloads():
    with TemporaryDirectory() as directory:
        with patch("orville_core.api.HuggingFaceHubClient", FakeHubClient):
            app = create_app(api_token="hub-token", storage="json", checkpoint_dir=Path(directory) / ".orville")
            client = TestClient(app)
            headers = {"Authorization": "Bearer hub-token"}
            machine = client.get("/api/v1/models/machine", headers=headers)
            assert machine.status_code == 200
            assert "cpu_cores" in machine.json()["capabilities"]
            search = client.post("/api/v1/models/hub/search", headers=headers, json={"query": "small", "supported_only": True})
            assert search.status_code == 200
            assert search.json()["models"][0]["model_id"] == "org/Small"
            pending = client.post("/api/v1/models/hub/download", headers=headers, json={"repo_id": "org/Small"})
            assert pending.status_code == 409
            traversal = client.post("/api/v1/models/hub/download", headers=headers, json={"repo_id": "org/Small", "destination": "..\\outside", "approved": True})
            assert traversal.status_code == 400
            queued = client.post("/api/v1/models/hub/download", headers=headers, json={"repo_id": "org/Small", "approved": True, "max_retries": 4})
            assert queued.status_code == 200, queued.text
            assert queued.json()["download"]["max_retries"] == 4
            job_id = queued.json()["download"]["job_id"]
            for _ in range(20):
                current = client.get(f"/api/v1/models/hub/downloads/{job_id}", headers=headers).json()["download"]
                if current["status"] == "completed":
                    break
                time.sleep(0.05)
            assert current["status"] == "completed"


def test_local_model_activation_exposes_generation_provider_and_pause_is_approval_gated():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        model_path = root / "models" / "tiny.gguf"
        model_path.parent.mkdir()
        model_path.write_bytes(b"fake model")
        catalog = LocalModelCatalog(root / "orville-models.json")
        catalog.import_model(model_path, model_id="org/tiny", capabilities=["text", "code"])
        app = create_app(api_token="local-token", storage="json", checkpoint_dir=root / ".orville")
        client = TestClient(app)
        headers = {"Authorization": "Bearer local-token"}
        listed = client.get("/api/v1/models/local", headers=headers)
        assert listed.status_code == 200
        assert listed.json()["models"][0]["status"] == "imported"
        blocked = client.post("/api/v1/models/hub/downloads/missing/pause", headers=headers, json={})
        assert blocked.status_code == 409
        activated = client.post("/api/v1/models/local/org%2Ftiny/activate", headers=headers, json={"runtime": "llama_cpp", "endpoint": "http://127.0.0.1:8000/v1", "approved": True})
        assert activated.status_code == 200, activated.text
        assert activated.json()["provider"]["provider_id"] == "local:org/tiny"
        providers = client.get("/api/v1/providers", headers=headers)
        assert any(item["provider_id"] == "local:org/tiny" and item["provider_type"] == "openai-compatible-local" for item in providers.json()["providers"])


def test_media_endpoint_routes_image_and_rejects_missing_video_capability():
    with TemporaryDirectory() as directory:
        with patch("orville_core.api.create_provider", side_effect=lambda config: FakeMediaProvider(config)):
            app = create_app(api_token="media-token", storage="json", checkpoint_dir=Path(directory) / ".orville")
            client = TestClient(app)
            headers = {"Authorization": "Bearer media-token"}
            registered = client.post("/api/v1/providers", headers=headers, json={"provider_id": "horde-image", "provider_type": "stable-horde", "model": "sdxl", "base_url": "https://aihorde.net/api", "capabilities": ["image_generation"]})
            assert registered.status_code == 200, registered.text
            generated = client.post("/api/v1/generate/media", headers=headers, json={"provider_id": "horde-image", "modality": "image", "prompt": "A signal room", "options": {"width": 640, "height": 384}})
            assert generated.status_code == 200, generated.text
            assert generated.json()["assets"][0]["type"] == "image"
            rejected = client.post("/api/v1/generate/media", headers=headers, json={"provider_id": "horde-image", "modality": "video", "prompt": "A moving signal room"})
            assert rejected.status_code == 400
            assert "video_generation" in rejected.json()["detail"]


def test_local_model_import_validation_license_activation_and_safe_removal_workflow():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        model_path = root / "models" / "workflow.gguf"
        model_path.parent.mkdir()
        model_path.write_bytes(b"workflow model")
        app = create_app(api_token="workflow-token", storage="json", checkpoint_dir=root / ".orville")
        client = TestClient(app)
        headers = {"Authorization": "Bearer workflow-token"}
        imported = client.post("/api/v1/models/local/import", headers=headers, json={
            "source": str(model_path),
            "model_id": "org/workflow",
            "capabilities": ["text", "code", "streaming"],
            "license": "apache-2.0",
            "license_restrictions": ["review-commercial-use"],
            "provenance": {"repository": "https://example.test/workflow", "revision": "r1"},
            "ownership": {"owner_id": "test-user", "owner_type": "user"},
            "approved": True,
        })
        assert imported.status_code == 200, imported.text
        assert imported.json()["model"]["provenance"]["revision"] == "r1"
        model_id = "org%2Fworkflow"
        validation = client.get(f"/api/v1/models/local/{model_id}/validate?runtime=llama_cpp", headers=headers)
        assert validation.status_code == 200, validation.text
        assert validation.json()["validation"]["status"] == "valid"
        assert any(item["code"] == "license_restriction" for item in validation.json()["validation"]["diagnostics"])
        blocked = client.post(f"/api/v1/models/local/{model_id}/activate", headers=headers, json={"runtime": "llama_cpp", "endpoint": "http://127.0.0.1:8000/v1", "approved": True})
        assert blocked.status_code == 400
        activated = client.post(f"/api/v1/models/local/{model_id}/activate", headers=headers, json={"runtime": "llama_cpp", "endpoint": "http://127.0.0.1:8000/v1", "accept_license_restrictions": True, "approved": True})
        assert activated.status_code == 200, activated.text
        objective = client.post("/api/v1/objectives", headers=headers, json={"objective": "Use the local model to stream a code response", "generation_mode": "code", "local_only": True, "provider_id": "local:org/workflow"})
        assert objective.status_code == 200, objective.text
        assert "agent.plan" in objective.json()["task_ids"]
        deactivated = client.post(f"/api/v1/models/local/{model_id}/deactivate", headers=headers, json={"approved": True})
        assert deactivated.status_code == 200, deactivated.text
        removed = client.request("DELETE", f"/api/v1/models/local/{model_id}", headers=headers, json={"approved": True})
        assert removed.status_code == 200, removed.text
        assert model_path.exists()
