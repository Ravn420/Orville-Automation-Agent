"""Secret-reference and append-only audit primitives for production hardening."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


_SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|token|secret|password|authorization)\s*[\"']?\s*[:=]\s*[\"']?[^\s,;\"']+"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]+"),
)
_TOKEN_SHAPED_PATTERN = re.compile(r"(?i)\b(?:sk|bbx|tok|key|secret)[_-][A-Za-z0-9._~+/=-]{8,}\b")
_BEARER_PATTERN = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+")
_SENSITIVE_FIELD_PATTERN = re.compile(r"(?i)(api[_-]?key|token|secret|password|authorization|credential|account(?:[_-]?(?:id|identifier|email))?)")
_ACCOUNT_VALUE_PATTERN = re.compile(r"(?i)\baccount(?:[_ -]?(?:id|identifier|email))?\s*[:=]?\s*[A-Za-z0-9][A-Za-z0-9._-]{7,}")


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class SecretReference:
    reference_id: str
    name: str
    environment: str
    provider: str
    created_at: str = field(default_factory=_now)
    rotated_at: str | None = None


@dataclass(frozen=True)
class AuditRecord:
    audit_id: str
    actor_id: str
    project_id: str | None
    action: str
    target: str
    outcome: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now)


class SecretScanner:
    @classmethod
    def find(cls, value: Any) -> tuple[str, ...]:
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
        matches: list[str] = []
        for pattern in _SECRET_PATTERNS:
            matches.extend(match.group(0) for match in pattern.finditer(text))
        return tuple(matches)

    @classmethod
    def redact(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: "[REDACTED]" if _SENSITIVE_FIELD_PATTERN.search(str(key)) else cls.redact(item) for key, item in value.items()}
        if isinstance(value, list):
            return [cls.redact(item) for item in value]
        if isinstance(value, str):
            output = _BEARER_PATTERN.sub("Bearer [REDACTED]", value)
            output = _ACCOUNT_VALUE_PATTERN.sub("account=[REDACTED]", output)
            for pattern in _SECRET_PATTERNS:
                output = pattern.sub(lambda match: match.group(0).split("=")[0].split(":")[0] + "=[REDACTED]", output)
            return _TOKEN_SHAPED_PATTERN.sub("[REDACTED]", output)
        return value


class SecretReferenceStore:
    """Stores only references and hashes; values remain in the process environment."""

    def __init__(self, database: str | Path) -> None:
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        db = self._connect()
        try:
            db.execute("""CREATE TABLE IF NOT EXISTS secret_references (
                reference_id TEXT PRIMARY KEY, name TEXT NOT NULL, environment TEXT NOT NULL,
                provider TEXT NOT NULL, created_at TEXT NOT NULL, rotated_at TEXT,
                UNIQUE(name, environment)
            )""")
        finally:
            db.close()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        return db

    def register(self, name: str, environment: str, provider: str) -> SecretReference:
        if not name or not environment or not provider:
            raise ValueError("secret name, environment, and provider are required")
        reference_id = "secret-ref-" + hashlib.sha256(f"{name}|{environment}|{provider}".encode()).hexdigest()[:16]
        reference = SecretReference(reference_id, name, environment, provider)
        db = self._connect()
        try:
            db.execute("INSERT INTO secret_references(reference_id, name, environment, provider, created_at) VALUES (?, ?, ?, ?, ?) ON CONFLICT(name, environment) DO UPDATE SET provider=excluded.provider", tuple(reference.__dict__[key] for key in ("reference_id", "name", "environment", "provider", "created_at")))
        finally:
            db.close()
        return reference

    def resolve_for_process(self, reference_id: str) -> str:
        db = self._connect()
        try:
            row = db.execute("SELECT name FROM secret_references WHERE reference_id = ?", (reference_id,)).fetchone()
        finally:
            db.close()
        if row is None:
            raise KeyError(f"secret reference not found: {reference_id}")
        value = os.getenv(row["name"])
        if not value:
            raise RuntimeError(f"secret is not configured in the process environment: {row['name']}")
        return value

    def list_references(self) -> tuple[SecretReference, ...]:
        db = self._connect()
        try:
            rows = db.execute("SELECT reference_id, name, environment, provider, created_at, rotated_at FROM secret_references ORDER BY name").fetchall()
        finally:
            db.close()
        return tuple(SecretReference(**dict(row)) for row in rows)


class AuditStore:
    def __init__(self, database: str | Path) -> None:
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        try:
            db.execute("""CREATE TABLE IF NOT EXISTS audit_records (
                audit_id TEXT PRIMARY KEY, actor_id TEXT NOT NULL, project_id TEXT,
                action TEXT NOT NULL, target TEXT NOT NULL, outcome TEXT NOT NULL,
                metadata TEXT NOT NULL, created_at TEXT NOT NULL
            )""")
        finally:
            db.close()

    def append(self, actor_id: str, action: str, target: str, outcome: str, *, project_id: str | None = None, metadata: dict[str, Any] | None = None) -> AuditRecord:
        record = AuditRecord("audit-" + hashlib.sha256(f"{actor_id}|{action}|{target}|{_now()}".encode()).hexdigest()[:16], actor_id, project_id, action, target, outcome, SecretScanner.redact(metadata or {}))
        db = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        try:
            db.execute("INSERT INTO audit_records VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (record.audit_id, record.actor_id, record.project_id, record.action, record.target, record.outcome, json.dumps(record.metadata), record.created_at))
        finally:
            db.close()
        return record
