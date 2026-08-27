from pathlib import Path

from orville_core.local_models import LocalModelCatalog
from orville_core.model_security import ResourceCapacity, ResourceRequest, ResourceScheduler, adapter_compatibility, classify_asset, classify_serialization, inspect_directory


def test_safe_formats_and_closed_asset_taxonomy(tmp_path: Path):
    assert classify_serialization("safetensors") == "safe"
    assert classify_serialization("pickle") == "unsafe"
    assert classify_asset(tmp_path / "adapter-lora.safetensors") == "adapter"
    assert classify_asset(tmp_path / "model-q4.gguf") == "quantized_model"
    assert classify_asset(tmp_path / "tokenizer.json") == "tokenizer"
    assert classify_asset(tmp_path / "config.json") == "configuration"


def test_directory_inspection_never_executes_sidecars(tmp_path: Path):
    root = tmp_path / "model"
    root.mkdir()
    (root / "weights.safetensors").write_bytes(b"weights")
    (root / "unsafe.py").write_text("raise RuntimeError('must never run')", encoding="utf-8")
    report = inspect_directory(root)
    assert report["scripts_detected"] is True
    assert report["execution_policy"] == "never_execute_imported_content"
    assert "unsafe.py" in report["scripts"]


def test_catalog_persists_redacted_security_inventory(tmp_path: Path):
    root = tmp_path / "model"
    root.mkdir()
    (root / "model.safetensors").write_bytes(b"weights")
    (root / "adapter_config.json").write_text("{}", encoding="utf-8")
    record = LocalModelCatalog(tmp_path / "catalog.json").import_model(root, model_id="org/adapter", asset_type="adapter")
    inventory = record.metadata["security_inventory"]
    assert inventory["execution_policy"] == "never_execute_imported_content"
    assert record.asset_type == "adapter"


def test_adapter_compatibility_has_clear_fail_closed_diagnostics():
    result = adapter_compatibility(asset_type="adapter", required_base_model="org/base-v1", selected_base_model="org/base-v2")
    assert result["compatible"] is False
    assert result["diagnostic_code"] == "base_model_mismatch"
    assert "org/base-v1" in result["diagnostic"]


def test_resource_scheduler_rejects_oversubscription_and_releases():
    scheduler = ResourceScheduler(ResourceCapacity(cpu_cores=4, ram_bytes=8_000, gpu_count=1, vram_bytes=4_000, disk_bytes=20_000, max_context_length=8_000, max_concurrency=2, thermal_watts=200, power_watts=250))
    request = ResourceRequest(cpu_cores=2, ram_bytes=4_000, gpu_count=1, vram_bytes=2_000, disk_bytes=10_000, context_length=4_000, concurrency=1, thermal_watts=100, power_watts=120)
    assert scheduler.admit(request).admitted is True
    rejected = scheduler.admit(request)
    assert rejected.admitted is False
    assert "resource_limit_exceeded:gpu_count" in rejected.reasons
    scheduler.release(request)
    assert scheduler.admit(request).admitted is True


def test_activation_fails_closed_without_license_or_provenance(tmp_path: Path):
    asset = tmp_path / "model.gguf"
    asset.write_bytes(b"weights")
    catalog = LocalModelCatalog(tmp_path / "catalog.json")
    catalog.import_model(asset, model_id="org/incomplete", runtime="ollama")
    try:
        catalog.activate("org/incomplete")
    except ValueError as exc:
        assert "missing_license_metadata" in str(exc)
    else:
        raise AssertionError("activation must require explicit license metadata")
