"""Safe, metadata-first cataloging for user-downloaded local model assets."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .attestations import AttestationError, AttestationPolicy, TrustStore, verify_attestation
from .attestation_service import AttestationVerificationService
from .model_safety import inspect_safety
from .model_security import classify_asset, classify_serialization, inspect_directory


@dataclass
class LocalModelRecord:
    model_id: str
    display_name: str
    source_path: str
    asset_type: str
    file_format: str
    checksum_sha256: str
    runtime: str | None = None
    endpoint: str | None = None
    base_model: str | None = None
    capabilities: list[str] | None = None
    license: str | None = None
    status: str = "imported"
    metadata: dict[str, Any] | None = None
    storage_mode: str = "reference"
    provenance: dict[str, Any] = field(default_factory=dict)
    ownership: dict[str, Any] = field(default_factory=dict)
    license_restrictions: list[str] = field(default_factory=list)
    attestation: dict[str, Any] = field(default_factory=dict)
    activation_evidence: dict[str, Any] = field(default_factory=dict)
    safety: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LocalModelRecord":
        values = dict(data)
        values.setdefault("storage_mode", "reference")
        values.setdefault("provenance", {})
        values.setdefault("ownership", {})
        values.setdefault("license_restrictions", [])
        values.setdefault("attestation", {})
        values.setdefault("activation_evidence", {})
        values.setdefault("safety", {})
        return cls(**values)


class LocalModelCatalog:
    """JSON-backed catalog; file inspection does not execute model code."""

    def __init__(self, catalog_path: str | Path, trust_store: TrustStore | None = None) -> None:
        self.catalog_path = Path(catalog_path)
        self.trust_store = trust_store
        self.attestation_service = AttestationVerificationService(trust_store)
        self.catalog_path.parent.mkdir(parents=True, exist_ok=True)

    def list_models(self) -> list[LocalModelRecord]:
        if not self.catalog_path.exists():
            return []
        payload = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        return [LocalModelRecord.from_dict(item) for item in payload.get("models", [])]

    def import_model(
        self,
        source: str | Path,
        *,
        model_id: str,
        display_name: str | None = None,
        runtime: str | None = None,
        endpoint: str | None = None,
        base_model: str | None = None,
        capabilities: list[str] | None = None,
        asset_type: str | None = None,
        license: str | None = None,
        metadata: dict[str, Any] | None = None,
        storage_root: str | Path | None = None,
        storage_mode: str = "reference",
        deduplicate: bool = False,
        provenance: dict[str, Any] | None = None,
        ownership: dict[str, Any] | None = None,
        license_restrictions: list[str] | None = None,
        attestation: dict[str, Any] | None = None,
    ) -> LocalModelRecord:
        path = Path(source).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"local model asset not found: {path}")
        if storage_mode not in {"reference", "copy", "link"}:
            raise ValueError("storage_mode must be reference, copy, or link")
        if not model_id.strip():
            raise ValueError("model_id must not be empty")
        file_format, detected_asset_type, inspected_metadata = self._inspect(path)
        asset_type = asset_type or detected_asset_type
        checksum = self._checksum(path)
        safety_report = inspect_safety(file_format=file_format, path=path, asset_type=asset_type, base_model=base_model, attestation=attestation)
        existing = self.list_models()
        duplicate = next((item for item in existing if item.model_id != model_id and item.checksum_sha256 == checksum), None)
        if duplicate and not deduplicate:
            raise ValueError(f"model asset duplicates registered model {duplicate.model_id}")
        stored_path = path
        original_source = str(path)
        if duplicate and deduplicate:
            stored_path = Path(duplicate.source_path)
            storage_mode = "reference"
        elif storage_root is not None and storage_mode != "reference":
            root = Path(storage_root).expanduser().resolve()
            root.mkdir(parents=True, exist_ok=True)
            target = (root / model_id.replace("/", "__")).resolve()
            if os.path.commonpath([str(root), str(target)]) != str(root):
                raise ValueError("storage destination must remain inside storage_root")
            if target.exists():
                raise FileExistsError(f"storage destination already exists: {target}")
            if storage_mode == "copy":
                if path.is_dir():
                    shutil.copytree(path, target)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, target)
            else:
                target.symlink_to(path, target_is_directory=path.is_dir())
            stored_path = target
        record = LocalModelRecord(
            model_id=model_id,
            display_name=display_name or path.name,
            source_path=str(stored_path),
            asset_type=asset_type,
            file_format=file_format,
            checksum_sha256=checksum,
            runtime=runtime,
            endpoint=endpoint,
            base_model=base_model,
            capabilities=capabilities or (["text", "code"] if file_format in {"gguf", "safetensors"} else []),
            license=license,
            status="imported",
            metadata={**inspected_metadata, "original_source_path": original_source, "deduplicated": bool(duplicate), **(metadata or {})},
            storage_mode=storage_mode,
            provenance={"source_path": original_source, "checksum_sha256": checksum, **(provenance or {})},
            ownership=dict(ownership or {}),
            license_restrictions=list(license_restrictions or []),
            attestation=dict(attestation or {}),
            safety=safety_report.to_dict(),
        )
        models = [item for item in self.list_models() if item.model_id != model_id]
        models.append(record)
        self._write(models)
        return record

    def verify_checksum(self, model_id: str) -> dict[str, Any]:
        record = self.get(model_id)
        path = Path(record.source_path)
        actual = self._checksum(path) if path.exists() else ""
        return {"model_id": model_id, "expected": record.checksum_sha256, "actual": actual, "matches": bool(actual) and actual == record.checksum_sha256}

    def get(self, model_id: str) -> LocalModelRecord:
        for model in self.list_models():
            if model.model_id == model_id:
                return model
        raise KeyError(f"local model not found: {model_id}")

    def validate(self, model_id: str, *, required_runtime: str | None = None, endpoint: str | None = None, available_ram_bytes: int | None = None, available_vram_bytes: int | None = None, hardware: dict[str, Any] | None = None, selected_base_model: str | None = None, attestation_policy: str = "optional", activation: bool = False) -> dict[str, Any]:
        record = self.get(model_id)
        path = Path(record.source_path)
        checks: dict[str, bool] = {"exists": path.exists(), "readable": os.access(path, os.R_OK) if path.exists() else False}
        diagnostics: list[dict[str, Any]] = []
        safety_report = inspect_safety(file_format=record.file_format, path=path, asset_type=record.asset_type, base_model=record.base_model, selected_base_model=selected_base_model, attestation=record.attestation)
        diagnostics.extend(safety_report.diagnostics)
        attestation_evidence = self.attestation_service.verify(subject_digest=record.checksum_sha256, envelope=record.attestation or None, policy_mode=attestation_policy)
        if attestation_evidence.verification_status != "verified":
            diagnostics.append({"code": attestation_evidence.diagnostic_code or "attestation_unverified", "message": attestation_evidence.diagnostic_message or f"attestation status is {attestation_evidence.verification_status}; required policies fail closed", "severity": "error" if attestation_policy in {"required", "required_tuf"} else "warning"})
        checks["attestation_valid"] = self.attestation_service.activation_allowed(attestation_evidence)
        if not checks["exists"]:
            diagnostics.append({"code": "missing_asset", "message": f"model asset is missing: {path}", "severity": "error"})
        if not checks["readable"]:
            diagnostics.append({"code": "unreadable_asset", "message": "model asset is not readable by the current user", "severity": "error"})
        checks["format_supported"] = record.file_format in {"gguf", "safetensors", "bin", "directory"} and safety_report.format_class != "unsafe_serialization"
        if not checks["format_supported"]:
            diagnostics.append({"code": "unsupported_format", "message": f"format '{record.file_format}' is not supported; use GGUF, safetensors, BIN, or a model directory", "severity": "error"})
        try:
            checksum = self._checksum(path) if path.exists() else ""
        except (OSError, ValueError) as exc:
            checksum = ""
            diagnostics.append({"code": "checksum_unreadable", "message": f"could not calculate model checksum: {exc}", "severity": "error"})
        checks["checksum_matches"] = bool(checksum) and checksum == record.checksum_sha256
        if not checks["checksum_matches"]:
            diagnostics.append({"code": "corrupted_or_changed", "message": "model checksum does not match the imported checksum; re-import or restore the original asset", "severity": "error"})
        runtime = (record.runtime or required_runtime or "").lower().replace("-", "_")
        checks["runtime_configured"] = bool(runtime)
        if not checks["runtime_configured"]:
            diagnostics.append({"code": "missing_runtime", "message": "no compatible local runtime has been selected", "severity": "error"})
        checks["runtime_matches_requirement"] = (
            not required_runtime
            or not record.runtime
            or runtime == required_runtime.lower().replace("-", "_")
        )
        if not checks["runtime_matches_requirement"]:
            diagnostics.append({"code": "runtime_mismatch", "message": f"configured runtime '{record.runtime}' does not satisfy required runtime '{required_runtime}'", "severity": "error"})
        checks["endpoint_configured"] = bool(endpoint or record.endpoint) if runtime in {"ollama", "custom", "custom_local", "openai_compatible_local"} else True
        if not checks["endpoint_configured"]:
            diagnostics.append({"code": "missing_runtime_endpoint", "message": f"runtime '{runtime}' requires a configured inference endpoint", "severity": "error"})
        size = path.stat().st_size if path.is_file() else sum(item.stat().st_size for item in path.rglob("*") if item.is_file()) if path.exists() else 0
        free_disk = shutil.disk_usage(path.parent).free
        checks["disk_available"] = free_disk >= max(size, 1)
        if not checks["disk_available"]:
            diagnostics.append({"code": "insufficient_disk", "message": f"insufficient disk space: {free_disk} bytes free, {size} bytes required", "severity": "error"})
        metadata = record.metadata or {}
        required_ram = int(metadata.get("required_ram_bytes", metadata.get("estimated_ram_bytes", 0)) or 0)
        checks["ram_available"] = available_ram_bytes is None or not required_ram or available_ram_bytes >= required_ram
        if not checks["ram_available"]:
            diagnostics.append({"code": "insufficient_ram", "message": "available system RAM is below the model requirement", "severity": "error"})
        required_vram = int(metadata.get("required_vram_bytes", 0) or 0)
        checks["vram_available"] = available_vram_bytes is None or not required_vram or available_vram_bytes >= required_vram
        if not checks["vram_available"]:
            diagnostics.append({"code": "insufficient_vram", "message": "available GPU memory is below the model requirement", "severity": "error"})
        required_gpu = bool(metadata.get("requires_gpu", False))
        has_gpu = bool((hardware or {}).get("gpu_available", False))
        checks["hardware_compatible"] = not required_gpu or has_gpu
        if not checks["hardware_compatible"]:
            diagnostics.append({"code": "incompatible_hardware", "message": "this model requires a compatible GPU, but no supported GPU was detected", "severity": "error"})
        if record.license_restrictions:
            diagnostics.append({"code": "license_restriction", "message": "license restrictions require operator review before activation", "severity": "warning"})
        if activation:
            checks["provenance_recorded"] = bool(record.provenance.get("source") or record.provenance.get("repository") or record.provenance.get("source_path"))
            checks["license_recorded"] = bool(record.license and record.license.strip())
            if not checks["provenance_recorded"]:
                diagnostics.append({"code": "missing_provenance", "message": "activation requires source and provenance metadata", "severity": "error"})
            if not checks["license_recorded"]:
                diagnostics.append({"code": "missing_license_metadata", "message": "activation requires license metadata", "severity": "error"})
        checks["valid"] = all(value for key, value in checks.items() if key != "valid")
        return {"model_id": model_id, "checks": checks, "status": "valid" if checks["valid"] else "invalid", "diagnostics": diagnostics, "safety": safety_report.to_dict(), "metadata": {"license": record.license, "license_restrictions": record.license_restrictions, "provenance": record.provenance, "ownership": record.ownership, "checksum_sha256": record.checksum_sha256, "attestation": record.attestation, "activation_evidence": attestation_evidence.to_dict(), "attestation_policy": attestation_policy}}

    def dry_run(self, model_id: str, *, required_runtime: str | None = None) -> dict[str, Any]:
        """Validate an imported model without activating or executing it."""
        validation = self.validate(model_id, required_runtime=required_runtime)
        return {"mode": "validation_only", "model_id": model_id, "would_activate": bool(validation["checks"]["valid"]), "executed": False, "catalog_mutated": False, "validation": validation}

    def activate(self, model_id: str, *, required_runtime: str | None = None, endpoint: str | None = None, attestation_policy: str = "optional") -> LocalModelRecord:
        validation = self.validate(model_id, required_runtime=required_runtime, endpoint=endpoint, attestation_policy=attestation_policy, activation=True)
        if not validation["checks"]["valid"]:
            raise ValueError(f"local model failed validation: {validation}")
        records = self.list_models()
        updated = None
        for record in records:
            if record.model_id == model_id:
                if required_runtime:
                    record.runtime = required_runtime
                if endpoint:
                    record.endpoint = endpoint
                record.activation_evidence = dict(validation["metadata"]["activation_evidence"])
                record.status = "active"
                updated = record
        if updated is None:
            raise KeyError(f"local model not found: {model_id}")
        self._write(records)
        return updated

    def deactivate(self, model_id: str) -> LocalModelRecord:
        records = self.list_models()
        for record in records:
            if record.model_id == model_id:
                record.status = "inactive"
                self._write(records)
                return record
        raise KeyError(f"local model not found: {model_id}")

    def remove(self, model_id: str, *, delete_files: bool = False) -> None:
        records = self.list_models()
        retained = [record for record in records if record.model_id != model_id]
        if len(retained) == len(records):
            raise KeyError(f"local model not found: {model_id}")
        if delete_files:
            from .security import SecurityViolation
            record = next(record for record in records if record.model_id == model_id)
            raise SecurityViolation("file deletion requires an explicit external confirmation flow")
        self._write(retained)

    def provider_config(self, model_id: str):
        """Return a provider config for a catalogued local model.

        The import catalog remains independent from the provider module; the
        import is local to this bridge to avoid a module-level cycle.
        """
        from .providers import ModelCapabilities, ProviderConfig

        record = self.get(model_id)
        capability_names = set(record.capabilities or [])
        capabilities = ModelCapabilities(
            text="text" in capability_names,
            code="code" in capability_names,
            vision="vision" in capability_names,
            image_generation="image_generation" in capability_names,
            video_generation="video_generation" in capability_names,
            audio="audio" in capability_names,
            embeddings="embeddings" in capability_names,
            structured_output="structured_output" in capability_names,
            tool_calling="tool_calling" in capability_names,
        )
        runtime = (record.runtime or "ollama").lower().replace("-", "_")
        provider_type = "ollama" if runtime == "ollama" else "openai-compatible-local"
        default_endpoint = "http://localhost:11434" if runtime == "ollama" else "http://localhost:8000/v1"
        return ProviderConfig(
            provider_id=f"local:{record.model_id}",
            provider_type=provider_type,
            model=record.model_id,
            base_url=record.endpoint or default_endpoint,
            capabilities=capabilities,
            local_model_id=record.model_id,
        )

    def _write(self, models: list[LocalModelRecord]) -> None:
        payload = {"schema_version": 1, "models": [model.to_dict() for model in models]}
        temporary = self.catalog_path.with_suffix(self.catalog_path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self.catalog_path)

    @staticmethod
    def _inspect(path: Path) -> tuple[str, str, dict[str, Any]]:
        inventory = inspect_directory(path)
        if path.is_file():
            suffix = path.suffix.lower().lstrip(".") or "unknown"
            classified_type = classify_asset(path, file_format=suffix)
            legacy_type = "adapter" if classified_type == "adapter" else "model"
            return suffix, legacy_type, {"size_bytes": path.stat().st_size, "serialization_class": classify_serialization(suffix), "asset_taxonomy": classified_type, "security_inventory": inventory}
        config = path / "config.json"
        metadata: dict[str, Any] = {"file_count": inventory["file_count"], "security_inventory": inventory}
        if config.is_file():
            try:
                raw = json.loads(config.read_text(encoding="utf-8"))
                for key in ("architectures", "model_type", "torch_dtype", "max_position_embeddings", "_name_or_path", "quantization_config"):
                    if key in raw:
                        metadata[key] = raw[key]
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                metadata["config_readable"] = False
        extensions = {item.suffix.lower().lstrip(".") for item in path.rglob("*") if item.is_file()}
        file_format = "safetensors" if "safetensors" in extensions else ("directory" if extensions else "unknown")
        classified_type = classify_asset(path, file_format=file_format, metadata=metadata)
        metadata["asset_taxonomy"] = classified_type
        return file_format, "directory", metadata

    @staticmethod
    def _checksum(path: Path) -> str:
        digest = hashlib.sha256()
        files = [path] if path.is_file() else sorted(item for item in path.rglob("*") if item.is_file())
        for item in files:
            digest.update(str(item.relative_to(path.parent if path.is_file() else path)).encode("utf-8"))
            with item.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
        return digest.hexdigest()
