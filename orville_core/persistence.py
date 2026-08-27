"""Durable SQLite persistence for Orville execution checkpoints."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import UTC, datetime
from pathlib import Path

from .models import Checkpoint
from .security import SecretRedactor


class SQLiteCheckpointStore:
    """Persist complete checkpoints in SQLite with atomic upserts.

    The class intentionally implements the same methods used by the engine's
    file-backed CheckpointStore so it can be adopted without changing engine
    semantics. SQLite is opened per operation, which keeps the store safe for
    multiple worker threads and process restarts.
    """

    def __init__(self, database: str | Path) -> None:
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 30000")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = FULL")
        return connection

    def _initialize(self) -> None:
        with self._lock:
            connection = self._connect()
            try:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS checkpoints (
                        run_id TEXT PRIMARY KEY,
                        schema_version INTEGER NOT NULL,
                        payload TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
                connection.execute("CREATE INDEX IF NOT EXISTS checkpoints_updated_at_idx ON checkpoints(updated_at)")
            finally:
                connection.close()

    def save(self, checkpoint: Checkpoint) -> Path:
        payload = json.dumps(SecretRedactor.redact(checkpoint.to_dict()), sort_keys=True, ensure_ascii=False)
        updated_at = datetime.now(UTC).isoformat()
        with self._lock:
            connection = self._connect()
            try:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                """
                INSERT INTO checkpoints(run_id, schema_version, payload, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    schema_version = excluded.schema_version,
                    payload = excluded.payload,
                    updated_at = excluded.updated_at
                """,
                (checkpoint.run_id, 1, payload, updated_at),
                )
                connection.execute("COMMIT")
            finally:
                connection.close()
        return self.database

    def load(self, run_id: str) -> Checkpoint:
        with self._lock:
            connection = self._connect()
            try:
                row = connection.execute("SELECT payload FROM checkpoints WHERE run_id = ?", (run_id,)).fetchone()
            finally:
                connection.close()
        if row is None:
            raise FileNotFoundError(f"checkpoint not found for run {run_id}")
        try:
            return Checkpoint.from_dict(json.loads(row["payload"]))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"checkpoint is corrupt for run {run_id}") from exc

    def exists(self, run_id: str) -> bool:
        with self._lock:
            connection = self._connect()
            try:
                row = connection.execute("SELECT 1 FROM checkpoints WHERE run_id = ?", (run_id,)).fetchone()
            finally:
                connection.close()
        return row is not None

    def list_run_ids(self) -> list[str]:
        with self._lock:
            connection = self._connect()
            try:
                rows = connection.execute("SELECT run_id FROM checkpoints ORDER BY updated_at DESC").fetchall()
            finally:
                connection.close()
        return [str(row["run_id"]) for row in rows]

    def close(self) -> None:
        """Compatibility hook; connections are intentionally short-lived."""
        return None
