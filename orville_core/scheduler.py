"""Durable scheduling and inbound-event controls for workflow automation."""

from __future__ import annotations

import hashlib
import hmac
import sqlite3
import json
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Schedule:
    schedule_id: str
    workflow_id: str
    interval_seconds: int
    enabled: bool = False
    next_run_at: str | None = None
    lease_owner: str | None = None
    lease_until: str | None = None


@dataclass(frozen=True)
class ScheduleExecution:
    execution_id: str
    schedule_id: str
    started_at: str
    finished_at: str | None
    status: str
    error: str = ""
    outputs: dict[str, Any] = field(default_factory=dict)
    artifacts: tuple[dict[str, Any], ...] = ()
    cost_units: float = 0.0
    cost_currency: str = ""
    connector_actions: tuple[dict[str, Any], ...] = ()
    approvals: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class InboundEvent:
    event_id: str
    source: str
    event_type: str
    payload: dict[str, Any]
    accepted: bool
    reason: str = ""


def _now() -> datetime:
    return datetime.now(UTC)


class ScheduleStore:
    def __init__(self, database: str | Path) -> None:
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        try:
            db.execute("""CREATE TABLE IF NOT EXISTS schedules (
                schedule_id TEXT PRIMARY KEY, workflow_id TEXT NOT NULL,
                interval_seconds INTEGER NOT NULL, enabled INTEGER NOT NULL,
                next_run_at TEXT, lease_owner TEXT, lease_until TEXT
            )""")
            columns = {row[1] for row in db.execute("PRAGMA table_info(schedules)").fetchall()}
            if "lease_owner" not in columns:
                db.execute("ALTER TABLE schedules ADD COLUMN lease_owner TEXT")
            if "lease_until" not in columns:
                db.execute("ALTER TABLE schedules ADD COLUMN lease_until TEXT")
            db.execute("""CREATE TABLE IF NOT EXISTS schedule_executions (
                execution_id TEXT PRIMARY KEY, schedule_id TEXT NOT NULL,
                started_at TEXT NOT NULL, finished_at TEXT, status TEXT NOT NULL, error TEXT NOT NULL,
                outputs_json TEXT NOT NULL DEFAULT '{}', artifacts_json TEXT NOT NULL DEFAULT '[]',
                cost_units REAL NOT NULL DEFAULT 0, cost_currency TEXT NOT NULL DEFAULT '',
                connector_actions_json TEXT NOT NULL DEFAULT '[]', approvals_json TEXT NOT NULL DEFAULT '[]'
            )""")
            execution_columns = {row[1] for row in db.execute("PRAGMA table_info(schedule_executions)").fetchall()}
            for name, definition in {
                "outputs_json": "TEXT NOT NULL DEFAULT '{}'",
                "artifacts_json": "TEXT NOT NULL DEFAULT '[]'",
                "cost_units": "REAL NOT NULL DEFAULT 0",
                "cost_currency": "TEXT NOT NULL DEFAULT ''",
                "connector_actions_json": "TEXT NOT NULL DEFAULT '[]'",
                "approvals_json": "TEXT NOT NULL DEFAULT '[]'",
            }.items():
                if name not in execution_columns:
                    db.execute(f"ALTER TABLE schedule_executions ADD COLUMN {name} {definition}")
        finally:
            db.close()

    def create(self, schedule_id: str, workflow_id: str, interval_seconds: int) -> Schedule:
        if interval_seconds < 1:
            raise ValueError("interval_seconds must be positive")
        next_run = (_now() + timedelta(seconds=interval_seconds)).isoformat()
        schedule = Schedule(schedule_id, workflow_id, interval_seconds, False, next_run)
        db = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        try:
            db.execute("INSERT INTO schedules (schedule_id, workflow_id, interval_seconds, enabled, next_run_at, lease_owner, lease_until) VALUES (?, ?, ?, ?, ?, NULL, NULL)", (schedule.schedule_id, schedule.workflow_id, schedule.interval_seconds, int(schedule.enabled), schedule.next_run_at))
        finally:
            db.close()
        return schedule

    def set_enabled(self, schedule_id: str, enabled: bool) -> Schedule:
        db = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        try:
            db.execute("UPDATE schedules SET enabled = ? WHERE schedule_id = ?", (int(enabled), schedule_id))
            row = db.execute("SELECT * FROM schedules WHERE schedule_id = ?", (schedule_id,)).fetchone()
        finally:
            db.close()
        if row is None:
            raise KeyError(f"schedule not found: {schedule_id}")
        return Schedule(row[0], row[1], row[2], bool(row[3]), row[4], row[5], row[6])

    def list(self) -> tuple[Schedule, ...]:
        db = sqlite3.connect(self.database, timeout=30)
        try:
            rows = db.execute("SELECT * FROM schedules ORDER BY schedule_id").fetchall()
        finally:
            db.close()
        return tuple(Schedule(row[0], row[1], row[2], bool(row[3]), row[4], row[5], row[6]) for row in rows)

    def due(self, now: datetime | None = None) -> tuple[Schedule, ...]:
        current = (now or _now()).isoformat()
        db = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        try:
            rows = db.execute("SELECT * FROM schedules WHERE enabled = 1 AND next_run_at <= ? ORDER BY next_run_at", (current,)).fetchall()
        finally:
            db.close()
        return tuple(Schedule(row[0], row[1], row[2], bool(row[3]), row[4], row[5], row[6]) for row in rows)

    def start_execution(self, schedule_id: str, *, execution_id: str, started_at: datetime | None = None) -> ScheduleExecution:
        self._get(schedule_id)
        started = (started_at or _now()).isoformat()
        db = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            existing = db.execute("SELECT * FROM schedule_executions WHERE execution_id = ?", (execution_id,)).fetchone()
            if existing is not None:
                if existing["status"] in {"failed", "cancelled"}:
                    db.execute("UPDATE schedule_executions SET started_at = ?, finished_at = NULL, status = 'running', error = '' WHERE execution_id = ?", (started, execution_id))
                    existing = db.execute("SELECT * FROM schedule_executions WHERE execution_id = ?", (execution_id,)).fetchone()
                return self._execution_from_row(existing)
            execution = ScheduleExecution(execution_id, schedule_id, started, None, "running")
            db.execute("INSERT INTO schedule_executions (execution_id, schedule_id, started_at, finished_at, status, error, outputs_json, artifacts_json, cost_units, cost_currency, connector_actions_json, approvals_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (execution.execution_id, execution.schedule_id, execution.started_at, execution.finished_at, execution.status, execution.error, "{}", "[]", 0.0, "", "[]", "[]"))
            return execution
        finally:
            db.close()

    def finish_execution(self, execution_id: str, *, status: str, error: str = "", finished_at: datetime | None = None, outputs: dict[str, Any] | None = None, artifacts: tuple[dict[str, Any], ...] | list[dict[str, Any]] = (), cost_units: float = 0.0, cost_currency: str = "", connector_actions: tuple[dict[str, Any], ...] | list[dict[str, Any]] = (), approvals: tuple[dict[str, Any], ...] | list[dict[str, Any]] = ()) -> ScheduleExecution:
        if status not in {"completed", "failed", "cancelled"}:
            raise ValueError("invalid execution status")
        db = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        try:
            if cost_units < 0:
                raise ValueError("cost_units must not be negative")
            serialized = (json.dumps(outputs or {}, ensure_ascii=False)[:100_000], json.dumps(list(artifacts), ensure_ascii=False)[:100_000], float(cost_units), str(cost_currency)[:20], json.dumps(list(connector_actions), ensure_ascii=False)[:100_000], json.dumps(list(approvals), ensure_ascii=False)[:100_000])
            db.execute("UPDATE schedule_executions SET finished_at = ?, status = ?, error = ?, outputs_json = ?, artifacts_json = ?, cost_units = ?, cost_currency = ?, connector_actions_json = ?, approvals_json = ? WHERE execution_id = ?", ((finished_at or _now()).isoformat(), status, error[:2_000], *serialized, execution_id))
            row = db.execute("SELECT * FROM schedule_executions WHERE execution_id = ?", (execution_id,)).fetchone()
        finally:
            db.close()
        if row is None:
            raise KeyError(f"execution not found: {execution_id}")
        return self._execution_from_row(row)

    @staticmethod
    def _execution_from_row(row: sqlite3.Row | tuple) -> ScheduleExecution:
        values = list(row)
        if len(values) < 12:
            values.extend(["{}", "[]", 0.0, "", "[]", "[]"])
        return ScheduleExecution(values[0], values[1], values[2], values[3], values[4], values[5], json.loads(values[6] or "{}"), tuple(json.loads(values[7] or "[]")), float(values[8] or 0.0), values[9] or "", tuple(json.loads(values[10] or "[]")), tuple(json.loads(values[11] or "[]")))

    def history(self, schedule_id: str, *, limit: int = 100) -> tuple[ScheduleExecution, ...]:
        self._get(schedule_id)
        db = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        try:
            rows = db.execute("SELECT * FROM schedule_executions WHERE schedule_id = ? ORDER BY started_at DESC LIMIT ?", (schedule_id, max(1, min(limit, 500)))).fetchall()
        finally:
            db.close()
        return tuple(self._execution_from_row(row) for row in rows)

    def _get(self, schedule_id: str) -> tuple:
        db = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        try:
            row = db.execute("SELECT * FROM schedules WHERE schedule_id = ?", (schedule_id,)).fetchone()
        finally:
            db.close()
        if row is None:
            raise KeyError(f"schedule not found: {schedule_id}")
        return row

    def claim(self, schedule_id: str, *, now: datetime | None = None, worker_id: str = "local", lease_seconds: int = 300) -> Schedule:
        current = now or _now()
        if lease_seconds < 1:
            raise ValueError("lease_seconds must be positive")
        lease_until = (current + timedelta(seconds=lease_seconds)).isoformat()
        db = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        try:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM schedules WHERE schedule_id = ?", (schedule_id,)).fetchone()
            if row is None:
                db.rollback()
                raise KeyError(f"schedule not found: {schedule_id}")
            existing_lease = row[6]
            if not row[3]:
                db.rollback()
                raise ValueError("schedule is disabled")
            if existing_lease and existing_lease > current.isoformat() and row[5] not in {None, worker_id}:
                db.rollback()
                raise RuntimeError("schedule is already leased")
            scheduled_for = row[4]
            db.execute("UPDATE schedules SET lease_owner = ?, lease_until = ? WHERE schedule_id = ? AND enabled = 1", (worker_id, lease_until, schedule_id))
            db.commit()
            return Schedule(row[0], row[1], row[2], bool(row[3]), scheduled_for, worker_id, lease_until)
        finally:
            db.close()

    def advance_after_success(self, schedule_id: str, *, worker_id: str, now: datetime | None = None) -> Schedule:
        current = now or _now()
        db = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        try:
            row = db.execute("SELECT * FROM schedules WHERE schedule_id = ? AND lease_owner = ?", (schedule_id, worker_id)).fetchone()
            if row is None:
                raise RuntimeError("schedule is not leased by worker")
            next_run = (current + timedelta(seconds=int(row[2]))).isoformat()
            db.execute("UPDATE schedules SET next_run_at = ? WHERE schedule_id = ? AND lease_owner = ?", (next_run, schedule_id, worker_id))
            return Schedule(row[0], row[1], row[2], bool(row[3]), next_run, row[5], row[6])
        finally:
            db.close()

    def release(self, schedule_id: str, *, worker_id: str) -> Schedule:
        db = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        try:
            db.execute("UPDATE schedules SET lease_owner = NULL, lease_until = NULL WHERE schedule_id = ? AND lease_owner = ?", (schedule_id, worker_id))
            row = db.execute("SELECT * FROM schedules WHERE schedule_id = ?", (schedule_id,)).fetchone()
        finally:
            db.close()
        if row is None:
            raise KeyError(f"schedule not found: {schedule_id}")
        return Schedule(row[0], row[1], row[2], bool(row[3]), row[4], row[5], row[6])

    def recover_stale_leases(self, *, now: datetime | None = None) -> int:
        current = (now or _now()).isoformat()
        db = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        try:
            cursor = db.execute("UPDATE schedules SET lease_owner = NULL, lease_until = NULL WHERE lease_until IS NOT NULL AND lease_until <= ?", (current,))
            return cursor.rowcount
        finally:
            db.close()


class EventIntake:
    def __init__(self, signing_secret: str | None = None, database: str | Path | None = None, *, max_body_bytes: int = 5_000_000, replay_window_seconds: int = 300) -> None:
        self.signing_secret = signing_secret
        self.database = Path(database) if database else None
        self.max_body_bytes = max_body_bytes
        self.replay_window_seconds = replay_window_seconds
        self._seen: set[str] = set()
        if self.database:
            self.database.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.database) as db:
                db.execute("CREATE TABLE IF NOT EXISTS inbound_events (event_id TEXT PRIMARY KEY, received_at REAL NOT NULL, source TEXT NOT NULL, event_type TEXT NOT NULL, accepted INTEGER NOT NULL DEFAULT 0, reason TEXT NOT NULL DEFAULT '')")
                columns = {row[1] for row in db.execute("PRAGMA table_info(inbound_events)").fetchall()}
                if "accepted" not in columns:
                    db.execute("ALTER TABLE inbound_events ADD COLUMN accepted INTEGER NOT NULL DEFAULT 0")
                if "reason" not in columns:
                    db.execute("ALTER TABLE inbound_events ADD COLUMN reason TEXT NOT NULL DEFAULT ''")

    def verify_signature(self, body: bytes, signature: str | None) -> bool:
        if not self.signing_secret or not signature or len(body) > self.max_body_bytes:
            return False
        timestamp: int | None = None
        candidate = signature
        if signature.startswith("t=") and ",v1=" in signature:
            raw_time, candidate = signature.split(",v1=", 1)
            try:
                timestamp = int(raw_time[2:])
            except ValueError:
                return False
            if abs(time.time() - timestamp) > self.replay_window_seconds:
                return False
            body = f"{timestamp}.".encode() + body
        expected = hmac.new(self.signing_secret.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, candidate)

    def accept(self, event_id: str, source: str, event_type: str, payload: dict[str, Any], *, signature_body: bytes | None = None, signature: str | None = None) -> InboundEvent:
        body = signature_body or b""
        if not event_id or len(event_id) > 240 or not source or len(source) > 240 or not event_type or len(event_type) > 240:
            return InboundEvent(event_id, source, event_type, payload, False, "invalid event metadata")
        if len(body) > self.max_body_bytes:
            return InboundEvent(event_id, source, event_type, payload, False, "payload too large")
        if self.signing_secret and not self.verify_signature(body, signature):
            return InboundEvent(event_id, source, event_type, payload, False, "invalid signature")
        if event_id in self._seen:
            return InboundEvent(event_id, source, event_type, payload, False, "duplicate event")
        if self.database:
            with sqlite3.connect(self.database, timeout=30, isolation_level=None) as db:
                try:
                    db.execute("INSERT INTO inbound_events (event_id, received_at, source, event_type, accepted, reason) VALUES (?, ?, ?, ?, 1, '')", (event_id, time.time(), source, event_type))
                except sqlite3.IntegrityError:
                    return InboundEvent(event_id, source, event_type, payload, False, "duplicate event")
        self._seen.add(event_id)
        return InboundEvent(event_id, source, event_type, payload, True)

    def recent(self, *, limit: int = 100) -> tuple[dict[str, Any], ...]:
        if not self.database:
            return tuple()
        with sqlite3.connect(self.database) as db:
            rows = db.execute("SELECT event_id, received_at, source, event_type, accepted, reason FROM inbound_events ORDER BY received_at DESC LIMIT ?", (max(1, min(limit, 500)),)).fetchall()
        return tuple({"event_id": row[0], "received_at": row[1], "source": row[2], "event_type": row[3], "accepted": bool(row[4]), "reason": row[5]} for row in rows)
