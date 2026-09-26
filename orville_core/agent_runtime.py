"""Persistent local agent profiles and bounded child-task orchestration."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .security import SecretRedactor
from .task_threads import TaskThread, TaskThreadStore, ThreadStatus


def _now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class AgentProfile:
    agent_id: str
    name: str
    description: str = ""
    system_instructions: str = ""
    model_policy: dict[str, Any] = field(default_factory=dict)
    memory_scope: str = "thread"
    skills: tuple[str, ...] = ()
    connectors: tuple[str, ...] = ()
    tool_permissions: tuple[str, ...] = ()
    risk_ceiling: str = "normal"
    enabled: bool = True
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)


@dataclass(frozen=True)
class ChildTask:
    relation_id: str
    parent_thread_id: str
    child_thread_id: str
    depth: int
    required: bool = True
    created_at: str = field(default_factory=_now)


@dataclass(frozen=True)
class AgentExecutionResult:
    """Safe, durable outcome of one local agent-handler invocation."""

    thread_id: str
    status: ThreadStatus
    output: Any = None
    error: str | None = None
    replayed: bool = False


class AgentRuntimeStore:
    """SQLite-backed agent profiles and child-thread lineage."""

    def __init__(self, database: str | Path, thread_store: TaskThreadStore | None = None, *, max_depth: int = 3, max_children: int = 25) -> None:
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self.thread_store = thread_store or TaskThreadStore(self.database)
        self.max_depth = max_depth
        self.max_children = max_children
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout = 30000")
        return db

    @contextmanager
    def _session(self):
        db = self._connect()
        try:
            yield db
        finally:
            db.close()

    def _initialize(self) -> None:
        with self._session() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS agent_profiles (
                    agent_id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL,
                    system_instructions TEXT NOT NULL, model_policy TEXT NOT NULL, memory_scope TEXT NOT NULL,
                    skills TEXT NOT NULL, connectors TEXT NOT NULL, tool_permissions TEXT NOT NULL,
                    risk_ceiling TEXT NOT NULL, enabled INTEGER NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS child_tasks (
                    relation_id TEXT PRIMARY KEY, parent_thread_id TEXT NOT NULL, child_thread_id TEXT NOT NULL UNIQUE,
                    depth INTEGER NOT NULL, required INTEGER NOT NULL, created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS child_tasks_parent_idx ON child_tasks(parent_thread_id, created_at);
            """)

    @staticmethod
    def _id(prefix: str) -> str:
        return f"{prefix}-{uuid4().hex[:12]}"

    def register_agent(self, profile: AgentProfile) -> AgentProfile:
        if not profile.agent_id.strip() or not profile.name.strip():
            raise ValueError("agent id and name must not be empty")
        if profile.risk_ceiling not in {"low", "normal", "high", "critical"}:
            raise ValueError("invalid risk ceiling")
        with self._session() as db:
            db.execute("INSERT INTO agent_profiles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(agent_id) DO UPDATE SET name=excluded.name, description=excluded.description, system_instructions=excluded.system_instructions, model_policy=excluded.model_policy, memory_scope=excluded.memory_scope, skills=excluded.skills, connectors=excluded.connectors, tool_permissions=excluded.tool_permissions, risk_ceiling=excluded.risk_ceiling, enabled=excluded.enabled, updated_at=excluded.updated_at", (profile.agent_id, profile.name.strip(), profile.description, profile.system_instructions, json.dumps(profile.model_policy), profile.memory_scope, json.dumps(list(profile.skills)), json.dumps(list(profile.connectors)), json.dumps(list(profile.tool_permissions)), profile.risk_ceiling, int(profile.enabled), profile.created_at, _now()))
        return self.get_agent(profile.agent_id)

    def get_agent(self, agent_id: str) -> AgentProfile:
        with self._session() as db:
            row = db.execute("SELECT * FROM agent_profiles WHERE agent_id = ?", (agent_id,)).fetchone()
        if row is None:
            raise KeyError(f"agent not found: {agent_id}")
        return self._row_to_agent(row)

    def list_agents(self, *, enabled_only: bool = False) -> list[AgentProfile]:
        query = "SELECT * FROM agent_profiles" + (" WHERE enabled = 1" if enabled_only else "") + " ORDER BY name"
        with self._session() as db:
            return [self._row_to_agent(row) for row in db.execute(query).fetchall()]

    @staticmethod
    def _row_to_agent(row: sqlite3.Row) -> AgentProfile:
        return AgentProfile(row["agent_id"], row["name"], row["description"], row["system_instructions"], json.loads(row["model_policy"]), row["memory_scope"], tuple(json.loads(row["skills"])), tuple(json.loads(row["connectors"])), tuple(json.loads(row["tool_permissions"])), row["risk_ceiling"], bool(row["enabled"]), row["created_at"], row["updated_at"])

    def set_enabled(self, agent_id: str, enabled: bool) -> AgentProfile:
        self.get_agent(agent_id)
        with self._session() as db:
            db.execute("UPDATE agent_profiles SET enabled = ?, updated_at = ? WHERE agent_id = ?", (int(enabled), _now(), agent_id))
        return self.get_agent(agent_id)

    def execute_thread(
        self,
        thread_id: str,
        handler: Callable[[str, dict[str, Any]], Any],
        *,
        retry_failed: bool = False,
        max_output_bytes: int = 65_536,
    ) -> AgentExecutionResult:
        """Run one local handler with durable lifecycle, replay, and redaction boundaries.

        The handler receives only the thread request and a safe execution context. A
        completed thread is replayed from its persisted result instead of invoking
        the handler again. Failed threads require an explicit retry flag.
        """
        if not callable(handler):
            raise TypeError("handler must be callable")
        if max_output_bytes < 1:
            raise ValueError("max_output_bytes must be positive")
        thread = self.thread_store.get_thread(thread_id)
        if thread.status == ThreadStatus.STOPPED:
            for message in reversed(self.thread_store.list_messages(thread_id)):
                if message.kind == "agent_result":
                    return AgentExecutionResult(thread_id, ThreadStatus.STOPPED, message.content.get("output"), replayed=True)
            return AgentExecutionResult(thread_id, ThreadStatus.STOPPED, replayed=True)
        profile = self.get_agent(thread.agent_id) if thread.agent_id != "default" else None
        if profile is not None and not profile.enabled:
            raise PermissionError(f"agent is disabled: {thread.agent_id}")
        if thread.status == ThreadStatus.FAILED:
            if not retry_failed:
                return AgentExecutionResult(thread_id, ThreadStatus.FAILED, error=thread.stop_reason or "thread failed")
            self.thread_store.transition(thread_id, ThreadStatus.RECOVERING, stop_reason="explicit_retry")
            thread = self.thread_store.get_thread(thread_id)
        if thread.status in {ThreadStatus.PLANNED, ThreadStatus.RECOVERING}:
            self.thread_store.transition(thread_id, ThreadStatus.RUNNING)
            thread = self.thread_store.get_thread(thread_id)
        if thread.status != ThreadStatus.RUNNING:
            raise ValueError(f"thread is not executable: {thread.status.value}")

        context = {
            "thread_id": thread.thread_id,
            "project_id": thread.project_id,
            "agent_id": thread.agent_id,
            "skills": list(profile.skills) if profile else [],
            "connectors": list(profile.connectors) if profile else [],
            "tool_permissions": list(profile.tool_permissions) if profile else [],
        }
        self.thread_store.append_message(thread_id, role="system", kind="agent_execution_started", content={"agent_id": thread.agent_id})
        try:
            output = SecretRedactor.redact(handler(thread.request, context))
            encoded = json.dumps(output, ensure_ascii=False)
            if len(encoded.encode("utf-8")) > max_output_bytes:
                raise ValueError("agent output exceeds configured size limit")
        except Exception as exc:
            error = SecretRedactor.redact_exception(exc)
            self.thread_store.append_message(thread_id, role="system", kind="agent_error", content={"error": error})
            self.thread_store.transition(thread_id, ThreadStatus.FAILED, stop_reason=error)
            return AgentExecutionResult(thread_id, ThreadStatus.FAILED, error=error)

        self.thread_store.append_message(thread_id, role="assistant", kind="agent_result", content={"output": output})
        current = self.thread_store.get_thread(thread_id)
        if current.status == ThreadStatus.CANCEL_REQUESTED:
            self.thread_store.transition(thread_id, ThreadStatus.CANCELLED, stop_reason="cancelled_during_execution")
            return AgentExecutionResult(thread_id, ThreadStatus.CANCELLED, output=output, error="cancelled_during_execution")
        self.thread_store.transition(thread_id, ThreadStatus.STOPPED, stop_reason="completed")
        return AgentExecutionResult(thread_id, ThreadStatus.STOPPED, output=output)

    def create_child_task(self, parent_thread_id: str, request: str, *, agent_id: str = "default", required: bool = True, project_id: str | None = None) -> tuple[TaskThread, ChildTask]:
        parent = self.thread_store.get_thread(parent_thread_id)
        with self._session() as db:
            count = int(db.execute("SELECT COUNT(*) FROM child_tasks WHERE parent_thread_id = ?", (parent_thread_id,)).fetchone()[0])
            if count >= self.max_children:
                raise ValueError("parent thread child-task limit exceeded")
            row = db.execute("SELECT MAX(depth) FROM child_tasks WHERE child_thread_id = ? OR parent_thread_id = ?", (parent_thread_id, parent_thread_id)).fetchone()
            depth = int(row[0] or 0) + 1
        if depth > self.max_depth:
            raise ValueError("child-task depth limit exceeded")
        profile = self.get_agent(agent_id) if agent_id != "default" else None
        if profile is not None and not profile.enabled:
            raise PermissionError(f"agent is disabled: {agent_id}")
        child = self.thread_store.create_thread(request, project_id=project_id or parent.project_id, agent_id=agent_id)
        relation = ChildTask(self._id("child"), parent_thread_id, child.thread_id, depth, required)
        with self._session() as db:
            db.execute("INSERT INTO child_tasks VALUES (?, ?, ?, ?, ?, ?)", (relation.relation_id, relation.parent_thread_id, relation.child_thread_id, relation.depth, int(relation.required), relation.created_at))
        self.thread_store.append_message(parent_thread_id, role="system", kind="child_task_created", content={"child_thread_id": child.thread_id, "agent_id": agent_id, "required": required})
        return child, relation

    def list_children(self, parent_thread_id: str) -> list[tuple[ChildTask, TaskThread]]:
        self.thread_store.get_thread(parent_thread_id)
        with self._session() as db:
            rows = db.execute("SELECT * FROM child_tasks WHERE parent_thread_id = ? ORDER BY created_at", (parent_thread_id,)).fetchall()
        return [(ChildTask(row["relation_id"], row["parent_thread_id"], row["child_thread_id"], row["depth"], bool(row["required"]), row["created_at"]), self.thread_store.get_thread(row["child_thread_id"])) for row in rows]

    def cancel_tree(self, parent_thread_id: str) -> list[str]:
        cancelled: list[str] = []
        for relation, child in self.list_children(parent_thread_id):
            if child.status not in {ThreadStatus.CANCELLED, ThreadStatus.STOPPED}:
                try:
                    self.thread_store.transition(child.thread_id, ThreadStatus.CANCEL_REQUESTED, stop_reason="parent_cancelled")
                    self.thread_store.transition(child.thread_id, ThreadStatus.CANCELLED, stop_reason="parent_cancelled")
                except ValueError:
                    pass
                cancelled.append(child.thread_id)
            cancelled.extend(self.cancel_tree(child.thread_id))
        return cancelled
