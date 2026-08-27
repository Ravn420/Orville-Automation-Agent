"""Durable multi-turn task threads, typed waits, and structured output.

This module is intentionally dependency-light so the Windows executable can use it
in local-only mode. It stores append-only messages and explicit waiting requests in
SQLite, validates a conservative JSON-Schema subset, and never stores secrets in
structured event payloads.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

from .security import SecretRedactor


def _now() -> str:
    return datetime.now(UTC).isoformat()


class ThreadStatus(StrEnum):
    PLANNED = "planned"
    RUNNING = "running"
    WAITING = "waiting"
    STOPPED = "stopped"
    FAILED = "failed"
    CANCEL_REQUESTED = "cancel_requested"
    CANCELLED = "cancelled"
    RECOVERING = "recovering"


@dataclass(frozen=True)
class TaskThread:
    thread_id: str
    project_id: str | None
    agent_id: str
    request: str
    status: ThreadStatus = ThreadStatus.PLANNED
    stop_reason: str | None = None
    version: int = 1
    structured_state: str = "none"
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)


@dataclass(frozen=True)
class ThreadMessage:
    message_id: str
    thread_id: str
    role: str
    kind: str
    content: Any
    sequence: int
    created_at: str = field(default_factory=_now)


@dataclass(frozen=True)
class WaitingRequest:
    event_id: str
    thread_id: str
    event_type: str
    description: str
    input_schema: dict[str, Any]
    risk_class: str = "normal"
    tool_name: str | None = None
    status: str = "pending"
    response: dict[str, Any] | None = None
    expires_at: str | None = None
    created_at: str = field(default_factory=_now)


@dataclass(frozen=True)
class StructuredResult:
    success: bool
    value: Any
    error: str | None = None


_ALLOWED_TRANSITIONS: dict[ThreadStatus, frozenset[ThreadStatus]] = {
    ThreadStatus.PLANNED: frozenset({ThreadStatus.RUNNING, ThreadStatus.CANCELLED}),
    ThreadStatus.RUNNING: frozenset({ThreadStatus.WAITING, ThreadStatus.STOPPED, ThreadStatus.FAILED, ThreadStatus.CANCEL_REQUESTED, ThreadStatus.RECOVERING}),
    ThreadStatus.WAITING: frozenset({ThreadStatus.RUNNING, ThreadStatus.STOPPED, ThreadStatus.FAILED, ThreadStatus.CANCELLED}),
    ThreadStatus.RECOVERING: frozenset({ThreadStatus.RUNNING, ThreadStatus.WAITING, ThreadStatus.FAILED, ThreadStatus.CANCELLED}),
    ThreadStatus.CANCEL_REQUESTED: frozenset({ThreadStatus.CANCELLED, ThreadStatus.STOPPED}),
    ThreadStatus.STOPPED: frozenset(),
    ThreadStatus.FAILED: frozenset({ThreadStatus.RECOVERING, ThreadStatus.CANCELLED}),
    ThreadStatus.CANCELLED: frozenset(),
}


class SchemaError(ValueError):
    """Raised when a structured-output schema is outside the supported subset."""


_SUPPORTED_TYPES = {"object", "array", "string", "number", "integer", "boolean", "null"}
_SUPPORTED_KEYS = {"type", "properties", "required", "additionalProperties", "items", "enum", "description", "anyOf", "$ref", "$defs"}
_FORBIDDEN_KEYS = {"pattern", "format", "minLength", "maxLength", "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf", "minItems", "maxItems", "uniqueItems", "allOf", "oneOf", "not", "if", "then", "else"}


def validate_schema(schema: dict[str, Any], *, max_depth: int = 5) -> None:
    if not isinstance(schema, dict):
        raise SchemaError("schema must be an object")
    if schema.get("type") != "object":
        raise SchemaError("schema root type must be object")

    def visit(node: Any, depth: int, root: bool = False) -> None:
        if not isinstance(node, dict):
            raise SchemaError("each schema node must be an object")
        forbidden = _FORBIDDEN_KEYS.intersection(node)
        if forbidden:
            raise SchemaError(f"unsupported schema keywords: {sorted(forbidden)}")
        unknown = set(node) - _SUPPORTED_KEYS
        if unknown:
            raise SchemaError(f"unsupported schema keywords: {sorted(unknown)}")
        if depth > max_depth:
            raise SchemaError(f"schema nesting exceeds {max_depth} levels")
        node_type = node.get("type")
        if isinstance(node_type, list):
            if not node_type or not set(node_type) <= _SUPPORTED_TYPES:
                raise SchemaError("invalid type union")
        elif node_type is not None and node_type not in _SUPPORTED_TYPES:
            raise SchemaError(f"unsupported type: {node_type}")
        if "anyOf" in node:
            if not isinstance(node["anyOf"], list) or not node["anyOf"]:
                raise SchemaError("anyOf must be a non-empty list")
            for child in node["anyOf"]:
                visit(child, depth + 1)
        if "enum" in node and (not isinstance(node["enum"], list) or not node["enum"]):
            raise SchemaError("enum must be a non-empty list")
        if node_type == "object":
            properties = node.get("properties", {})
            required = node.get("required", [])
            if not isinstance(properties, dict) or not isinstance(required, list):
                raise SchemaError("object properties and required must be collections")
            if node.get("additionalProperties") is not False:
                raise SchemaError("object additionalProperties must be false")
            if set(required) != set(properties):
                raise SchemaError("required must list every object property")
            for child in properties.values():
                visit(child, depth + 1)
        if node_type == "array":
            if "items" not in node:
                raise SchemaError("array schema requires items")
            visit(node["items"], depth + 1)
        for key in ("$defs",):
            if key in node:
                if not isinstance(node[key], dict):
                    raise SchemaError(f"{key} must be an object")
                for child in node[key].values():
                    visit(child, depth + 1)

    visit(schema, 0, True)


def _zero_value(schema: dict[str, Any]) -> Any:
    node_type = schema.get("type")
    if isinstance(node_type, list):
        if "null" in node_type:
            return None
        node_type = node_type[0]
    if "anyOf" in schema:
        for child in schema["anyOf"]:
            if child.get("type") == "null":
                return None
        return _zero_value(schema["anyOf"][0])
    if "enum" in schema:
        return schema["enum"][0]
    return {"object": {key: _zero_value(value) for key, value in schema.get("properties", {}).items()}, "array": [], "string": "", "number": 0, "integer": 0, "boolean": False, "null": None}.get(node_type)


def validate_value(value: Any, schema: dict[str, Any], *, depth: int = 0) -> None:
    if "anyOf" in schema:
        if any(_value_matches(value, child, depth=depth + 1) for child in schema["anyOf"]):
            return
        raise SchemaError("value does not match anyOf")
    node_type = schema.get("type")
    types = set(node_type) if isinstance(node_type, list) else {node_type}
    if value is None and "null" in types:
        return
    if "object" in types and isinstance(value, dict):
        properties = schema.get("properties", {})
        if set(value) != set(properties):
            raise SchemaError("object fields do not match schema")
        for key, child in properties.items():
            validate_value(value[key], child, depth=depth + 1)
        return
    if "array" in types and isinstance(value, list):
        for item in value:
            validate_value(item, schema["items"], depth=depth + 1)
        return
    if "string" in types and isinstance(value, str):
        pass
    elif "boolean" in types and isinstance(value, bool):
        pass
    elif "integer" in types and isinstance(value, int) and not isinstance(value, bool):
        pass
    elif "number" in types and isinstance(value, (int, float)) and not isinstance(value, bool):
        pass
    else:
        raise SchemaError(f"value type does not match {sorted(types)}")
    if "enum" in schema and value not in schema["enum"]:
        raise SchemaError("value is not in enum")


def _value_matches(value: Any, schema: dict[str, Any], *, depth: int) -> bool:
    try:
        validate_value(value, schema, depth=depth)
        return True
    except SchemaError:
        return False


class TaskThreadStore:
    """SQLite-backed task threads with optimistic version checks."""

    def __init__(self, database: str | Path) -> None:
        self.database = Path(database)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout = 30000")
        db.execute("PRAGMA journal_mode = WAL")
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
                CREATE TABLE IF NOT EXISTS task_threads (
                    thread_id TEXT PRIMARY KEY, project_id TEXT, agent_id TEXT NOT NULL, request TEXT NOT NULL,
                    status TEXT NOT NULL, stop_reason TEXT, version INTEGER NOT NULL, structured_state TEXT NOT NULL,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS thread_messages (
                    message_id TEXT PRIMARY KEY, thread_id TEXT NOT NULL REFERENCES task_threads(thread_id),
                    role TEXT NOT NULL, kind TEXT NOT NULL, content TEXT NOT NULL, sequence INTEGER NOT NULL,
                    created_at TEXT NOT NULL, UNIQUE(thread_id, sequence)
                );
                CREATE TABLE IF NOT EXISTS waiting_requests (
                    event_id TEXT PRIMARY KEY, thread_id TEXT NOT NULL REFERENCES task_threads(thread_id),
                    event_type TEXT NOT NULL, description TEXT NOT NULL, input_schema TEXT NOT NULL,
                    risk_class TEXT NOT NULL, tool_name TEXT, status TEXT NOT NULL, response TEXT,
                    expires_at TEXT, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS structured_outputs (
                    thread_id TEXT PRIMARY KEY REFERENCES task_threads(thread_id), schema_json TEXT NOT NULL,
                    state TEXT NOT NULL, result_json TEXT, error TEXT, updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS thread_messages_idx ON thread_messages(thread_id, sequence);
            """)

    @staticmethod
    def _id(prefix: str) -> str:
        return f"{prefix}-{uuid4().hex[:12]}"

    def create_thread(self, request: str, *, project_id: str | None = None, agent_id: str = "default") -> TaskThread:
        if not request.strip():
            raise ValueError("request must not be empty")
        thread = TaskThread(self._id("thread"), project_id, agent_id, request.strip())
        with self._lock, self._session() as db:
            db.execute("INSERT INTO task_threads VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", tuple(asdict(thread).values()))
        self.append_message(thread.thread_id, role="user", kind="request", content=request.strip())
        return self.get_thread(thread.thread_id)

    def get_thread(self, thread_id: str) -> TaskThread:
        with self._session() as db:
            row = db.execute("SELECT * FROM task_threads WHERE thread_id = ?", (thread_id,)).fetchone()
        if row is None:
            raise KeyError(f"thread not found: {thread_id}")
        data = dict(row)
        data["status"] = ThreadStatus(data["status"])
        return TaskThread(**data)

    def list_threads(self, *, project_id: str | None = None, limit: int = 100) -> list[TaskThread]:
        query = "SELECT * FROM task_threads"
        args: list[Any] = []
        if project_id:
            query += " WHERE project_id = ?"
            args.append(project_id)
        query += " ORDER BY updated_at DESC LIMIT ?"
        args.append(max(1, min(limit, 500)))
        with self._session() as db:
            rows = db.execute(query, args).fetchall()
        return [self._row_to_thread(row) for row in rows]

    @staticmethod
    def _row_to_thread(row: sqlite3.Row) -> TaskThread:
        data = dict(row)
        data["status"] = ThreadStatus(data["status"])
        return TaskThread(**data)

    def append_message(self, thread_id: str, *, role: str, kind: str, content: Any) -> ThreadMessage:
        self.get_thread(thread_id)
        if role not in {"user", "assistant", "tool", "system"}:
            raise ValueError("invalid message role")
        safe = SecretRedactor.redact(content)
        with self._lock, self._session() as db:
            sequence = int(db.execute("SELECT COALESCE(MAX(sequence), 0) + 1 FROM thread_messages WHERE thread_id = ?", (thread_id,)).fetchone()[0])
            message = ThreadMessage(self._id("message"), thread_id, role, kind, safe, sequence)
            db.execute("INSERT INTO thread_messages VALUES (?, ?, ?, ?, ?, ?, ?)", (message.message_id, message.thread_id, message.role, message.kind, json.dumps(message.content, ensure_ascii=False), message.sequence, message.created_at))
            db.execute("UPDATE task_threads SET updated_at = ?, version = version + 1 WHERE thread_id = ?", (_now(), thread_id))
        return message

    def list_messages(self, thread_id: str, *, after: int = 0) -> list[ThreadMessage]:
        self.get_thread(thread_id)
        with self._session() as db:
            rows = db.execute("SELECT * FROM thread_messages WHERE thread_id = ? AND sequence > ? ORDER BY sequence", (thread_id, after)).fetchall()
        return [ThreadMessage(row["message_id"], row["thread_id"], row["role"], row["kind"], json.loads(row["content"]), row["sequence"], row["created_at"]) for row in rows]

    def transition(self, thread_id: str, new_status: ThreadStatus, *, stop_reason: str | None = None, expected_version: int | None = None) -> TaskThread:
        current = self.get_thread(thread_id)
        if new_status not in _ALLOWED_TRANSITIONS[current.status]:
            raise ValueError(f"invalid thread transition: {current.status.value} -> {new_status.value}")
        with self._lock, self._session() as db:
            clause = "thread_id = ? AND version = ?" if expected_version is not None else "thread_id = ?"
            args: list[Any] = [new_status.value, stop_reason, _now()]
            args.extend([thread_id, expected_version] if expected_version is not None else [thread_id])
            db.execute(f"UPDATE task_threads SET status = ?, stop_reason = ?, updated_at = ?, version = version + 1 WHERE {clause}", args)
            if db.total_changes != 1:
                raise RuntimeError("thread changed concurrently; reload before retrying")
        return self.get_thread(thread_id)

    def request_wait(self, thread_id: str, *, event_type: str, description: str, input_schema: dict[str, Any], risk_class: str = "normal", tool_name: str | None = None, expires_at: str | None = None) -> WaitingRequest:
        validate_schema(input_schema)
        thread = self.get_thread(thread_id)
        if thread.status not in {ThreadStatus.RUNNING, ThreadStatus.RECOVERING}:
            raise ValueError("thread must be running before requesting input")
        event = WaitingRequest(self._id("event"), thread_id, event_type, description, input_schema, risk_class, tool_name, expires_at=expires_at)
        with self._lock, self._session() as db:
            db.execute("INSERT INTO waiting_requests VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (event.event_id, event.thread_id, event.event_type, event.description, json.dumps(event.input_schema), event.risk_class, event.tool_name, event.status, None, event.expires_at, event.created_at))
        self.transition(thread_id, ThreadStatus.WAITING)
        self.append_message(thread_id, role="system", kind="waiting_request", content={"event_id": event.event_id, "event_type": event.event_type, "description": event.description, "input_schema": event.input_schema, "risk_class": event.risk_class})
        return event

    def resolve_wait(self, event_id: str, response: dict[str, Any], *, accept: bool = True) -> WaitingRequest:
        with self._session() as db:
            row = db.execute("SELECT * FROM waiting_requests WHERE event_id = ?", (event_id,)).fetchone()
        if row is None:
            raise KeyError(f"waiting event not found: {event_id}")
        event = self._row_to_wait(row)
        if event.status != "pending":
            raise ValueError("waiting event has already been resolved")
        if not isinstance(response, dict):
            raise SchemaError("waiting response must be an object")
        validate_value(response, event.input_schema)
        status = "accepted" if accept else "rejected"
        with self._lock, self._session() as db:
            db.execute("UPDATE waiting_requests SET status = ?, response = ? WHERE event_id = ? AND status = 'pending'", (status, json.dumps(SecretRedactor.redact(response)), event_id))
            if db.total_changes != 1:
                raise RuntimeError("waiting event changed concurrently")
        thread = self.get_thread(event.thread_id)
        if accept:
            self.transition(event.thread_id, ThreadStatus.RUNNING)
        else:
            self.transition(event.thread_id, ThreadStatus.CANCELLED, stop_reason="approval_rejected")
        self.append_message(event.thread_id, role="user", kind="waiting_response", content={"event_id": event_id, "accepted": accept, "response": response})
        return WaitingRequest(event.event_id, event.thread_id, event.event_type, event.description, event.input_schema, event.risk_class, event.tool_name, status, response, event.expires_at, event.created_at)

    @staticmethod
    def _row_to_wait(row: sqlite3.Row) -> WaitingRequest:
        return WaitingRequest(row["event_id"], row["thread_id"], row["event_type"], row["description"], json.loads(row["input_schema"]), row["risk_class"], row["tool_name"], row["status"], json.loads(row["response"]) if row["response"] else None, row["expires_at"], row["created_at"])

    def arm_structured_output(self, thread_id: str, schema: dict[str, Any]) -> None:
        validate_schema(schema)
        self.get_thread(thread_id)
        with self._lock, self._session() as db:
            db.execute("INSERT INTO structured_outputs(thread_id, schema_json, state, result_json, error, updated_at) VALUES (?, ?, 'armed', NULL, NULL, ?) ON CONFLICT(thread_id) DO UPDATE SET schema_json = excluded.schema_json, state = 'armed', result_json = NULL, error = NULL, updated_at = excluded.updated_at", (thread_id, json.dumps(schema), _now()))
            db.execute("UPDATE task_threads SET structured_state = 'armed', updated_at = ?, version = version + 1 WHERE thread_id = ?", (_now(), thread_id))

    def complete_structured_output(self, thread_id: str, value: Any) -> StructuredResult:
        self.get_thread(thread_id)
        with self._session() as db:
            row = db.execute("SELECT * FROM structured_outputs WHERE thread_id = ?", (thread_id,)).fetchone()
        if row is None or row["state"] != "armed":
            return StructuredResult(False, None, "no structured-output schema is armed")
        schema = json.loads(row["schema_json"])
        try:
            validate_value(value, schema)
        except SchemaError as exc:
            result = StructuredResult(False, _zero_value(schema), str(exc))
            state = "failed"
        else:
            result = StructuredResult(True, SecretRedactor.redact(value), None)
            state = "consumed"
        with self._lock, self._session() as db:
            db.execute("UPDATE structured_outputs SET state = ?, result_json = ?, error = ?, updated_at = ? WHERE thread_id = ? AND state = 'armed'", (state, json.dumps(result.value), result.error, _now(), thread_id))
            db.execute("UPDATE task_threads SET structured_state = ?, updated_at = ?, version = version + 1 WHERE thread_id = ?", (state, _now(), thread_id))
        self.append_message(thread_id, role="system", kind="structured_output_result", content=asdict(result))
        return result

    def recover_after_restart(self) -> list[TaskThread]:
        with self._lock, self._session() as db:
            rows = db.execute("SELECT * FROM task_threads WHERE status IN ('running', 'cancel_requested')").fetchall()
            for row in rows:
                db.execute("UPDATE task_threads SET status = 'recovering', updated_at = ?, version = version + 1 WHERE thread_id = ? AND status = ?", (_now(), row["thread_id"], row["status"]))
        return [self.get_thread(row["thread_id"]) for row in rows]
