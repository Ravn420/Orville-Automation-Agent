"""Health check data structures for Orville deployments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HealthCheck:
    """A single health check result."""
    name: str
    available: bool
    version: str | None = None
    detail: str = ""
    required: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "available": self.available,
            "version": self.version,
            "detail": self.detail,
            "required": self.required,
        }
