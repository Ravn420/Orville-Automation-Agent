"""Deterministic workflow automation contracts for Orville.

This module provides a local control-plane implementation. External schedulers,
webhooks, and connector events can be attached through adapters without giving
AI steps unrestricted side effects.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
from dataclasses import dataclass, field
from uuid import uuid4
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Callable


class TriggerType(StrEnum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    WEBHOOK = "webhook"
    DATA = "data"
    CONNECTOR = "connector"
    TASK_EVENT = "task_event"


class RunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"
    WAITING_APPROVAL = "waiting_approval"


class StepExecutionMode(StrEnum):
    """Execution ownership for a workflow step."""

    DETERMINISTIC = "deterministic"
    AGENTIC = "agentic"


SAFETY_CRITICAL_CATEGORIES = frozenset({
    "safety_critical",
    "authorization",
    "validation",
    "persistence",
    "artifact_integrity",
})


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class WorkflowStep:
    step_id: str
    kind: str
    config: dict[str, Any] = field(default_factory=dict)
    requires_approval: bool = False


def step_execution_mode(step: WorkflowStep) -> StepExecutionMode:
    """Return the declared execution mode, defaulting to deterministic."""
    raw_mode = step.config.get("execution_mode", StepExecutionMode.DETERMINISTIC.value)
    try:
        return StepExecutionMode(raw_mode)
    except ValueError as exc:
        raise ValueError(f"unsupported workflow step execution mode: {raw_mode}") from exc


def validate_step_policy(step: WorkflowStep) -> None:
    """Reject agentic implementations for safety-critical workflow categories."""
    mode = step_execution_mode(step)
    category = str(step.config.get("safety_category", "")).strip().lower()
    if category in SAFETY_CRITICAL_CATEGORIES and mode is not StepExecutionMode.DETERMINISTIC:
        raise PermissionError(
            f"safety-critical workflow step must be deterministic: {step.step_id}"
        )


def validate_workflow_steps(steps: tuple[WorkflowStep, ...]) -> None:
    """Validate execution modes for every step before persistence or execution."""
    for step in steps:
        validate_step_policy(step)


@dataclass(frozen=True)
class ApprovalCheckpoint:
    approval_id: str
    run_id: str
    step_id: str
    action_summary: str
    target_summary: str
    status: str
    requested_at: str
    resolved_at: str | None = None
    approver_id: str | None = None
    resolution_reason: str = ""


@dataclass(frozen=True)
class WorkflowVersion:
    version_id: str
    workflow_id: str
    version: int
    trigger: TriggerType
    steps: tuple[WorkflowStep, ...]
    enabled: bool = False
    created_at: str = field(default_factory=_now)


@dataclass(frozen=True)
class WorkflowRun:
    run_id: str
    workflow_id: str
    version_id: str
    idempotency_key: str
    status: RunStatus
    attempts: int = 0
    error: str | None = None
    created_at: str = field(default_factory=_now)


class WorkflowStore:
    def __init__(self, database: str | Path) -> None:
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()

    def _session(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        return db

    def _initialize(self) -> None:
        db = self._session()
        try:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS workflows (workflow_id TEXT PRIMARY KEY, name TEXT NOT NULL, enabled INTEGER NOT NULL, created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS workflow_versions (version_id TEXT PRIMARY KEY, workflow_id TEXT NOT NULL, version INTEGER NOT NULL, trigger_type TEXT NOT NULL, definition TEXT NOT NULL, enabled INTEGER NOT NULL, created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS workflow_runs (run_id TEXT PRIMARY KEY, workflow_id TEXT NOT NULL, version_id TEXT NOT NULL, idempotency_key TEXT NOT NULL UNIQUE, status TEXT NOT NULL, attempts INTEGER NOT NULL, error TEXT, created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS workflow_events (sequence INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL, event_type TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS approval_checkpoints (approval_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, step_id TEXT NOT NULL, action_summary TEXT NOT NULL, target_summary TEXT NOT NULL, status TEXT NOT NULL, requested_at TEXT NOT NULL, resolved_at TEXT, approver_id TEXT, resolution_reason TEXT NOT NULL DEFAULT '');
            """)
        finally:
            db.close()

    def create_workflow(self, name: str) -> str:
        workflow_id = "workflow-" + hashlib.sha256((name + _now()).encode()).hexdigest()[:12]
        db = self._session()
        try:
            db.execute("INSERT INTO workflows VALUES (?, ?, ?, ?)", (workflow_id, name, 0, _now()))
        finally:
            db.close()
        return workflow_id

    def add_version(self, workflow_id: str, trigger: TriggerType, steps: tuple[WorkflowStep, ...]) -> WorkflowVersion:
        db = self._session()
        try:
            row = db.execute("SELECT COALESCE(MAX(version), 0) AS current FROM workflow_versions WHERE workflow_id = ?", (workflow_id,)).fetchone()
            version = int(row["current"]) + 1
            version_id = f"{workflow_id}-v{version}"
            validate_workflow_steps(steps)
            record = WorkflowVersion(version_id, workflow_id, version, trigger, steps)
            definition = json.dumps([{"step_id": step.step_id, "kind": step.kind, "config": step.config, "requires_approval": step.requires_approval} for step in steps])
            db.execute("INSERT INTO workflow_versions VALUES (?, ?, ?, ?, ?, ?, ?)", (version_id, workflow_id, version, trigger.value, definition, 0, record.created_at))
            return record
        finally:
            db.close()

    def enabled_version(self, workflow_id: str) -> WorkflowVersion:
        db = self._session()
        try:
            row = db.execute("SELECT * FROM workflow_versions WHERE workflow_id = ? AND enabled = 1 ORDER BY version DESC LIMIT 1", (workflow_id,)).fetchone()
        finally:
            db.close()
        if row is None:
            raise KeyError(f"enabled workflow version not found: {workflow_id}")
        definition = json.loads(row["definition"])
        steps = tuple(WorkflowStep(item["step_id"], item["kind"], item.get("config", {}), bool(item.get("requires_approval", False))) for item in definition)
        return WorkflowVersion(row["version_id"], row["workflow_id"], row["version"], TriggerType(row["trigger_type"]), steps, bool(row["enabled"]), row["created_at"])

    def set_enabled(self, workflow_id: str, version_id: str, enabled: bool) -> None:
        db = self._session()
        try:
            db.execute("UPDATE workflow_versions SET enabled = ? WHERE version_id = ? AND workflow_id = ?", (int(enabled), version_id, workflow_id))
            db.execute("UPDATE workflows SET enabled = ? WHERE workflow_id = ?", (int(enabled), workflow_id))
        finally:
            db.close()

    def start_run(self, workflow_id: str, version_id: str, idempotency_key: str) -> WorkflowRun:
        db = self._session()
        try:
            existing = db.execute("SELECT * FROM workflow_runs WHERE idempotency_key = ?", (idempotency_key,)).fetchone()
            if existing:
                return WorkflowRun(existing["run_id"], existing["workflow_id"], existing["version_id"], existing["idempotency_key"], RunStatus(existing["status"]), existing["attempts"], existing["error"], existing["created_at"])
            run_id = "run-" + hashlib.sha256((workflow_id + version_id + idempotency_key).encode()).hexdigest()[:16]
            record = WorkflowRun(run_id, workflow_id, version_id, idempotency_key, RunStatus.RUNNING)
            db.execute("INSERT INTO workflow_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (record.run_id, record.workflow_id, record.version_id, record.idempotency_key, record.status.value, record.attempts, record.error, record.created_at))
            return record
        finally:
            db.close()

    def create_approval_checkpoint(self, run_id: str, step_id: str, *, action_summary: str, target_summary: str, requested_at: str | None = None) -> ApprovalCheckpoint:
        """Persist an idempotent, secret-free approval request for a protected step."""
        if not action_summary.strip() or not target_summary.strip():
            raise ValueError("approval checkpoint summaries must not be empty")
        requested = requested_at or _now()
        approval_id = "approval-" + hashlib.sha256(f"{run_id}:{step_id}".encode()).hexdigest()[:20]
        db = self._session()
        try:
            db.execute("INSERT OR IGNORE INTO approval_checkpoints (approval_id, run_id, step_id, action_summary, target_summary, status, requested_at, resolved_at, approver_id, resolution_reason) VALUES (?, ?, ?, ?, ?, 'pending', ?, NULL, NULL, '')", (approval_id, run_id, step_id, action_summary[:500], target_summary[:500], requested))
            row = db.execute("SELECT * FROM approval_checkpoints WHERE approval_id = ?", (approval_id,)).fetchone()
        finally:
            db.close()
        return self._approval_from_row(row)

    def resolve_approval_checkpoint(self, approval_id: str, *, approved: bool, approver_id: str, reason: str = "", resolved_at: str | None = None) -> ApprovalCheckpoint:
        """Resolve a pending checkpoint once; repeated identical resolution is idempotent."""
        if not approver_id.strip():
            raise ValueError("approver_id must not be empty")
        db = self._session()
        try:
            row = db.execute("SELECT * FROM approval_checkpoints WHERE approval_id = ?", (approval_id,)).fetchone()
            if row is None:
                raise KeyError(f"approval checkpoint not found: {approval_id}")
            status = "approved" if approved else "rejected"
            if row[5] == "pending":
                db.execute("UPDATE approval_checkpoints SET status = ?, resolved_at = ?, approver_id = ?, resolution_reason = ? WHERE approval_id = ? AND status = 'pending'", (status, resolved_at or _now(), approver_id[:200], reason[:500], approval_id))
                row = db.execute("SELECT * FROM approval_checkpoints WHERE approval_id = ?", (approval_id,)).fetchone()
        finally:
            db.close()
        return self._approval_from_row(row)

    def approval_checkpoint(self, approval_id: str) -> ApprovalCheckpoint:
        db = self._session()
        try:
            row = db.execute("SELECT * FROM approval_checkpoints WHERE approval_id = ?", (approval_id,)).fetchone()
        finally:
            db.close()
        if row is None:
            raise KeyError(f"approval checkpoint not found: {approval_id}")
        return self._approval_from_row(row)

    @staticmethod
    def _approval_from_row(row: sqlite3.Row | tuple) -> ApprovalCheckpoint:
        return ApprovalCheckpoint(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9])

    def finish_run(self, run_id: str, status: RunStatus, *, error: str | None = None, attempts: int | None = None) -> WorkflowRun:
        db = self._session()
        try:
            current = db.execute("SELECT * FROM workflow_runs WHERE run_id = ?", (run_id,)).fetchone()
            if current is None:
                raise KeyError(f"workflow run not found: {run_id}")
            next_attempts = int(current["attempts"]) if attempts is None else attempts
            db.execute("UPDATE workflow_runs SET status = ?, attempts = ?, error = ? WHERE run_id = ?", (status.value, next_attempts, error, run_id))
            return WorkflowRun(run_id, current["workflow_id"], current["version_id"], current["idempotency_key"], status, next_attempts, error, current["created_at"])
        finally:
            db.close()

    def retry_or_dead_letter(self, run_id: str, error: str, *, max_attempts: int = 3) -> WorkflowRun:
        db = self._session()
        try:
            current = db.execute("SELECT * FROM workflow_runs WHERE run_id = ?", (run_id,)).fetchone()
            if current is None:
                raise KeyError(f"workflow run not found: {run_id}")
            attempts = int(current["attempts"]) + 1
            status = RunStatus.RUNNING if attempts < max_attempts else RunStatus.DEAD_LETTER
            db.execute("UPDATE workflow_runs SET status = ?, attempts = ?, error = ? WHERE run_id = ?", (status.value, attempts, error, run_id))
            return WorkflowRun(run_id, current["workflow_id"], current["version_id"], current["idempotency_key"], status, attempts, error, current["created_at"])
        finally:
            db.close()

    def list_runs(self, workflow_id: str) -> list[WorkflowRun]:
        db = self._session()
        try:
            rows = db.execute("SELECT * FROM workflow_runs WHERE workflow_id = ? ORDER BY created_at DESC", (workflow_id,)).fetchall()
            return [WorkflowRun(row["run_id"], row["workflow_id"], row["version_id"], row["idempotency_key"], RunStatus(row["status"]), row["attempts"], row["error"], row["created_at"]) for row in rows]
        finally:
            db.close()


