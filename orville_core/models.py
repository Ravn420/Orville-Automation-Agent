"""Typed state models for Orville's standalone orchestration core."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class TaskStatus(StrEnum):
    PLANNED = "planned"
    READY = "ready"
    RUNNING = "running"
    VERIFIED = "verified"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    WAITING_APPROVAL = "waiting_approval"


class RunStatus(StrEnum):
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"
    WAITING_APPROVAL = "waiting_approval"


@dataclass
class TaskNode:
    """A single executable node in a directed acyclic task graph."""

    task_id: str
    title: str
    handler: str
    depends_on: list[str] = field(default_factory=list)
    inputs: dict[str, Any] = field(default_factory=dict)
    max_attempts: int = 1
    timeout_seconds: float | None = None
    approval_required: bool = False
    approved: bool = False
    idempotency_key: str | None = None
    owned_paths: list[str] = field(default_factory=list)
    required_inputs: list[str] = field(default_factory=list)
    owner: str | None = None
    status: TaskStatus = TaskStatus.PLANNED
    attempts: int = 0
    output: Any = None
    error: str | None = None

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            raise ValueError("task_id must not be empty")
        if not self.title.strip():
            raise ValueError(f"title must not be empty for {self.task_id}")
        if not self.handler.strip():
            raise ValueError(f"handler must not be empty for {self.task_id}")
        if self.max_attempts < 1:
            raise ValueError(f"max_attempts must be >= 1 for {self.task_id}")
        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            raise ValueError(f"timeout_seconds must be positive for {self.task_id}")
        if len(set(self.owned_paths)) != len(self.owned_paths):
            raise ValueError(f"owned_paths must be unique for {self.task_id}")
        if len(set(self.required_inputs)) != len(self.required_inputs):
            raise ValueError(f"required_inputs must be unique for {self.task_id}")
        if any(not name.strip() for name in self.required_inputs):
            raise ValueError(f"required_inputs must contain non-empty names for {self.task_id}")
        if self.owner is not None and not self.owner.strip():
            raise ValueError(f"owner must be non-empty when specified for {self.task_id}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "handler": self.handler,
            "depends_on": list(self.depends_on),
            "inputs": self.inputs,
            "max_attempts": self.max_attempts,
            "timeout_seconds": self.timeout_seconds,
            "approval_required": self.approval_required,
            "approved": self.approved,
            "idempotency_key": self.idempotency_key,
            "owned_paths": list(self.owned_paths),
            "required_inputs": list(self.required_inputs),
            "owner": self.owner,
            "status": self.status.value,
            "attempts": self.attempts,
            "output": self.output,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskNode":
        return cls(
            task_id=data["task_id"],
            title=data["title"],
            handler=data["handler"],
            depends_on=list(data.get("depends_on", [])),
            inputs=dict(data.get("inputs", {})),
            max_attempts=int(data.get("max_attempts", 1)),
            timeout_seconds=data.get("timeout_seconds"),
            approval_required=bool(data.get("approval_required", False)),
            approved=bool(data.get("approved", False)),
            idempotency_key=data.get("idempotency_key"),
            owned_paths=list(data.get("owned_paths", [])),
            required_inputs=list(data.get("required_inputs", [])),
            owner=data.get("owner"),
            status=TaskStatus(data.get("status", TaskStatus.PLANNED.value)),
            attempts=int(data.get("attempts", 0)),
            output=data.get("output"),
            error=data.get("error"),
        )


@dataclass
class TaskGraph:
    """A named collection of task nodes with dependency validation."""

    graph_id: str
    name: str
    tasks: list[TaskNode]

    def __post_init__(self) -> None:
        if not self.graph_id.strip():
            raise ValueError("graph_id must not be empty")
        if not self.name.strip():
            raise ValueError("name must not be empty")
        self.validate()

    def task_map(self) -> dict[str, TaskNode]:
        return {task.task_id: task for task in self.tasks}

    def validate(self) -> None:
        task_map = self.task_map()
        owned: dict[str, str] = {}
        for task in self.tasks:
            for path in task.owned_paths:
                if path in owned:
                    raise ValueError(f"owned path conflict: {path} claimed by {owned[path]} and {task.task_id}")
                owned[path] = task.task_id
        if len(task_map) != len(self.tasks):
            raise ValueError("task IDs must be unique")
        for task in self.tasks:
            if task.owned_paths and not task.owner:
                raise ValueError(f"task {task.task_id} has owned paths but no owner")
            missing_inputs = set(task.required_inputs) - set(task.inputs)
            if missing_inputs:
                raise ValueError(f"{task.task_id} has missing required inputs: {sorted(missing_inputs)}")
            missing = set(task.depends_on) - set(task_map)
            if missing:
                raise ValueError(f"{task.task_id} depends on unknown tasks: {sorted(missing)}")
            if task.task_id in task.depends_on:
                raise ValueError(f"task {task.task_id} cannot depend on itself")

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(task_id: str) -> None:
            if task_id in visiting:
                raise ValueError("task graph contains a dependency cycle")
            if task_id in visited:
                return
            visiting.add(task_id)
            for dependency in task_map[task_id].depends_on:
                visit(dependency)
            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in task_map:
            visit(task_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "name": self.name,
            "tasks": [task.to_dict() for task in self.tasks],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskGraph":
        return cls(
            graph_id=data["graph_id"],
            name=data["name"],
            tasks=[TaskNode.from_dict(task) for task in data["tasks"]],
        )


@dataclass
class Event:
    sequence: int
    event_type: str
    task_id: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "event_type": self.event_type,
            "task_id": self.task_id,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        return cls(
            sequence=int(data["sequence"]),
            event_type=data["event_type"],
            task_id=data.get("task_id"),
            details=dict(data.get("details", {})),
        )


@dataclass(frozen=True)
class OperationCheckpoint:
    """Secret-safe durable before/after evidence for a material operation."""

    checkpoint_id: str
    task_id: str
    operation_kind: str
    phase: str
    status: str
    attempt: int
    sequence: int

    def __post_init__(self) -> None:
        if self.phase not in {"before", "after"}:
            raise ValueError("operation checkpoint phase must be before or after")
        if self.operation_kind not in {"agent", "tool", "model", "approval", "artifact", "task"}:
            raise ValueError(f"unsupported operation kind: {self.operation_kind}")
        if self.attempt < 0 or self.sequence < 1:
            raise ValueError("operation checkpoint counters are invalid")

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkpoint_id": self.checkpoint_id,
            "task_id": self.task_id,
            "operation_kind": self.operation_kind,
            "phase": self.phase,
            "status": self.status,
            "attempt": self.attempt,
            "sequence": self.sequence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OperationCheckpoint":
        return cls(
            checkpoint_id=str(data["checkpoint_id"]),
            task_id=str(data["task_id"]),
            operation_kind=str(data["operation_kind"]),
            phase=str(data["phase"]),
            status=str(data["status"]),
            attempt=int(data.get("attempt", 0)),
            sequence=int(data["sequence"]),
        )


@dataclass
class Checkpoint:
    """Complete persisted state needed to resume one graph execution."""

    run_id: str
    graph: TaskGraph
    context: dict[str, Any] = field(default_factory=dict)
    run_status: RunStatus = RunStatus.RUNNING
    events: list[Event] = field(default_factory=list)
    operation_checkpoints: list[OperationCheckpoint] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 2,
            "run_id": self.run_id,
            "graph": self.graph.to_dict(),
            "context": self.context,
            "run_status": self.run_status.value,
            "events": [event.to_dict() for event in self.events],
            "operation_checkpoints": [item.to_dict() for item in self.operation_checkpoints],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Checkpoint":
        schema_version = int(data.get("schema_version", 1))
        if schema_version not in {1, 2}:
            raise ValueError(f"unsupported checkpoint schema: {data.get('schema_version')}")
        return cls(
            run_id=data["run_id"],
            graph=TaskGraph.from_dict(data["graph"]),
            context=dict(data.get("context", {})),
            run_status=RunStatus(data.get("run_status", RunStatus.RUNNING.value)),
            events=[Event.from_dict(event) for event in data.get("events", [])],
            operation_checkpoints=[
                OperationCheckpoint.from_dict(item)
                for item in data.get("operation_checkpoints", [])
            ],
        )
