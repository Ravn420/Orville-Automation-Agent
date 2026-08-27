"""Lifecycle, metadata, and safety regression tests for local model imports."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from orville_core.local_models import LocalModelCatalog
from orville_core.security import SecurityViolation


def make_catalog(tmp_path: Path) -> tuple[LocalModelCatalog, Path]:
    catalog = LocalModelCatalog(tmp_path / "catalog.json")
    asset = tmp_path / "model.gguf"
    asset.write_bytes(b"synthetic-gguf-model")
    return catalog, asset


def test_import_preserves_metadata_and_provider_configuration(tmp_path: Path) -> None:
    catalog, asset = make_catalog(tmp_path)

    record = catalog.import_model(
        asset,
        model_id="local/demo",
        display_name="Demo model",
        runtime="ollama",
        endpoint="http://localhost:11434",
        license="apache-2.0",
        license_restrictions=["review-before-production"],
        provenance={"source": "synthetic-fixture"},
        ownership={"owner": "test-user"},
        metadata={"estimated_ram_bytes": 1024},
    )

    assert record.display_name == "Demo model"
    assert record.license == "apache-2.0"
    assert record.license_restrictions == ["review-before-production"]
    assert record.provenance["source"] == "synthetic-fixture"
    assert record.ownership["owner"] == "test-user"
    assert record.checksum_sha256
    assert catalog.verify_checksum("local/demo")["matches"] is True
    provider = catalog.provider_config("local/demo")
    assert provider.provider_id == "local:local/demo"
    assert provider.base_url == "http://localhost:11434"
    assert provider.local_model_id == "local/demo"


def test_duplicate_detection_and_explicit_deduplication(tmp_path: Path) -> None:
    catalog, asset = make_catalog(tmp_path)
    catalog.import_model(asset, model_id="local/first")

    with pytest.raises(ValueError, match="duplicates registered model local/first"):
        catalog.import_model(asset, model_id="local/second")

    duplicate = catalog.import_model(asset, model_id="local/second", deduplicate=True)
    assert duplicate.metadata["deduplicated"] is True
    assert duplicate.source_path == str(asset.resolve())
    assert len(catalog.list_models()) == 2


def test_copy_storage_and_checksum_detect_changes(tmp_path: Path) -> None:
    catalog, asset = make_catalog(tmp_path)
    record = catalog.import_model(
        asset,
        model_id="local/copied",
        storage_root=tmp_path / "models",
        storage_mode="copy",
    )
    stored = Path(record.source_path)
    assert stored.is_file()
    assert stored != asset.resolve()
    stored.write_bytes(b"tampered-model")

    verification = catalog.verify_checksum("local/copied")
    assert verification["matches"] is False
    result = catalog.validate("local/copied", required_runtime="ollama")
    assert result["status"] == "invalid"
    assert any(item["code"] == "corrupted_or_changed" for item in result["diagnostics"])


def test_validation_reports_unsupported_format_and_runtime_mismatch(tmp_path: Path) -> None:
    catalog = LocalModelCatalog(tmp_path / "catalog.json")
    asset = tmp_path / "unsafe.pkl"
    asset.write_bytes(b"not-a-real-pickle-model")
    catalog.import_model(asset, model_id="local/unsafe", runtime="transformers")

    result = catalog.validate("local/unsafe", required_runtime="transformers")
    codes = {item["code"] for item in result["diagnostics"]}
    assert result["status"] == "invalid"
    assert "unsupported_format" in codes

    gguf = tmp_path / "runtime.gguf"
    gguf.write_bytes(b"valid-format-fixture")
    catalog.import_model(gguf, model_id="local/runtime", runtime="ollama")
    mismatch = catalog.validate("local/runtime", required_runtime="transformers")
    assert mismatch["checks"]["runtime_configured"] is True
    assert mismatch["status"] == "invalid"
    assert any(item["code"] == "runtime_mismatch" for item in mismatch["diagnostics"])


def test_validation_reports_resource_and_hardware_constraints(tmp_path: Path) -> None:
    catalog, asset = make_catalog(tmp_path)
    catalog.import_model(
        asset,
        model_id="local/resource-heavy",
        runtime="ollama",
        metadata={
            "required_ram_bytes": 100,
            "required_vram_bytes": 200,
            "requires_gpu": True,
        },
    )

    result = catalog.validate(
        "local/resource-heavy",
        available_ram_bytes=1,
        available_vram_bytes=1,
        hardware={"gpu_available": False},
    )
    codes = {item["code"] for item in result["diagnostics"]}
    assert result["status"] == "invalid"
    assert {"insufficient_ram", "insufficient_vram", "incompatible_hardware"} <= codes


def test_dry_run_does_not_mutate_or_activate_model(tmp_path: Path) -> None:
    catalog, asset = make_catalog(tmp_path)
    catalog.import_model(asset, model_id="local/dry-run", runtime="ollama", endpoint="http://localhost:11434")
    before = json.loads((tmp_path / "catalog.json").read_text(encoding="utf-8"))

    result = catalog.dry_run("local/dry-run", required_runtime="ollama")

    after = json.loads((tmp_path / "catalog.json").read_text(encoding="utf-8"))
    assert result["mode"] == "validation_only"
    assert result["executed"] is False
    assert result["catalog_mutated"] is False
    assert result["would_activate"] is True
    assert before == after
    assert catalog.get("local/dry-run").status == "imported"


def test_activation_deactivation_and_deletion_confirmation(tmp_path: Path) -> None:
    catalog, asset = make_catalog(tmp_path)
    catalog.import_model(asset, model_id="local/lifecycle", runtime="ollama", endpoint="http://localhost:11434", license="apache-2.0", provenance={"source": "synthetic-fixture"})

    active = catalog.activate("local/lifecycle", required_runtime="ollama")
    assert active.status == "active"
    inactive = catalog.deactivate("local/lifecycle")
    assert inactive.status == "inactive"

    with pytest.raises(SecurityViolation, match="explicit external confirmation"):
        catalog.remove("local/lifecycle", delete_files=True)
    assert catalog.get("local/lifecycle").status == "inactive"

    catalog.remove("local/lifecycle")
    with pytest.raises(KeyError, match="local model not found"):
        catalog.get("local/lifecycle")


def test_directory_import_extracts_config_metadata_and_rejects_missing_asset(tmp_path: Path) -> None:
    catalog = LocalModelCatalog(tmp_path / "catalog.json")
    model_dir = tmp_path / "transformer"
    model_dir.mkdir()
    (model_dir / "config.json").write_text(
        json.dumps({"architectures": ["DemoForCausalLM"], "model_type": "demo"}),
        encoding="utf-8",
    )
    (model_dir / "model.safetensors").write_bytes(b"weights")
    record = catalog.import_model(model_dir, model_id="local/dir", runtime="transformers")
    assert record.file_format == "safetensors"
    assert record.metadata["model_type"] == "demo"
    assert record.metadata["architectures"] == ["DemoForCausalLM"]

    missing = catalog.validate("local/dir")
    assert "missing_runtime" not in {item["code"] for item in missing["diagnostics"]}
    (model_dir / "model.safetensors").unlink()
    changed = catalog.validate("local/dir", required_runtime="transformers")
    assert changed["status"] == "invalid"
    assert any(item["code"] == "corrupted_or_changed" for item in changed["diagnostics"])
