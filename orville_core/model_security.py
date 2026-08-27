"""Fail-closed security primitives for local model assets and scheduling.

This module only inspects paths and metadata. It never deserializes, imports, or
executes content from a model directory.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

AssetType = Literal["full_model", "adapter", "quantized_model", "tokenizer", "configuration", "auxiliary_asset"]
ASSET_TYPES = frozenset({"full_model", "adapter", "quantized_model", "tokenizer", "configuration", "auxiliary_asset"})
SAFE_SERIALIZATIONS = frozenset({"safetensors", "gguf", "onnx"})
UNSAFE_SERIALIZATIONS = frozenset({"pickle", "pkl", "pt", "pth", "joblib", "dill"})
_SCRIPT_SUFFIXES = frozenset({".py", ".pyc", ".sh", ".bash", ".ps1", ".bat", ".cmd", ".exe", ".dll", ".so"})


def classify_asset(path: str | Path, *, file_format: str | None = None, declared_type: str | None = None, metadata: dict[str, Any] | None = None) -> AssetType:
    """Return one closed asset type without loading the asset."""
    target = Path(path)
    name = target.name.lower()
    metadata = metadata or {}
    if declared_type in ASSET_TYPES:
        return declared_type  # type: ignore[return-value]
    if "adapter" in name or "lora" in name or (target.is_dir() and (target / "adapter_config.json").exists()):
        return "adapter"
    if "tokenizer" in name or name in {"vocab.json", "merges.txt", "tokenizer.json", "special_tokens_map.json"}:
        return "tokenizer"
    if name in {"config.json", "generation_config.json", "preprocessor_config.json"}:
        return "configuration"
    fmt = (file_format or target.suffix.lstrip(".")).lower()
    quantized = bool(metadata.get("quantization_config") or metadata.get("quantized") or fmt in {"gguf", "ggml", "q4", "q5", "q8"})
    if quantized:
        return "quantized_model"
    if target.is_file() and fmt in SAFE_SERIALIZATIONS | UNSAFE_SERIALIZATIONS:
        return "full_model"
    if target.is_dir():
        return "full_model"
    return "auxiliary_asset"


def classify_serialization(file_format: str) -> str:
    fmt = file_format.strip().lower().lstrip(".")
    if fmt in SAFE_SERIALIZATIONS:
        return "safe"
    if fmt in UNSAFE_SERIALIZATIONS:
        return "unsafe"
    return "unknown"


def inspect_directory(path: str | Path) -> dict[str, Any]:
    """Inspect names and sizes only; executable files are never opened or run."""
    root = Path(path).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(root)
    files = [root] if root.is_file() else sorted(item for item in root.rglob("*") if item.is_file())
    scripts = [str(item.relative_to(root.parent if root.is_file() else root)) for item in files if item.suffix.lower() in _SCRIPT_SUFFIXES]
    assets = [{"name": str(item.relative_to(root.parent if root.is_file() else root)), "size_bytes": item.stat().st_size, "asset_type": classify_asset(item)} for item in files]
    return {"root": str(root), "file_count": len(files), "scripts_detected": bool(scripts), "scripts": scripts, "assets": assets, "execution_policy": "never_execute_imported_content"}


def adapter_compatibility(*, asset_type: str, required_base_model: str | None, selected_base_model: str | None) -> dict[str, Any]:
    if asset_type != "adapter":
        return {"compatible": True, "diagnostic_code": None, "diagnostic": "base-model check not applicable"}
    if not required_base_model:
        return {"compatible": False, "diagnostic_code": "adapter_base_model_missing", "diagnostic": "adapter activation requires a declared base-model identity"}
    if not selected_base_model:
        return {"compatible": False, "diagnostic_code": "selected_base_model_missing", "diagnostic": f"select base model '{required_base_model}' before activating this adapter"}
    if required_base_model != selected_base_model:
        return {"compatible": False, "diagnostic_code": "base_model_mismatch", "diagnostic": f"adapter requires base model '{required_base_model}', but '{selected_base_model}' was selected"}
    return {"compatible": True, "diagnostic_code": None, "diagnostic": "adapter base model matches"}


@dataclass(frozen=True)
class ResourceRequest:
    cpu_cores: float = 0
    ram_bytes: int = 0
    gpu_count: int = 0
    vram_bytes: int = 0
    disk_bytes: int = 0
    context_length: int = 0
    concurrency: int = 1
    thermal_watts: float = 0
    power_watts: float = 0


@dataclass(frozen=True)
class ResourceCapacity:
    cpu_cores: float
    ram_bytes: int
    gpu_count: int = 0
    vram_bytes: int = 0
    disk_bytes: int = 0
    max_context_length: int = 0
    max_concurrency: int = 1
    thermal_watts: float = 0
    power_watts: float = 0


@dataclass(frozen=True)
class AdmissionDecision:
    admitted: bool
    reasons: tuple[str, ...] = ()
    remaining: dict[str, float] = field(default_factory=dict)


class ResourceScheduler:
    """Deterministic, non-oversubscribing admission controller."""

    def __init__(self, capacity: ResourceCapacity) -> None:
        self.capacity = capacity
        self._active = ResourceRequest(concurrency=0)

    def admit(self, request: ResourceRequest) -> AdmissionDecision:
        reasons: list[str] = []
        active = self._active
        checks = {
            "cpu_cores": (active.cpu_cores + request.cpu_cores, self.capacity.cpu_cores),
            "ram_bytes": (active.ram_bytes + request.ram_bytes, self.capacity.ram_bytes),
            "gpu_count": (active.gpu_count + request.gpu_count, self.capacity.gpu_count),
            "vram_bytes": (active.vram_bytes + request.vram_bytes, self.capacity.vram_bytes),
            "disk_bytes": (request.disk_bytes, self.capacity.disk_bytes),
            "context_length": (request.context_length, self.capacity.max_context_length),
            "concurrency": (active.concurrency + request.concurrency, self.capacity.max_concurrency),
            "thermal_watts": (active.thermal_watts + request.thermal_watts, self.capacity.thermal_watts),
            "power_watts": (active.power_watts + request.power_watts, self.capacity.power_watts),
        }
        for name, (used, limit) in checks.items():
            if used < 0 or (limit > 0 and used > limit):
                reasons.append(f"resource_limit_exceeded:{name}")
        if request.concurrency < 1:
            reasons.append("invalid_concurrency")
        if reasons:
            return AdmissionDecision(False, tuple(reasons), self.remaining())
        self._active = ResourceRequest(**{field: getattr(active, field) + getattr(request, field) for field in ResourceRequest.__dataclass_fields__})
        return AdmissionDecision(True, (), self.remaining())

    def release(self, request: ResourceRequest) -> None:
        values = {field: max(0, getattr(self._active, field) - getattr(request, field)) for field in ResourceRequest.__dataclass_fields__}
        self._active = ResourceRequest(**values)

    def remaining(self) -> dict[str, float]:
        return {
            "cpu_cores": self.capacity.cpu_cores - self._active.cpu_cores,
            "ram_bytes": self.capacity.ram_bytes - self._active.ram_bytes,
            "gpu_count": self.capacity.gpu_count - self._active.gpu_count,
            "vram_bytes": self.capacity.vram_bytes - self._active.vram_bytes,
            "disk_bytes": self.capacity.disk_bytes,
            "context_length": self.capacity.max_context_length,
            "concurrency": self.capacity.max_concurrency - self._active.concurrency,
            "thermal_watts": self.capacity.thermal_watts - self._active.thermal_watts,
            "power_watts": self.capacity.power_watts - self._active.power_watts,
        }