class AutomationDispatcher:
    """Bridge durable triggers to versioned workflows with idempotency and outcome recording."""

    def __init__(self, schedule_store: Any, workflow_store: WorkflowStore, executor: "WorkflowExecutor") -> None:
        self.schedule_store = schedule_store
        self.workflow_store = workflow_store
        self.executor = executor

    def dispatch_webhook(self, workflow_id: str, event_id: str, payload: dict[str, Any] | None = None, *, approved_steps: frozenset[str] = frozenset()) -> WorkflowRun:
        version = self.workflow_store.enabled_version(workflow_id)
        run = self.workflow_store.start_run(workflow_id, version.version_id, f"event:{event_id}")
        try:
            self.executor.execute(version.steps, payload or {}, approved_steps=approved_steps)
            return self.workflow_store.finish_run(run.run_id, RunStatus.COMPLETED)
        except Exception as exc:
            self.workflow_store.finish_run(run.run_id, RunStatus.FAILED, error=str(exc)[:2_000])
            raise

    def dispatch_schedule(self, schedule_id: str, payload: dict[str, Any] | None = None, *, worker_id: str = "local", approved_steps: frozenset[str] = frozenset()) -> WorkflowRun:
        schedule = self.schedule_store.claim(schedule_id, worker_id=worker_id)
        idempotency_key = f"schedule:{schedule.schedule_id}:{schedule.next_run_at}"
        execution_id = "execution-" + hashlib.sha256(idempotency_key.encode()).hexdigest()[:24]
        execution = self.schedule_store.start_execution(schedule_id, execution_id=execution_id)
        try:
            version = self.workflow_store.enabled_version(schedule.workflow_id)
            run = self.workflow_store.start_run(schedule.workflow_id, version.version_id, idempotency_key)
            if execution.status == "running" and run.status in {RunStatus.RUNNING, RunStatus.FAILED}:
                result = self.executor.execute(version.steps, payload or {}, approved_steps=approved_steps)
                del result
                completed = self.workflow_store.finish_run(run.run_id, RunStatus.COMPLETED)
                self.schedule_store.finish_execution(execution_id, status="completed")
            else:
                completed = run
            if completed.status == RunStatus.COMPLETED:
                self.schedule_store.advance_after_success(schedule_id, worker_id=worker_id)
            self.schedule_store.release(schedule_id, worker_id=worker_id)
            return completed
        except Exception as exc:
            try:
                if "run" in locals() and run.status != RunStatus.COMPLETED:
                    self.workflow_store.finish_run(run.run_id, RunStatus.FAILED, error=str(exc)[:2_000])
                self.schedule_store.finish_execution(execution_id, status="failed", error=str(exc)[:2_000])
            finally:
                self.schedule_store.release(schedule_id, worker_id=worker_id)
            raise


