"""Durable circuit-breaker state shared by router processes.

SQLite is used as the default backend because it is bundled with Python, works
outside Manus, and supports atomic updates across independent processes.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path


class SQLiteCircuitStateStore:
    """Persist provider failure counters and cooldown timestamps in SQLite."""

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
                    CREATE TABLE IF NOT EXISTS provider_circuit_state (
                        provider_id TEXT PRIMARY KEY,
                        failures INTEGER NOT NULL,
                        last_failure_at REAL NOT NULL,
                        updated_at REAL NOT NULL
                    )
                    """
                )
            finally:
                connection.close()

    def failure_count(self, provider_id: str) -> int:
        row = self._read(provider_id)
        return int(row["failures"]) if row is not None else 0

    def record_failure(self, provider_id: str, *, now: float | None = None) -> int:
        """Atomically increment failures and return the new count."""
        timestamp = time.time() if now is None else float(now)
        with self._lock:
            connection = self._connect()
            try:
                connection.execute("BEGIN IMMEDIATE")
                row = connection.execute(
                    "SELECT failures FROM provider_circuit_state WHERE provider_id = ?",
                    (provider_id,),
                ).fetchone()
                failures = int(row["failures"]) + 1 if row else 1
                connection.execute(
                    """
                    INSERT INTO provider_circuit_state(provider_id, failures, last_failure_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(provider_id) DO UPDATE SET
                        failures = excluded.failures,
                        last_failure_at = excluded.last_failure_at,
                        updated_at = excluded.updated_at
                    """,
                    (provider_id, failures, timestamp, timestamp),
                )
                connection.execute("COMMIT")
                return failures
            except Exception:
                connection.execute("ROLLBACK")
                raise
            finally:
                connection.close()

    def record_success(self, provider_id: str) -> None:
        """Clear provider failures after a successful request."""
        with self._lock:
            connection = self._connect()
            try:
                connection.execute("DELETE FROM provider_circuit_state WHERE provider_id = ?", (provider_id,))
            finally:
                connection.close()

    def state(self, provider_id: str, *, failure_threshold: int, cooldown_seconds: float, now: float | None = None) -> str:
        """Return ``closed``, ``open``, or ``half_open`` from persisted state."""
        row = self._read(provider_id)
        if row is None or int(row["failures"]) < failure_threshold:
            return "closed"
        timestamp = time.time() if now is None else float(now)
        return "open" if timestamp - float(row["last_failure_at"]) < cooldown_seconds else "half_open"

    def _read(self, provider_id: str) -> sqlite3.Row | None:
        with self._lock:
            connection = self._connect()
            try:
                return connection.execute(
                    "SELECT failures, last_failure_at FROM provider_circuit_state WHERE provider_id = ?",
                    (provider_id,),
                ).fetchone()
            finally:
                connection.close()

    def close(self) -> None:
        """Compatibility hook; connections are intentionally short-lived."""
        return None
