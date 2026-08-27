"""Local usage metering, budgets, and provider health state."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class UsageRecord:
    usage_id: str
    scope: str
    category: str
    provider_id: str | None
    units: float
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0
    status: str = "success"
    metadata: dict[str, Any] | None = None
    recorded_at: str = ""


@dataclass(frozen=True)
class Budget:
    scope: str
    max_units: float
    max_input_tokens: int
    max_output_tokens: int
    max_calls: int
    enabled: bool = True


@dataclass(frozen=True)
class ProviderHealth:
    provider_id: str
    status: str
    consecutive_failures: int
    last_success_at: str | None
    last_failure_at: str | None
    next_retry_at: str | None
    message: str = ""


class UsageHealthStore:
    def __init__(self, database: str | Path, *, failure_threshold: int = 3, cooldown_seconds: int = 60) -> None:
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        with sqlite3.connect(self.database) as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS usage_records (
                    usage_id TEXT PRIMARY KEY, scope TEXT NOT NULL, category TEXT NOT NULL,
                    provider_id TEXT, units REAL NOT NULL, input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL, latency_ms REAL NOT NULL, status TEXT NOT NULL,
                    metadata TEXT NOT NULL, recorded_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS budgets (
                    scope TEXT PRIMARY KEY, max_units REAL NOT NULL, max_input_tokens INTEGER NOT NULL,
                    max_output_tokens INTEGER NOT NULL, max_calls INTEGER NOT NULL, enabled INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS provider_health (
                    provider_id TEXT PRIMARY KEY, status TEXT NOT NULL, consecutive_failures INTEGER NOT NULL,
                    last_success_at TEXT, last_failure_at TEXT, next_retry_at TEXT, message TEXT NOT NULL
                );
            """)

    @contextmanager
    def _session(self):
        db = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            yield db
        finally:
            db.close()

    def set_budget(self, budget: Budget) -> Budget:
        with self._session() as db:
            db.execute("INSERT INTO budgets VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(scope) DO UPDATE SET max_units=excluded.max_units, max_input_tokens=excluded.max_input_tokens, max_output_tokens=excluded.max_output_tokens, max_calls=excluded.max_calls, enabled=excluded.enabled", (budget.scope, budget.max_units, budget.max_input_tokens, budget.max_output_tokens, budget.max_calls, int(budget.enabled)))
        return self.get_budget(budget.scope)

    def get_budget(self, scope: str) -> Budget:
        with self._session() as db:
            row = db.execute("SELECT * FROM budgets WHERE scope = ?", (scope,)).fetchone()
        if row is None:
            raise KeyError(f"budget not found: {scope}")
        return Budget(row["scope"], row["max_units"], row["max_input_tokens"], row["max_output_tokens"], row["max_calls"], bool(row["enabled"]))

    def usage(self, scope: str, *, since: str | None = None) -> dict[str, float]:
        query = "SELECT COALESCE(SUM(units),0), COALESCE(SUM(input_tokens),0), COALESCE(SUM(output_tokens),0), COUNT(*) FROM usage_records WHERE scope = ?"
        args: list[Any] = [scope]
        if since:
            query += " AND recorded_at >= ?"
            args.append(since)
        with self._session() as db:
            row = db.execute(query, args).fetchone()
        return {"units": float(row[0]), "input_tokens": float(row[1]), "output_tokens": float(row[2]), "calls": float(row[3])}

    def can_spend(self, scope: str, *, units: float = 0, input_tokens: int = 0, output_tokens: int = 0, calls: int = 1) -> tuple[bool, str]:
        try:
            budget = self.get_budget(scope)
        except KeyError:
            return True, "no budget configured"
        if not budget.enabled:
            return True, "budget disabled"
        current = self.usage(scope)
        checks = ((current["units"] + units, budget.max_units, "units"), (current["input_tokens"] + input_tokens, budget.max_input_tokens, "input tokens"), (current["output_tokens"] + output_tokens, budget.max_output_tokens, "output tokens"), (current["calls"] + calls, budget.max_calls, "calls"))
        for value, maximum, label in checks:
            if maximum >= 0 and value > maximum:
                return False, f"{label} budget exceeded"
        return True, "within budget"

    def record(self, *, scope: str, category: str, provider_id: str | None = None, units: float = 0, input_tokens: int = 0, output_tokens: int = 0, latency_ms: float = 0, status: str = "success", metadata: dict[str, Any] | None = None) -> UsageRecord:
        allowed, reason = self.can_spend(scope, units=units, input_tokens=input_tokens, output_tokens=output_tokens)
        if not allowed:
            raise PermissionError(reason)
        record = UsageRecord(uuid4().hex, scope, category, provider_id, units, input_tokens, output_tokens, latency_ms, status, metadata or {}, _now())
        import json
        with self._session() as db:
            db.execute("INSERT INTO usage_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (record.usage_id, record.scope, record.category, record.provider_id, record.units, record.input_tokens, record.output_tokens, record.latency_ms, record.status, json.dumps(record.metadata), record.recorded_at))
        return record

    def provider_health(self, provider_id: str) -> ProviderHealth:
        with self._session() as db:
            row = db.execute("SELECT * FROM provider_health WHERE provider_id = ?", (provider_id,)).fetchone()
        if row is None:
            return ProviderHealth(provider_id, "unknown", 0, None, None, None)
        return ProviderHealth(row["provider_id"], row["status"], row["consecutive_failures"], row["last_success_at"], row["last_failure_at"], row["next_retry_at"], row["message"])

    def provider_available(self, provider_id: str) -> bool:
        health = self.provider_health(provider_id)
        if health.status != "open":
            return True
        if not health.next_retry_at:
            return False
        return datetime.fromisoformat(health.next_retry_at) <= datetime.now(UTC)

    def record_provider_result(self, provider_id: str, *, success: bool, message: str = "") -> ProviderHealth:
        current = self.provider_health(provider_id)
        now = _now()
        if success:
            health = ProviderHealth(provider_id, "closed", 0, now, current.last_failure_at, None, message[:500])
        else:
            failures = current.consecutive_failures + 1
            status = "open" if failures >= self.failure_threshold else "degraded"
            retry = (datetime.now(UTC) + timedelta(seconds=self.cooldown_seconds * max(1, failures - self.failure_threshold + 1))).isoformat() if status == "open" else None
            health = ProviderHealth(provider_id, status, failures, current.last_success_at, now, retry, message[:500])
        with self._session() as db:
            db.execute("INSERT INTO provider_health VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(provider_id) DO UPDATE SET status=excluded.status, consecutive_failures=excluded.consecutive_failures, last_success_at=excluded.last_success_at, last_failure_at=excluded.last_failure_at, next_retry_at=excluded.next_retry_at, message=excluded.message", (health.provider_id, health.status, health.consecutive_failures, health.last_success_at, health.last_failure_at, health.next_retry_at, health.message))
        return health
