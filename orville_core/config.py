"""Validated environment configuration for Orville runtime processes."""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimeConfig:
    api_token: str
    host: str = "127.0.0.1"
    port: int = 8787
    storage: str = "sqlite"
    database_path: Path = Path(".orville/orville.db")
    allowed_origins: tuple[str, ...] = ("http://localhost:3000",)
    requests_per_minute: int = 120

    @classmethod
    def from_environment(cls, environment: dict[str, str] | None = None) -> "RuntimeConfig":
        env = environment if environment is not None else os.environ
        token = env.get("ORVILLE_API_TOKEN", "")
        if not token or token == "replace-with-a-high-entropy-secret":
            raise ValueError("ORVILLE_API_TOKEN must be a non-placeholder secret")
        host = env.get("ORVILLE_API_HOST", "127.0.0.1")
        if host not in {"127.0.0.1", "localhost", "0.0.0.0"}:
            raise ValueError("ORVILLE_API_HOST must be localhost, 127.0.0.1, or 0.0.0.0")
        try:
            port = int(env.get("ORVILLE_API_PORT", "8787"))
        except ValueError as exc:
            raise ValueError("ORVILLE_API_PORT must be an integer") from exc
        if not 1 <= port <= 65535:
            raise ValueError("ORVILLE_API_PORT must be between 1 and 65535")
        storage = env.get("ORVILLE_STORAGE", "sqlite").lower()
        if storage not in {"sqlite", "json"}:
            raise ValueError("ORVILLE_STORAGE must be sqlite or json")
        try:
            rpm = int(env.get("ORVILLE_REQUESTS_PER_MINUTE", "120"))
        except ValueError as exc:
            raise ValueError("ORVILLE_REQUESTS_PER_MINUTE must be an integer") from exc
        if rpm < 1:
            raise ValueError("ORVILLE_REQUESTS_PER_MINUTE must be positive")
        origins = tuple(item.strip() for item in env.get("ORVILLE_ALLOWED_ORIGINS", "http://localhost:3000").split(",") if item.strip())
        if not origins:
            raise ValueError("ORVILLE_ALLOWED_ORIGINS must contain at least one origin")
        return cls(token, host, port, storage, Path(env.get("ORVILLE_DB_PATH", ".orville/orville.db")), origins, rpm)

    def redacted(self) -> dict[str, object]:
        return {"host": self.host, "port": self.port, "storage": self.storage, "database_path": str(self.database_path), "allowed_origins": list(self.allowed_origins), "requests_per_minute": self.requests_per_minute, "api_token_configured": bool(self.api_token)}

    @staticmethod
    def generate_token(length: int = 32) -> str:
        if length < 16:
            raise ValueError("generated tokens must be at least 16 characters")
        return secrets.token_urlsafe(length)
