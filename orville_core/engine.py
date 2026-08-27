"""Core synchronous task-graph executor with durable checkpoints."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import hashlib
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from .checkpoint import CheckpointStore
from .models import Checkpoint, Event, OperationCheckpoint, RunStatus, TaskGraph, TaskNode, TaskStatus
from .workspace_locks import WorkspaceLeaseError, WorkspaceLeaseRegistry

TaskHandler = Callable[[TaskNode, dict[str, Any]], Any]
VerificationHandler = Callable[[TaskNode, Any, dict[str, Any]], Any]
EventListener = Callable[[Event], None]


@dataclass
class ExecutionResult:
    run_id: str
    status: RunStatus
    checkpoint_path: str
    outputs: dict[str, Any]
    events: list[Event]


class OrchestrationEngine:
    """Execute a validated DAG and persist state after every material transition."""

    def __init__(
        self,
        checkpoint_store: CheckpointStore,
        handlers: dict[str, TaskHandler] | None = None,
        listeners: Iterable[EventListener] = (),
        verifiers: dict[str, VerificationHandler] | None = None,
        max_workers: int = 3,
    ) -> None:
        """Create an executor with bounded parallelism.

        The Orville project runtime uses three workers so independent tasks in
        the active milestone can proceed together while dependency ordering,
        approvals, verification, and blockers remain authoritative.
        """
        if max_workers < 1:
            raise ValueError("max_workers must be >= 1")
        self.checkpoint_store = checkpoint_store
        self.handlers = handlers or {}
        self.verifiers = verifiers or {}
        self.max_workers = max_workers
        self.listeners = list(listeners)
        self.workspace_leases = WorkspaceLeaseRegistry()

    def register_handler(self, name: str, handler: TaskHandler) -> None:
        if not name.strip():
            raise ValueError("handler name must not be empty")
        self.handlers[name] = handler

    def run(
        self,
        graph: TaskGraph,
        *,
        context: dict[str, Any] | None = None,
        run_id: str | None = None,
        resume: bool = False,
    ) -> ExecutionResult:
        graph.validate()
        if resume:
            if not run_id:
                raise ValueError("run_id is required when resume=True")
            checkpoint = self.checkpoint_store.load(run_id)
            if checkpoint.graph.graph_id != graph.graph_id:
                raise ValueError("resume graph_id does not match checkpoint")
        else:
            run_id = run_id or uuid4().hex
            checkpoint = Checkpoint(run_id=run_id, graph=graph, context=context or {})
            self._record(checkpoint, "run_created", details={"graph_id": graph.graph_id})
            self._save(checkpoint)

        if checkpoint.run_status in {RunStatus.COMPLETED, RunStatus.CANCELLED}:
            return self._result(checkpoint)

        checkpoint.run_status = RunStatus.RUNNING
        self._record(checkpoint, "run_resumed" if resume else "run_started")
        self._save(checkpoint)

        while True:
            if checkpoint.context.get("pause_requested"):
                checkpoint.run_status = RunStatus.PAUSED
                self._record(checkpoint, "run_paused")
                self._save(checkpoint)
                break
            if checkpoint.context.get("cancel_requested"):
                for task in checkpoint.graph.tasks:
                    if task.status not in {TaskStatus.VERIFIED, TaskStatus.CANCELLED, TaskStatus.SKIPPED}:
                        task.status = TaskStatus.CANCELLED
                        self._record(checkpoint, "task_cancelled", task.task_id, {"reason": "run cancellation requested"})
                checkpoint.run_status = RunStatus.CANCELLED
                self._record(checkpoint, "run_cancelled")
                self._save(checkpoint)
                break
            progressed = False
            waiting_for_approval = False
            if self.max_workers > 1:
                parallel_tasks = [
                    task for task in checkpoint.graph.tasks
                    if task.status not in {TaskStatus.VERIFIED, TaskStatus.CANCELLED, TaskStatus.SKIPPED, TaskStatus.WAITING_APPROVAL}
                    and not (task.status == TaskStatus.FAILED and task.attempts >= task.max_attempts)
                    and self._dependencies_satisfied(task, checkpoint.graph)
                    and self._condition_matches(task, checkpoint.context)
                    and not task.approval_required
                ]
                if len(parallel_tasks) > 1:
                    self._execute_parallel_batch(checkpoint, parallel_tasks)
                    continue
            for task in checkpoint.graph.tasks:
                if task.status in {TaskStatus.VERIFIED, TaskStatus.CANCELLED, TaskStatus.SKIPPED}:
                    continue
                if task.approval_required and not task.approved and task.task_id not in checkpoint.context.get("approved_tasks", []):
                    if task.status != TaskStatus.WAITING_APPROVAL:
                        task.status = TaskStatus.WAITING_APPROVAL
                        self._record(checkpoint, "approval_required", task.task_id)
                        self._record_operation(checkpoint, task, "before", "waiting_approval")
                        self._save(checkpoint)
                    waiting_for_approval = True
                    continue
                if not self._condition_matches(task, checkpoint.context):
                    task.status = TaskStatus.SKIPPED
                    task.output = {"skipped": True, "reason": "condition not met"}
                    checkpoint.context.setdefault("outputs", {})[task.task_id] = task.output
                    self._record(checkpoint, "task_skipped", task.task_id)
                    self._save(checkpoint)
                    progressed = True
                    continue
                if task.status == TaskStatus.FAILED and task.attempts >= task.max_attempts:
                    continue
                if not self._dependencies_satisfied(task, checkpoint.graph):
                    if self._dependency_failed(task, checkpoint.graph):
                        if task.status != TaskStatus.BLOCKED:
                            task.status = TaskStatus.BLOCKED
                            task.error = "dependency failed"
                            self._record(checkpoint, "task_blocked", task.task_id, {"reason": task.error})
                            self._save(checkpoint)
                            progressed = True
                    continue
                progressed = True
                self._execute_task(checkpoint, task)

            if all(task.status in {TaskStatus.VERIFIED, TaskStatus.CANCELLED, TaskStatus.SKIPPED} for task in checkpoint.graph.tasks):
                checkpoint.run_status = RunStatus.COMPLETED
                self._record(checkpoint, "run_completed")
                self._save(checkpoint)
                break
            if waiting_for_approval:
                checkpoint.run_status = RunStatus.WAITING_APPROVAL
                self._record(checkpoint, "run_waiting_approval")
                self._save(checkpoint)
                break
            if any(task.status == TaskStatus.BLOCKED for task in checkpoint.graph.tasks):
                checkpoint.run_status = RunStatus.BLOCKED
                self._record(checkpoint, "run_blocked")
                self._save(checkpoint)
                break
            if any(task.status == TaskStatus.FAILED and task.attempts >= task.max_attempts for task in checkpoint.graph.tasks):
                checkpoint.run_status = RunStatus.FAILED
                self._record(checkpoint, "run_failed")
                self._save(checkpoint)
                break
            if not progressed:
                checkpoint.run_status = RunStatus.FAILED
                self._record(checkpoint, "run_failed", details={"reason": "no executable tasks remain"})
                self._save(checkpoint)
                break

        return self._result(checkpoint)

    def _execute_task(self, checkpoint: Checkpoint, task: TaskNode) -> None:
        handler = self.handlers.get(task.handler)
        if handler is None:
            task.status = TaskStatus.FAILED
            task.error = f"handler not registered: {task.handler}"
            task.attempts += 1
            self._record(checkpoint, "task_failed", task.task_id, {"error": task.error})
            self._save(checkpoint)
            return

        if task.idempotency_key:
            cached = checkpoint.context.setdefault("idempotency", {}).get(task.idempotency_key)
            if cached is not None:
                task.output = cached
                task.status = TaskStatus.VERIFIED
                checkpoint.context.setdefault("outputs", {})[task.task_id] = cached
                self._record(checkpoint, "task_idempotency_reused", task.task_id, {"key": task.idempotency_key})
                self._save(checkpoint)
                return
        task.status = TaskStatus.READY
        self._record(checkpoint, "task_ready", task.task_id)
        self._save(checkpoint)
        task.status = TaskStatus.RUNNING
        task.attempts += 1
        task.error = None
        self._record(checkpoint, "task_started", task.task_id, {"attempt": task.attempts})
        self._record_operation(checkpoint, task, "before", "running")
        self._save(checkpoint)
        progress_callback = lambda event_type, details=None: self._emit_progress(checkpoint, task, event_type, details or {})
        checkpoint.context["_progress_callback"] = progress_callback
        try:
            if task.timeout_seconds is None:
                task.output = handler(task, checkpoint.context)
            else:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(handler, task, checkpoint.context)
                    try:
                        task.output = future.result(timeout=task.timeout_seconds)
                    except FutureTimeoutError as exc:
                        future.cancel()
                        raise TimeoutError(f"task exceeded {task.timeout_seconds}s timeout") from exc
            checkpoint.context.setdefault("outputs", {})[task.task_id] = task.output
            if task.idempotency_key:
                checkpoint.context.setdefault("idempotency", {})[task.idempotency_key] = task.output
            self._record_operation(checkpoint, task, "after", "succeeded")
        except Exception as exc:  # noqa: BLE001 - task failures are persisted, not swallowed
            task.status = TaskStatus.FAILED
            task.error = f"{type(exc).__name__}: {exc}"
            self._record(checkpoint, "task_failed", task.task_id, {"attempt": task.attempts, "error": task.error})
            self._record_operation(checkpoint, task, "after", "failed")
            checkpoint.context.pop("_progress_callback", None)
            self._save(checkpoint)
            return
        finally:
            checkpoint.context.pop("_progress_callback", None)
        verifier = self.verifiers.get(task.task_id) or self.verifiers.get(task.handler)
        if verifier is not None:
            try:
                verification = verifier(task, task.output, checkpoint.context)
                if hasattr(verification, "passed"):
                    passed = bool(verification.passed)
                elif isinstance(verification, bool):
                    passed = verification
                elif isinstance(verification, dict):
                    passed = bool(verification.get("passed", False))
                else:
                    passed = False
                checkpoint.context.setdefault("verifications", {})[task.task_id] = verification.to_dict() if hasattr(verification, "to_dict") else verification
                if not passed:
                    task.status = TaskStatus.FAILED
                    task.error = "independent verification failed"
                    self._record(checkpoint, "task_verification_failed", task.task_id, {"attempt": task.attempts})
                    self._save(checkpoint)
                    return
                self._record(checkpoint, "task_verified_independently", task.task_id, {"attempt": task.attempts})
            except Exception as exc:  # noqa: BLE001 - verifier failures are persisted
                task.status = TaskStatus.FAILED
                task.error = f"verification error: {type(exc).__name__}: {exc}"
                self._record(checkpoint, "task_verification_failed", task.task_id, {"attempt": task.attempts, "error": task.error})
                self._save(checkpoint)
                return
        task.status = TaskStatus.VERIFIED
        self._record(checkpoint, "task_verified", task.task_id, {"attempt": task.attempts, "independent": verifier is not None})
        self._save(checkpoint)

    def _execute_parallel_batch(self, checkpoint: Checkpoint, tasks: list[TaskNode]) -> None:
        """Run independent ready tasks against isolated context snapshots, then merge results serially."""
        for task in tasks:
            task.status = TaskStatus.RUNNING
            task.attempts += 1
            task.error = None
            self._record(checkpoint, "task_started", task.task_id, {"attempt": task.attempts, "parallel": True})
            self._record_operation(checkpoint, task, "before", "running")
        self._save(checkpoint)

        def invoke(task: TaskNode) -> tuple[TaskNode, Any, Exception | None]:
            handler = self.handlers.get(task.handler)
            if handler is None:
                return task, None, LookupError(f"handler not registered: {task.handler}")
            lease = None
            try:
                lease = self.workspace_leases.acquire(task.task_id, task.owned_paths)
                local_context = deepcopy(checkpoint.context)
                if task.timeout_seconds is None:
                    return task, handler(task, local_context), None
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(handler, task, local_context)
                    try:
                        return task, future.result(timeout=task.timeout_seconds), None
                    except FutureTimeoutError as exc:
                        future.cancel()
                        return task, None, TimeoutError(f"task exceeded {task.timeout_seconds}s timeout")
            except Exception as exc:  # noqa: BLE001 - persisted as task failure
                return task, None, exc
            finally:
                if lease is not None:
                    self.workspace_leases.release(lease.lease_id)

        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(tasks))) as executor:
            futures = [executor.submit(invoke, task) for task in tasks]
            results = [future.result() for future in futures]

        for task, output, error in results:
            if error is not None:
                task.status = TaskStatus.FAILED
                task.error = f"{type(error).__name__}: {error}"
                self._record(checkpoint, "task_failed", task.task_id, {"attempt": task.attempts, "parallel": True, "error": task.error})
                self._record_operation(checkpoint, task, "after", "failed")
                continue
            task.output = output
            checkpoint.context.setdefault("outputs", {})[task.task_id] = output
            if task.idempotency_key:
                checkpoint.context.setdefault("idempotency", {})[task.idempotency_key] = output
            self._record_operation(checkpoint, task, "after", "succeeded")
            verifier = self.verifiers.get(task.task_id) or self.verifiers.get(task.handler)
            if verifier is not None:
                verification = verifier(task, output, checkpoint.context)
                passed = verification.passed if hasattr(verification, "passed") else bool(verification if isinstance(verification, bool) else verification.get("passed", False))
                checkpoint.context.setdefault("verifications", {})[task.task_id] = verification.to_dict() if hasattr(verification, "to_dict") else verification
                if not passed:
                    task.status = TaskStatus.FAILED
                    task.error = "independent verification failed"
                    self._record(checkpoint, "task_verification_failed", task.task_id, {"attempt": task.attempts, "parallel": True})
                    continue
            task.status = TaskStatus.VERIFIED
            self._record(checkpoint, "task_verified", task.task_id, {"attempt": task.attempts, "parallel": True, "independent": verifier is not None})
        self._save(checkpoint)

    @staticmethod
    def _operation_kind(task: TaskNode) -> str:
        """Return a bounded operation category for durable checkpoint evidence."""
        return str(task.inputs.get("operation_kind", "task"))

    def _record_operation(self, checkpoint: Checkpoint, task: TaskNode, phase: str, status: str) -> None:
        """Append secret-free operation evidence; the caller persists the checkpoint."""
        operation_kind = self._operation_kind(task)
        if operation_kind not in {"agent", "tool", "model", "approval", "artifact", "task"}:
            raise ValueError(f"unsupported operation kind: {operation_kind}")
        sequence = len(checkpoint.operation_checkpoints) + 1
        checkpoint_id = "opcp-" + hashlib.sha256(
            f"{checkpoint.run_id}:{task.task_id}:{phase}:{sequence}".encode("utf-8")
        ).hexdigest()[:20]
        checkpoint.operation_checkpoints.append(
            OperationCheckpoint(
                checkpoint_id=checkpoint_id,
                task_id=task.task_id,
                operation_kind=operation_kind,
                phase=phase,
                status=status,
                attempt=task.attempts,
                sequence=sequence,
            )
        )
        self._record(
            checkpoint,
            f"operation_checkpoint_{phase}",
            task.task_id,
            {"operation_kind": operation_kind, "status": status, "sequence": sequence},
        )

    @staticmethod
    def _condition_matches(task: TaskNode, context: dict[str, Any]) -> bool:
        condition = task.inputs.get("when")
        if not condition:
            return True
        if not isinstance(condition, dict) or "key" not in condition:
            raise ValueError(f"task {task.task_id} has invalid condition; expected {{'key': ..., 'equals': ...}}")
        current: Any = context
        for part in str(condition["key"]).split("."):
            if not isinstance(current, dict) or part not in current:
                current = None
                break
            current = current[part]
        return current == condition.get("equals", True)

    def approve(self, run_id: str, task_id: str) -> None:
        checkpoint = self.checkpoint_store.load(run_id)
        task = checkpoint.graph.task_map().get(task_id)
        if task is None:
            raise KeyError(f"unknown task: {task_id}")
        task.approved = True
        checkpoint.context.setdefault("approved_tasks", []).append(task_id)
        self._record_operation(checkpoint, task, "after", "approved")
        if task.status == TaskStatus.WAITING_APPROVAL:
            task.status = TaskStatus.PLANNED
        self._record(checkpoint, "task_approved", task_id)
        self._save(checkpoint)

    def pause(self, run_id: str) -> None:
        """Request a durable pause at the next safe scheduler boundary."""
        checkpoint = self.checkpoint_store.load(run_id)
        checkpoint.context["pause_requested"] = True
        self._record(checkpoint, "run_pause_requested")
        self._save(checkpoint)

    def resume(self, run_id: str) -> None:
        """Clear a durable pause request; execution resumes via ``run(..., resume=True)``."""
        checkpoint = self.checkpoint_store.load(run_id)
        checkpoint.context.pop("pause_requested", None)
        checkpoint.context.pop("cancel_requested", None)
        checkpoint.run_status = RunStatus.RUNNING
        self._record(checkpoint, "run_resume_requested")
        self._save(checkpoint)

    def cancel(self, run_id: str) -> None:
        checkpoint = self.checkpoint_store.load(run_id)
        checkpoint.context["cancel_requested"] = True
        checkpoint.context.pop("pause_requested", None)
        self._record(checkpoint, "run_cancellation_requested")
        self._save(checkpoint)

    def retry(self, run_id: str, task_id: str | None = None) -> None:
        """Reset selected failed tasks for an explicit, auditable retry."""
        checkpoint = self.checkpoint_store.load(run_id)
        selected = [
            task for task in checkpoint.graph.tasks
            if task_id is None or task.task_id == task_id
        ]
        if not selected:
            raise KeyError(f"unknown task: {task_id}")
        retryable = [task for task in selected if task.status is TaskStatus.FAILED]
        if not retryable:
            raise ValueError("no failed task is eligible for retry")
        for task in retryable:
            task.status = TaskStatus.PLANNED
            task.attempts = 0
            task.error = None
            task.output = None
            if task.idempotency_key:
                checkpoint.context.setdefault("idempotency", {}).pop(task.idempotency_key, None)
            self._record(checkpoint, "task_retry_requested", task.task_id)
        checkpoint.run_status = RunStatus.RUNNING
        checkpoint.context.pop("pause_requested", None)
        checkpoint.context.pop("cancel_requested", None)
        self._save(checkpoint)

    def replay(self, run_id: str, through_sequence: int | None = None) -> list[Event]:
        """Return an immutable event-prefix replay without mutating run state."""
        checkpoint = self.checkpoint_store.load(run_id)
        if through_sequence is not None and through_sequence < 0:
            raise ValueError("through_sequence must be non-negative")
        events = checkpoint.events
        if through_sequence is not None:
            events = [event for event in events if event.sequence <= through_sequence]
        return list(events)

    def inspect_state(self, run_id: str) -> dict[str, Any]:
        """Return a bounded, secret-safe run projection for controlled inspection."""
        checkpoint = self.checkpoint_store.load(run_id)
        return {
            "run_id": checkpoint.run_id,
            "graph_id": checkpoint.graph.graph_id,
            "run_status": checkpoint.run_status.value,
            "task_count": len(checkpoint.graph.tasks),
            "tasks": [
                {
                    "task_id": task.task_id,
                    "status": task.status.value,
                    "attempts": task.attempts,
                    "has_output": task.output is not None,
                    "has_error": task.error is not None,
                }
                for task in checkpoint.graph.tasks
            ],
            "event_count": len(checkpoint.events),
            "operation_checkpoint_count": len(checkpoint.operation_checkpoints),
            "latest_event_sequence": checkpoint.events[-1].sequence if checkpoint.events else 0,
        }

    @staticmethod
    def _dependencies_satisfied(task: TaskNode, graph: TaskGraph) -> bool:
        task_map = graph.task_map()
        return all(task_map[dependency].status == TaskStatus.VERIFIED for dependency in task.depends_on)

    @staticmethod
    def _dependency_failed(task: TaskNode, graph: TaskGraph) -> bool:
        task_map = graph.task_map()
        return any(task_map[dependency].status in {TaskStatus.FAILED, TaskStatus.BLOCKED, TaskStatus.CANCELLED} for dependency in task.depends_on)

    def _record(
        self,
        checkpoint: Checkpoint,
        event_type: str,
        task_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        event = Event(
            sequence=len(checkpoint.events) + 1,
            event_type=event_type,
            task_id=task_id,
            details={"timestamp": datetime.now(UTC).isoformat(), **(details or {})},
        )
        checkpoint.events.append(event)
        for listener in self.listeners:
            listener(event)

    def _emit_progress(self, checkpoint: Checkpoint, task: TaskNode, event_type: str, details: dict[str, Any]) -> None:
        self._record(checkpoint, event_type, task.task_id, details)
        self._save(checkpoint)

    def _save(self, checkpoint: Checkpoint) -> None:
        transient = checkpoint.context.pop("_progress_callback", None)
        try:
            self.checkpoint_store.save(checkpoint)
        finally:
            if transient is not None:
                checkpoint.context["_progress_callback"] = transient

    @staticmethod
    def _result(checkpoint: Checkpoint) -> ExecutionResult:
        return ExecutionResult(
            run_id=checkpoint.run_id,
            status=checkpoint.run_status,
            checkpoint_path=str(checkpoint.run_id),
            outputs={task.task_id: task.output for task in checkpoint.graph.tasks if task.output is not None},
            events=list(checkpoint.events),
        )
