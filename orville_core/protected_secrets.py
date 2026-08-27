"""Runtime-only protected secret resolution for enterprise deployments.

Secret values are never persisted by this module. The durable store contains
only references, provider metadata, version markers, and rotation timestamps.
Values are resolved from an injected resolver (environment by default) for the
shortest possible operation window and can be scrubbed from a mutable mapping.
"""
from __future__ import annotations

import os
import re
import secrets
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, MutableMapping


class ProtectedSecretError(RuntimeError):
    """Raised when a protected secret cannot be safely resolved."""


@dataclass(frozen=True)
class ProtectedSecretReference:
    reference_id: str
    name: str
    provider: str
    environment: str
    version: int
    status: str
    rotated_at: float | None


class ProtectedSecretStore:
    """Persist secret metadata while resolving values only at runtime."""

    def __init__(self, database: str | Path, resolver: Callable[[str], str | None] | None = None) -> None:
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self._resolver = resolver or os.getenv
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS protected_secrets (
                reference_id TEXT PRIMARY KEY, name TEXT NOT NULL, provider TEXT NOT NULL,
                environment TEXT NOT NULL, version INTEGER NOT NULL, status TEXT NOT NULL,
                rotated_at REAL, created_at REAL NOT NULL, UNIQUE(name, environment)
            )""")

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.database, timeout=30, isolation_level="IMMEDIATE")
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        return db

    def register(self, name: str, provider: str, environment: str) -> ProtectedSecretReference:
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{1,127}", name):
            raise ProtectedSecretError("secret name must be an uppercase environment-variable identifier")
        if not provider.strip() or not environment.strip():
            raise ProtectedSecretError("provider and environment are required")
        reference_id = "protected-" + secrets.token_hex(12)
        now = time.time()
        with self._connect() as db:
            existing = db.execute("SELECT reference_id, name, provider, environment, version, status, rotated_at FROM protected_secrets WHERE name=? AND environment=?", (name, environment)).fetchone()
            if existing:
                return ProtectedSecretReference(**dict(existing))
            db.execute("INSERT INTO protected_secrets VALUES (?, ?, ?, ?, 1, 'active', NULL, ?)", (reference_id, name, provider, environment, now))
        return ProtectedSecretReference(reference_id, name, provider, environment, 1, "active", None)

    def resolve(self, reference_id: str) -> str:
        with self._connect() as db:
            row = db.execute("SELECT name, status FROM protected_secrets WHERE reference_id=?", (reference_id,)).fetchone()
        if row is None or row["status"] != "active":
            raise ProtectedSecretError("secret reference is missing or inactive")
        value = self._resolver(str(row["name"]))
        if not value:
            raise ProtectedSecretError("secret value is unavailable from the configured runtime resolver")
        return value

    def rotate(self, reference_id: str, new_name: str | None = None) -> ProtectedSecretReference:
        with self._connect() as db:
            row = db.execute("SELECT * FROM protected_secrets WHERE reference_id=?", (reference_id,)).fetchone()
            if row is None or row["status"] != "active":
                raise ProtectedSecretError("cannot rotate missing or inactive secret reference")
            target = new_name or str(row["name"])
            if not re.fullmatch(r"[A-Z][A-Z0-9_]{1,127}", target):
                raise ProtectedSecretError("rotated secret name is invalid")
            version = int(row["version"]) + 1
            rotated_at = time.time()
            db.execute("UPDATE protected_secrets SET name=?, version=?, rotated_at=? WHERE reference_id=?", (target, version, rotated_at, reference_id))
            return ProtectedSecretReference(reference_id, target, row["provider"], row["environment"], version, "active", rotated_at)

    def revoke(self, reference_id: str) -> None:
        with self._connect() as db:
            db.execute("UPDATE protected_secrets SET status='revoked', rotated_at=? WHERE reference_id=?", (time.time(), reference_id))

    def list_metadata(self) -> tuple[ProtectedSecretReference, ...]:
        with self._connect() as db:
            rows = db.execute("SELECT reference_id, name, provider, environment, version, status, rotated_at FROM protected_secrets ORDER BY reference_id").fetchall()
        return tuple(ProtectedSecretReference(**dict(row)) for row in rows)

    def redacted_export(self) -> dict[str, object]:
        return {"schema": "orville.protected-secrets.metadata", "secrets": [{"reference_id": item.reference_id, "name": item.name, "provider": item.provider, "environment": item.environment, "version": item.version, "status": item.status, "rotated_at": item.rotated_at} for item in self.list_metadata()]}

    @staticmethod
    def scrub(mapping: MutableMapping[str, object], secret_names: Mapping[str, str] | None = None) -> None:
        """Remove secret values from a mutable runtime mapping after use."""
        for key in tuple((secret_names or {}).keys()):
            if key in mapping:
                mapping[key] = "[SCRUBBED]"
