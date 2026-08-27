from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from orville_core.integration import streaming_model_task_handler
from orville_core.local_models import LocalModelCatalog
from orville_core.model_runtime import probe_runtime_capabilities
from orville_core.providers import LLMResponse, ModelCapabilities, ProviderConfig, ProviderError, ProviderRegistry, StreamChunk
from orville_core.routing import ProviderRouter


def test_import_can_copy_to_selected_root_and_reuse_duplicate_by_reference():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "source.gguf"
        source.write_bytes(b"model")
        catalog = LocalModelCatalog(root / "catalog.json")
        first = catalog.import_model(source, model_id="org/first", storage_root=root / "stored", storage_mode="copy")
        second = catalog.import_model(source, model_id="org/second", deduplicate=True)
        assert Path(first.source_path).exists()
        assert second.storage_mode == "reference"
        assert second.source_path == first.source_path or second.source_path == str(source)
        assert second.metadata["deduplicated"] is True


def test_ollama_probe_exposes_only_declared_runtime_modalities():
    with patch("orville_core.model_runtime._get_json", return_value=(True, {"models": [{"name": "vision-model"}]}, None)):
        report = probe_runtime_capabilities("ollama", "http://127.0.0.1:11434", declared={"text", "vision", "image_generation"}, model="vision-model")
    assert report.reachable is True
    assert "vision" in report.exposed_modalities
    assert "image_generation" not in report.exposed_modalities


class FlakyProvider:
    def __init__(self):
        self.config = ProviderConfig("flaky", "test", "model", "https://example.test", capabilities=ModelCapabilities(streaming=True))
        self.calls = 0

    def generate(self, request):
        return LLMResponse("flaky", "model", "", {})

    def stream(self, request):
        self.calls += 1
        yield StreamChunk("flaky", "model", "one")
        if self.calls == 1:
            raise ProviderError("connection lost")
        yield StreamChunk("flaky", "model", "two", finish_reason="stop")

    def embed(self, inputs):
        raise NotImplementedError

    def health_check(self):
        return {"ok": True}


def test_stream_reconnect_resumes_without_duplicate_prefix():
    provider = FlakyProvider()
    registry = ProviderRegistry()
    registry.register(provider)
    handler = streaming_model_task_handler(ProviderRouter(registry))
    task = type("Task", (), {"task_id": "t", "inputs": {"prompt": "hi", "preferred_provider_ids": ["flaky"], "stream_policy": {"reconnect_attempts": 1}}})()
    events = []
    result = handler(task, {"_progress_callback": lambda event, data: events.append(event)})
    assert result["text"] == "onetwo"
    assert "model_stream_reconnected" in events


def test_import_preserves_license_provenance_checksum_and_ownership():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "owned.gguf"
        source.write_bytes(b"owned-model")
        record = LocalModelCatalog(root / "catalog.json").import_model(
            source,
            model_id="org/owned",
            license="apache-2.0",
            license_restrictions=["review-commercial-use"],
            provenance={"repository": "https://example.test/model", "revision": "abc123"},
            ownership={"owner_id": "user-42", "owner_type": "user"},
        )
        assert record.license == "apache-2.0"
        assert record.license_restrictions == ["review-commercial-use"]
        assert record.provenance["revision"] == "abc123"
        assert record.ownership["owner_id"] == "user-42"
        assert record.provenance["checksum_sha256"] == record.checksum_sha256


def test_validation_reports_corruption_format_runtime_and_resources():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "model.xyz"
        source.write_bytes(b"model")
        catalog = LocalModelCatalog(root / "catalog.json")
        record = catalog.import_model(source, model_id="org/model", runtime=None)
        source.write_bytes(b"changed")
        result = catalog.validate(record.model_id, available_ram_bytes=1, hardware={"gpu_available": False})
        codes = {item["code"] for item in result["diagnostics"]}
        assert {"unsupported_format", "corrupted_or_changed", "missing_runtime"}.issubset(codes)


def test_model_safety_classifies_unsafe_serialization_and_preserves_attestation():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "adapter.pth"
        source.write_bytes(b"unsafe-placeholder")
        catalog = LocalModelCatalog(root / "catalog.json")
        record = catalog.import_model(
            source,
            model_id="org/adapter",
            asset_type="adapter",
            base_model="org/base-v1",
            attestation={"type": "sigstore", "value": "synthetic"},
        )
        result = catalog.validate(record.model_id, selected_base_model="org/base-v2")
        codes = {item["code"] for item in result["diagnostics"]}
        assert "unsafe_serialization" in codes
        assert "base_model_mismatch" in codes
        assert result["metadata"]["attestation"]["type"] == "sigstore"
        assert result["safety"]["attestation_status"] == "unverified"
