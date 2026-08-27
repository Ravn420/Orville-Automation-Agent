"""Non-executing safety checks for imported model assets.

This module classifies serialization formats, validates adapter/base-model
relationships, and reports optional attestations. It never deserializes or
loads model files.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


SAFE_FORMATS = frozenset({"gguf", "safetensors", "onnx"})
UNSAFE_FORMATS = frozenset({"pkl", "pickle", "pt", "pth", "bin", "joblib"})


@dataclass(frozen=True)
class ModelSafetyReport:
    format_class: str
    scripts_detected: bool
    adapter_compatible: bool
    attestation_status: str
    diagnostics: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_class": self.format_class,
            "scripts_detected": self.scripts_detected,
            "adapter_compatible": self.adapter_compatible,
            "attestation_status": self.attestation_status,
            "diagnostics": list(self.diagnostics),
        }


def classify_format(file_format: str, path: Path) -> str:
    suffixes = {path.suffix.lower().lstrip(".")} if path.is_file() else {item.suffix.lower().lstrip(".") for item in path.rglob("*") if item.is_file()}
    values = {file_format.lower(), *suffixes}
    if values & UNSAFE_FORMATS:
        return "unsafe_serialization"
    if values & SAFE_FORMATS:
        return "safe_serialization"
    return "unknown_serialization"


def inspect_safety(*, file_format: str, path: Path, asset_type: str, base_model: str | None = None, selected_base_model: str | None = None, attestation: dict[str, Any] | None = None) -> ModelSafetyReport:
    diagnostics: list[dict[str, Any]] = []
    format_class = classify_format(file_format, path)
    if format_class == "unsafe_serialization":
        diagnostics.append({"code": "unsafe_serialization", "message": "format may contain executable serialization payloads; do not load it in the host process", "severity": "error"})
    elif format_class == "unknown_serialization":
        diagnostics.append({"code": "unknown_serialization", "message": "serialization safety is unknown; use a reviewed safe format such as GGUF or safetensors", "severity": "warning"})
    scripts = any(item.suffix.lower() in { ".py", ".sh", ".ps1", ".bat", ".cmd"} for item in path.rglob("*") if item.is_file()) if path.is_dir() else False
    if scripts:
        diagnostics.append({"code": "model_scripts_present", "message": "model directory contains scripts; scripts are never executed by Orville", "severity": "warning"})
    compatible = not (asset_type == "adapter" and base_model and selected_base_model and base_model != selected_base_model)
    if not compatible:
        diagnostics.append({"code": "base_model_mismatch", "message": f"adapter requires base model '{base_model}', but '{selected_base_model}' was selected", "severity": "error"})
    attestation_status = "not_provided"
    if attestation:
        attestation_status = "unverified"
        diagnostics.append({"code": "attestation_unverified", "message": "attestation metadata is preserved but has not been cryptographically verified", "severity": "warning"})
    return ModelSafetyReport(format_class, scripts, compatible, attestation_status, tuple(diagnostics))
