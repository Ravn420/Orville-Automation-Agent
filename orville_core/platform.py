"""Durable project/task/plan control-plane contracts for Orville Milestone 1.

This module deliberately stays independent of the existing execution checkpoint
store. It provides a small SQLite-backed control plane that can be adopted by
the current API without changing run/checkpoint semantics.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

from .security import SecretRedactor


def _now() -> str:
    return datetime.now(UTC).isoformat()


class TaskLifecycle(StrEnum):
    NEW = "new"
    ANALYZING = "analyzing"
    PLAN_READY = "plan_ready"
    AWAITING_PLAN_APPROVAL = "awaiting_plan_approval"
    WORKSPACE_READY = "workspace_ready"
    EXECUTING = "executing"
    VALIDATING = "validating"
    REPAIRING = "repairing"
    PREVIEW_READY = "preview_ready"
    AWAITING_FEEDBACK = "awaiting_feedback"
    READY_TO_PUBLISH = "ready_to_publish"
    AWAITING_RELEASE_APPROVAL = "awaiting_release_approval"
    DEPLOYING = "deploying"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


_ALLOWED_TRANSITIONS: dict[TaskLifecycle, frozenset[TaskLifecycle]] = {
    TaskLifecycle.NEW: frozenset({TaskLifecycle.ANALYZING, TaskLifecycle.CANCELLED}),
    TaskLifecycle.ANALYZING: frozenset({TaskLifecycle.PLAN_READY, TaskLifecycle.CANCELLED}),
    TaskLifecycle.PLAN_READY: frozenset({TaskLifecycle.AWAITING_PLAN_APPROVAL, TaskLifecycle.CANCELLED}),
    TaskLifecycle.AWAITING_PLAN_APPROVAL: frozenset({TaskLifecycle.WORKSPACE_READY, TaskLifecycle.CANCELLED}),
    TaskLifecycle.WORKSPACE_READY: frozenset({TaskLifecycle.EXECUTING, TaskLifecycle.CANCELLED}),
    TaskLifecycle.EXECUTING: frozenset({TaskLifecycle.VALIDATING, TaskLifecycle.REPAIRING, TaskLifecycle.CANCELLED}),
    TaskLifecycle.VALIDATING: frozenset({TaskLifecycle.PREVIEW_READY, TaskLifecycle.REPAIRING, TaskLifecycle.COMPLETED, TaskLifecycle.CANCELLED}),
    TaskLifecycle.REPAIRING: frozenset({TaskLifecycle.EXECUTING, TaskLifecycle.VALIDATING, TaskLifecycle.CANCELLED}),
    TaskLifecycle.PREVIEW_READY: frozenset({TaskLifecycle.AWAITING_FEEDBACK, TaskLifecycle.READY_TO_PUBLISH, TaskLifecycle.EXECUTING, TaskLifecycle.CANCELLED}),
    TaskLifecycle.AWAITING_FEEDBACK: frozenset({TaskLifecycle.EXECUTING, TaskLifecycle.READY_TO_PUBLISH, TaskLifecycle.CANCELLED}),
    TaskLifecycle.READY_TO_PUBLISH: frozenset({TaskLifecycle.AWAITING_RELEASE_APPROVAL, TaskLifecycle.COMPLETED, TaskLifecycle.CANCELLED}),
    TaskLifecycle.AWAITING_RELEASE_APPROVAL: frozenset({TaskLifecycle.DEPLOYING, TaskLifecycle.CANCELLED}),
    TaskLifecycle.DEPLOYING: frozenset({TaskLifecycle.COMPLETED, TaskLifecycle.CANCELLED}),
    TaskLifecycle.COMPLETED: frozenset(),
    TaskLifecycle.CANCELLED: frozenset(),
}


@dataclass(frozen=True)
class Project:
    project_id: str
    name: str
    description: str = ""
    owner_id: str = "local"
    environment: str = "development"
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)


@dataclass(frozen=True)
class ProjectInstruction:
    instruction_id: str
    project_id: str
    content: str
    version: int = 1
    active: bool = True
    created_at: str = field(default_factory=_now)


@dataclass(frozen=True)
class ProjectMemory:
    memory_id: str
    project_id: str
    key: str
    value: str
    source: str = "user"
    created_at: str = field(default_factory=_now)


@dataclass(frozen=True)
class AgentTask:
    task_id: str
    project_id: str
    request: str
    base_revision: str | None = None
    mode: str = "general"
    provider_id: str | None = None
    budget: dict[str, Any] = field(default_factory=dict)
    tool_permissions: tuple[str, ...] = ()
    status: TaskLifecycle = TaskLifecycle.NEW
    current_milestone: str | None = None
    resulting_revision: str | None = None
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)


@dataclass(frozen=True)
class Plan:
    plan_id: str
    task_id: str
    objective: str
    assumptions: tuple[str, ...] = ()
    affected_files: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    acceptance_criteria: tuple[str, ...] = ()
    required_approvals: tuple[str, ...] = ()
    status: str = "awaiting_approval"
    created_at: str = field(default_factory=_now)


@dataclass(frozen=True)
class PlanMilestone:
    milestone_id: str
    plan_id: str
    sequence: int
    title: str
    agent_mode: str = "general"
    depends_on: tuple[str, ...] = ()
    status: str = "planned"


@dataclass(frozen=True)
class Approval:
    approval_id: str
    project_id: str
    subject_type: str
    subject_id: str
    risk_class: str
    actor_id: str
    decision: str
    reason: str = ""
    created_at: str = field(default_factory=_now)


class PlatformStore:
    """SQLite control-plane store with append-only task events."""

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
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def _session(self):
        db = self._connect()
        try:
            yield db
        finally:
            db.close()

    def _initialize(self) -> None:
        with self._session() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL,
                    owner_id TEXT NOT NULL, environment TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS instructions (
                    instruction_id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(project_id),
                    content TEXT NOT NULL, version INTEGER NOT NULL, active INTEGER NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS memory (
                    memory_id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(project_id),
                    key TEXT NOT NULL, value TEXT NOT NULL, source TEXT NOT NULL, created_at TEXT NOT NULL,
                    UNIQUE(project_id, key)
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(project_id), request TEXT NOT NULL,
                    base_revision TEXT, mode TEXT NOT NULL, provider_id TEXT, budget TEXT NOT NULL,
                    tool_permissions TEXT NOT NULL, status TEXT NOT NULL, current_milestone TEXT,
                    resulting_revision TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS plans (
                    plan_id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(task_id), objective TEXT NOT NULL,
                    assumptions TEXT NOT NULL, affected_files TEXT NOT NULL, risks TEXT NOT NULL,
                    acceptance_criteria TEXT NOT NULL, required_approvals TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS milestones (
                    milestone_id TEXT PRIMARY KEY, plan_id TEXT NOT NULL REFERENCES plans(plan_id), sequence INTEGER NOT NULL,
                    title TEXT NOT NULL, agent_mode TEXT NOT NULL, depends_on TEXT NOT NULL, status TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS approvals (
                    approval_id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(project_id),
                    subject_type TEXT NOT NULL, subject_id TEXT NOT NULL, risk_class TEXT NOT NULL,
                    actor_id TEXT NOT NULL, decision TEXT NOT NULL, reason TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS task_events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL REFERENCES tasks(task_id),
                    event_type TEXT NOT NULL, actor_id TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS task_events_task_idx ON task_events(task_id, sequence);
                """
            )

    @staticmethod
    def _id(prefix: str) -> str:
        return f"{prefix}-{uuid4().hex[:12]}"

    def create_project(self, name: str, description: str = "", *, owner_id: str = "local", environment: str = "development") -> Project:
        if not name.strip():
            raise ValueError("project name must not be empty")
        project = Project(self._id("project"), name.strip(), description, owner_id, environment)
        with self._lock, self._session() as db:
            db.execute("INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?, ?)", tuple(asdict(project).values()))
        return project

    def get_project(self, project_id: str) -> Project:
        with self._session() as db:
            row = db.execute("SELECT * FROM projects WHERE project_id = ?", (project_id,)).fetchone()
        if row is None:
            raise KeyError(f"project not found: {project_id}")
        return Project(**dict(row))

    def list_projects(self, *, owner_id: str | None = None) -> list[Project]:
        query = "SELECT * FROM projects"
        params: tuple[Any, ...] = ()
        if owner_id:
            query += " WHERE owner_id = ?"
            params = (owner_id,)
        query += " ORDER BY updated_at DESC"
        with self._session() as db:
            rows = db.execute(query, params).fetchall()
        return [Project(**dict(row)) for row in rows]

    def list_tasks(self, *, project_id: str | None = None, limit: int = 100) -> list[AgentTask]:
        query = "SELECT * FROM tasks"
        params: tuple[Any, ...] = ()
        if project_id:
            query += " WHERE project_id = ?"
            params = (project_id,)
        query += " ORDER BY updated_at DESC LIMIT ?"
        with self._session() as db:
            rows = db.execute(query, (*params, max(1, min(limit, 500)))).fetchall()
        result: list[AgentTask] = []
        for row in rows:
            data = dict(row)
            data["budget"] = json.loads(data["budget"])
            data["tool_permissions"] = tuple(json.loads(data["tool_permissions"]))
            data["status"] = TaskLifecycle(data["status"])
            result.append(AgentTask(**data))
        return result

    def save_instruction(self, project_id: str, content: str) -> ProjectInstruction:
        self.get_project(project_id)
        if not content.strip():
            raise ValueError("instruction content must not be empty")
        with self._lock, self._session() as db:
            version = int(db.execute("SELECT COALESCE(MAX(version), 0) + 1 FROM instructions WHERE project_id = ?", (project_id,)).fetchone()[0])
            db.execute("UPDATE instructions SET active = 0 WHERE project_id = ?", (project_id,))
            instruction = ProjectInstruction(self._id("instruction"), project_id, content.strip(), version)
            db.execute("INSERT INTO instructions VALUES (?, ?, ?, ?, ?, ?)", tuple(asdict(instruction).values()))
        return instruction

    def list_instructions(self, project_id: str, *, active_only: bool = False) -> list[ProjectInstruction]:
        self.get_project(project_id)
        query = "SELECT * FROM instructions WHERE project_id = ?"
        params: tuple[Any, ...] = (project_id,)
        if active_only:
            query += " AND active = 1"
        query += " ORDER BY version DESC"
        with self._session() as db:
            return [ProjectInstruction(**dict(row)) for row in db.execute(query, params).fetchall()]

    def save_memory(self, project_id: str, key: str, value: str, *, source: str = "user") -> ProjectMemory:
        self.get_project(project_id)
        if not key.strip() or not value.strip():
            raise ValueError("memory key and value must not be empty")
        memory = ProjectMemory(self._id("memory"), project_id, key.strip(), value.strip(), source.strip() or "user")
        with self._lock, self._session() as db:
            db.execute("INSERT INTO memory(memory_id, project_id, key, value, source, created_at) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(project_id, key) DO UPDATE SET value = excluded.value, source = excluded.source, created_at = excluded.created_at", tuple(asdict(memory).values()))
            row = db.execute("SELECT * FROM memory WHERE project_id = ? AND key = ?", (project_id, key.strip())).fetchone()
        return ProjectMemory(**dict(row))

    def list_memory(self, project_id: str) -> list[ProjectMemory]:
        self.get_project(project_id)
        with self._session() as db:
            rows = db.execute("SELECT * FROM memory WHERE project_id = ? ORDER BY created_at DESC", (project_id,)).fetchall()
        return [ProjectMemory(**dict(row)) for row in rows]

    def delete_memory(self, project_id: str, key: str) -> None:
        self.get_project(project_id)
        with self._lock, self._session() as db:
            db.execute("DELETE FROM memory WHERE project_id = ? AND key = ?", (project_id, key))

    def create_task(self, project_id: str, request: str, *, base_revision: str | None = None, mode: str = "general", provider_id: str | None = None, budget: dict[str, Any] | None = None, tool_permissions: tuple[str, ...] = ()) -> AgentTask:
        self.get_project(project_id)
        if not request.strip():
            raise ValueError("task request must not be empty")
        task = AgentTask(self._id("task"), project_id, request.strip(), base_revision, mode, provider_id, budget or {}, tool_permissions)
        with self._lock, self._session() as db:
            db.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (task.task_id, task.project_id, task.request, task.base_revision, task.mode, task.provider_id, json.dumps(task.budget), json.dumps(list(task.tool_permissions)), task.status.value, task.current_milestone, task.resulting_revision, task.created_at, task.updated_at))
        self.append_event(task.task_id, "task.created", "system", {"request": task.request, "mode": task.mode})
        return task

    def get_task(self, task_id: str) -> AgentTask:
        with self._session() as db:
            row = db.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
        if row is None:
            raise KeyError(f"task not found: {task_id}")
        data = dict(row)
        data["budget"] = json.loads(data["budget"])
        data["tool_permissions"] = tuple(json.loads(data["tool_permissions"]))
        data["status"] = TaskLifecycle(data["status"])
        return AgentTask(**data)

    def transition_task(self, task_id: str, new_status: TaskLifecycle, *, actor_id: str = "system", milestone: str | None = None, details: dict[str, Any] | None = None) -> AgentTask:
        task = self.get_task(task_id)
        if new_status not in _ALLOWED_TRANSITIONS[task.status]:
            raise ValueError(f"invalid task transition: {task.status.value} -> {new_status.value}")
        updated = _now()
        with self._lock, self._session() as db:
            db.execute("UPDATE tasks SET status = ?, current_milestone = ?, updated_at = ? WHERE task_id = ? AND status = ?", (new_status.value, milestone, updated, task_id, task.status.value))
            if db.total_changes != 1:
                raise RuntimeError("task changed concurrently; reload before retrying")
        self.append_event(task_id, "task.status_changed", actor_id, {"from": task.status.value, "to": new_status.value, **(details or {})})
        return self.get_task(task_id)

    def create_plan(self, task_id: str, objective: str, *, assumptions: tuple[str, ...] = (), affected_files: tuple[str, ...] = (), risks: tuple[str, ...] = (), acceptance_criteria: tuple[str, ...] = (), required_approvals: tuple[str, ...] = (), milestones: list[PlanMilestone] | None = None) -> Plan:
        task = self.get_task(task_id)
        plan = Plan(self._id("plan"), task_id, objective, assumptions, affected_files, risks, acceptance_criteria, required_approvals)
        with self._lock, self._session() as db:
            db.execute("INSERT INTO plans VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (plan.plan_id, plan.task_id, plan.objective, json.dumps(list(plan.assumptions)), json.dumps(list(plan.affected_files)), json.dumps(list(plan.risks)), json.dumps(list(plan.acceptance_criteria)), json.dumps(list(plan.required_approvals)), plan.status, plan.created_at))
            for milestone in milestones or []:
                if milestone.plan_id not in {"", "placeholder", plan.plan_id}:
                    raise ValueError("milestone references a different plan")
                milestone = replace(milestone, plan_id=plan.plan_id)
                db.execute("INSERT INTO milestones VALUES (?, ?, ?, ?, ?, ?, ?)", (milestone.milestone_id, milestone.plan_id, milestone.sequence, milestone.title, milestone.agent_mode, json.dumps(list(milestone.depends_on)), milestone.status))
        if task.status == TaskLifecycle.NEW:
            self.transition_task(task_id, TaskLifecycle.ANALYZING)
            self.transition_task(task_id, TaskLifecycle.PLAN_READY)
            self.transition_task(task_id, TaskLifecycle.AWAITING_PLAN_APPROVAL)
        self.append_event(task_id, "plan.created", "system", {"plan_id": plan.plan_id, "affected_files": list(plan.affected_files)})
        return plan

    def decide_plan(self, plan_id: str, *, approved: bool, actor_id: str, reason: str = "") -> Approval:
        with self._session() as db:
            row = db.execute("SELECT * FROM plans WHERE plan_id = ?", (plan_id,)).fetchone()
        if row is None:
            raise KeyError(f"plan not found: {plan_id}")
        task = self.get_task(row["task_id"])
        decision = "approved" if approved else "rejected"
        approval = Approval(self._id("approval"), task.project_id, "plan", plan_id, "plan", actor_id, decision, reason)
        with self._lock, self._session() as db:
            db.execute("UPDATE plans SET status = ? WHERE plan_id = ? AND status = 'awaiting_approval'", (decision, plan_id))
            if db.total_changes != 1:
                raise ValueError("plan has already received a decision")
            db.execute("INSERT INTO approvals VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", tuple(asdict(approval).values()))
        self.append_event(task.task_id, "plan.decision", actor_id, {"plan_id": plan_id, "decision": decision, "reason": reason})
        if approved:
            self.transition_task(task.task_id, TaskLifecycle.WORKSPACE_READY, actor_id=actor_id)
        else:
            self.transition_task(task.task_id, TaskLifecycle.CANCELLED, actor_id=actor_id, details={"reason": "plan rejected"})
        return approval

    def append_event(self, task_id: str, event_type: str, actor_id: str, payload: dict[str, Any] | None = None) -> int:
        safe_payload = SecretRedactor.redact(payload or {})
        with self._lock, self._session() as db:
            cursor = db.execute("INSERT INTO task_events(task_id, event_type, actor_id, payload, created_at) VALUES (?, ?, ?, ?, ?)", (task_id, event_type, actor_id, json.dumps(safe_payload, ensure_ascii=False), _now()))
            return int(cursor.lastrowid)

    def list_events(self, task_id: str, *, after: int = 0) -> list[dict[str, Any]]:
        with self._session() as db:
            rows = db.execute("SELECT sequence, task_id, event_type, actor_id, payload, created_at FROM task_events WHERE task_id = ? AND sequence > ? ORDER BY sequence", (task_id, after)).fetchall()
        return [{**dict(row), "payload": json.loads(row["payload"])} for row in rows]
