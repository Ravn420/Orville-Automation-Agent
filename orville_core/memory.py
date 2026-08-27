"""Durable, isolated, and user-controlled task/project memory."""
from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4
from typing import Any

from .security import SecretRedactor


_ALLOWED_SCOPES = {"task", "project"}
_MAX_VALUE_BYTES = 100_000


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class MemoryRecord:
    memory_id: str
    scope: str
    owner_id: str
    key: str
    value: Any
    source: str
    created_at: str
    updated_at: str
    expires_at: str | None
    deleted_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MemoryStore:
    """SQLite-backed memory with task/project isolation and explicit retention controls."""

    def __init__(self, database: str | Path) -> None:
        self.database = str(Path(database).expanduser())
        Path(self.database).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout = 30000")
        db.execute("PRAGMA journal_mode = WAL")
        return db

    def _initialize(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS memory_records (
                    memory_id TEXT PRIMARY KEY,
                    scope TEXT NOT NULL CHECK(scope IN ('task', 'project')),
                    owner_id TEXT NOT NULL,
                    memory_key TEXT NOT NULL,
                    value_json TEXT NOT NULL,
                    source TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    expires_at TEXT,
                    deleted_at TEXT,
                    UNIQUE(scope, owner_id, memory_key)
                );
                CREATE INDEX IF NOT EXISTS memory_owner_idx ON memory_records(scope, owner_id, updated_at);
                CREATE INDEX IF NOT EXISTS memory_expiry_idx ON memory_records(expires_at);
                """
            )

    @staticmethod
    def _validate(scope: str, owner_id: str, key: str, value: Any, source: str) -> None:
        if scope not in _ALLOWED_SCOPES:
            raise ValueError("scope must be task or project")
        if not owner_id.strip() or len(owner_id) > 256:
            raise ValueError("owner_id must be non-empty and bounded")
        if not key.strip() or len(key) > 256:
            raise ValueError("key must be non-empty and bounded")
        if not source.strip() or len(source) > 256:
            raise ValueError("source must be non-empty and bounded")
        try:
            encoded = json.dumps(SecretRedactor.redact(value), ensure_ascii=False)
        except (TypeError, ValueError) as exc:
            raise ValueError("value must be JSON serializable") from exc
        if len(encoded.encode("utf-8")) > _MAX_VALUE_BYTES:
            raise ValueError("value exceeds memory size limit")

    @staticmethod
    def _row(row: sqlite3.Row) -> MemoryRecord:
        return MemoryRecord(
            memory_id=row["memory_id"], scope=row["scope"], owner_id=row["owner_id"], key=row["memory_key"],
            value=json.loads(row["value_json"]), source=row["source"], created_at=row["created_at"],
            updated_at=row["updated_at"], expires_at=row["expires_at"], deleted_at=row["deleted_at"],
        )

    @staticmethod
    def _active_clause(now: str) -> str:
        return "deleted_at IS NULL AND (expires_at IS NULL OR expires_at > ?)"

    def put(self, scope: str, owner_id: str, key: str, value: Any, *, source: str = "user", ttl_seconds: int | None = None) -> MemoryRecord:
        self._validate(scope, owner_id, key, value, source)
        if ttl_seconds is not None and not 1 <= ttl_seconds <= 31_536_000:
            raise ValueError("ttl_seconds must be between 1 and 31536000")
        safe_value = SecretRedactor.redact(value)
        now = _now()
        expires_at = (datetime.now(UTC) + timedelta(seconds=ttl_seconds)).isoformat() if ttl_seconds else None
        with self._lock, self._connect() as db:
            row = db.execute("SELECT memory_id, created_at FROM memory_records WHERE scope = ? AND owner_id = ? AND memory_key = ?", (scope, owner_id, key)).fetchone()
            memory_id = row["memory_id"] if row else "mem-" + uuid4().hex[:20]
            created_at = row["created_at"] if row else now
            db.execute(
                """INSERT INTO memory_records(memory_id, scope, owner_id, memory_key, value_json, source, created_at, updated_at, expires_at, deleted_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                   ON CONFLICT(scope, owner_id, memory_key) DO UPDATE SET value_json=excluded.value_json, source=excluded.source,
                   updated_at=excluded.updated_at, expires_at=excluded.expires_at, deleted_at=NULL""",
                (memory_id, scope, owner_id, key, json.dumps(safe_value, ensure_ascii=False, sort_keys=True), source, created_at, now, expires_at),
            )
            return self._row(db.execute("SELECT * FROM memory_records WHERE memory_id = ?", (memory_id,)).fetchone())

    def get(self, scope: str, owner_id: str, key: str) -> MemoryRecord | None:
        if scope not in _ALLOWED_SCOPES:
            raise ValueError("scope must be task or project")
        now = _now()
        with self._connect() as db:
            row = db.execute(f"SELECT * FROM memory_records WHERE scope = ? AND owner_id = ? AND memory_key = ? AND {self._active_clause(now)}", (scope, owner_id, key, now)).fetchone()
        return self._row(row) if row else None

    def list(self, scope: str, owner_id: str, *, include_expired: bool = False) -> list[MemoryRecord]:
        if scope not in _ALLOWED_SCOPES:
            raise ValueError("scope must be task or project")
        now = _now()
        clause = "deleted_at IS NULL" if include_expired else self._active_clause(now)
        args: tuple[Any, ...] = (scope, owner_id) if include_expired else (scope, owner_id, now)
        with self._connect() as db:
            rows = db.execute(f"SELECT * FROM memory_records WHERE scope = ? AND owner_id = ? AND {clause} ORDER BY updated_at DESC", args).fetchall()
        return [self._row(row) for row in rows]

    def delete(self, memory_id: str, *, owner_id: str) -> bool:
        now = _now()
        with self._lock, self._connect() as db:
            cursor = db.execute("UPDATE memory_records SET deleted_at = ?, updated_at = ? WHERE memory_id = ? AND owner_id = ? AND deleted_at IS NULL", (now, now, memory_id, owner_id))
        return cursor.rowcount == 1

    def retention_plan(self, *, now: str | None = None) -> dict[str, Any]:
        current = now or _now()
        with self._connect() as db:
            rows = db.execute("SELECT memory_id, scope, owner_id, memory_key, expires_at FROM memory_records WHERE deleted_at IS NULL AND expires_at IS NOT NULL AND expires_at <= ? ORDER BY expires_at", (current,)).fetchall()
        return {"status": "plan_only", "expired_count": len(rows), "candidates": [dict(row) for row in rows], "destructive_action_required": bool(rows)}

    def purge_expired(self, *, before: str | None = None) -> int:
        cutoff = before or _now()
        now = _now()
        with self._lock, self._connect() as db:
            cursor = db.execute("UPDATE memory_records SET deleted_at = ?, updated_at = ? WHERE deleted_at IS NULL AND expires_at IS NOT NULL AND expires_at <= ?", (now, now, cutoff))
        return cursor.rowcount

    def inspect(self, scope: str, owner_id: str) -> dict[str, Any]:
        records = self.list(scope, owner_id)
        return {"scope": scope, "owner_id": owner_id, "count": len(records), "records": [record.to_dict() for record in records], "isolated": True}
