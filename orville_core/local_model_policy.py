"""Safety policy for scanning, activating, and running imported local models."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


class LocalModelPolicyError(ValueError):
    pass


@dataclass(frozen=True)
class LocalModelExecutionPolicy:
    allowed_roots: tuple[Path, ...]
    network_enabled: bool = False
    max_cpu_percent: int = 100
    max_memory_mb: int = 4096
    max_vram_mb: int | None = None
    max_disk_mb: int = 100_000
    max_concurrency: int = 1
    max_context_tokens: int = 32768
    max_generation_tokens: int = 4096
    allow_scripts: bool = False

    def __post_init__(self) -> None:
        if not self.allowed_roots:
            raise LocalModelPolicyError("at least one allowed model root is required")
        if any(value < 1 for value in (self.max_cpu_percent, self.max_memory_mb, self.max_disk_mb, self.max_concurrency, self.max_context_tokens, self.max_generation_tokens)):
            raise LocalModelPolicyError("resource limits must be positive")
        if self.max_cpu_percent > 100 or (self.max_vram_mb is not None and self.max_vram_mb < 1):
            raise LocalModelPolicyError("resource limits are invalid")
        if self.allow_scripts:
            raise LocalModelPolicyError("model-provided scripts are never allowed")

    def validate_path(self, path: str | Path) -> Path:
        candidate = Path(path).expanduser().resolve()
        if not any(candidate == root.resolve() or root.resolve() in candidate.parents for root in self.allowed_roots):
            raise LocalModelPolicyError("model path is outside allowed roots")
        return candidate

    def to_dict(self) -> dict[str, Any]:
        return {"allowed_roots": [str(root) for root in self.allowed_roots], "network_enabled": self.network_enabled, "max_cpu_percent": self.max_cpu_percent, "max_memory_mb": self.max_memory_mb, "max_vram_mb": self.max_vram_mb, "max_disk_mb": self.max_disk_mb, "max_concurrency": self.max_concurrency, "max_context_tokens": self.max_context_tokens, "max_generation_tokens": self.max_generation_tokens, "allow_scripts": self.allow_scripts}