class WorkflowExecutor:
    """Execute declared deterministic or agentic handlers with fail-closed policy checks."""

    def __init__(
        self,
        handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] | None = None,
        *,
        agentic_handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] | None = None,
    ) -> None:
        self.handlers = handlers or {}
        self.agentic_handlers = agentic_handlers or {}

    def execute(self, steps: tuple[WorkflowStep, ...], payload: dict[str, Any], *, approved_steps: frozenset[str] = frozenset(), dry_run: bool = False) -> dict[str, Any]:
        """Execute safe steps and preview external-mutating steps when requested."""
        validate_workflow_steps(steps)
        context = dict(payload)
        previews: list[dict[str, Any]] = []
        for step in steps:
            mode = step_execution_mode(step)
            mutates_external_state = bool(step.config.get("mutates_external_state", False))
            if dry_run and mutates_external_state:
                previews.append({
                    "step_id": step.step_id,
                    "kind": step.kind,
                    "executed": False,
                    "requires_approval": step.requires_approval,
                    "reason": "external side effects are disabled in dry-run mode",
                })
                continue
            if step.requires_approval and step.step_id not in approved_steps:
                raise PermissionError(f"workflow step requires approval: {step.step_id}")
            handlers = self.agentic_handlers if mode is StepExecutionMode.AGENTIC else self.handlers
            handler = handlers.get(step.kind)
            if handler is None:
                raise LookupError(f"{mode.value} workflow step handler unavailable: {step.kind}")
            result = handler({**context, **step.config})
            if not isinstance(result, dict):
                raise TypeError(f"workflow handler must return dict: {step.kind}")
            context.update(result)
        if dry_run:
            context["_dry_run"] = True
            context["dry_run_actions"] = previews
        return context
