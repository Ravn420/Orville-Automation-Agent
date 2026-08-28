"""Run-manager boundary for deployed API execution.

The manager owns synchronous and background objective execution while keeping
provider-backed handlers in the orchestration engine. It is intentionally
small so deployments can inject a durable implementation without replacing
model execution with test or placeholder handlers.
"""
from __future__ import annotations

from collections.abc import Callable
from threading import Lock, Thread
from typing import Any

from .engine import ExecutionResult, OrchestrationEngine
from .models import Checkpoint, TaskGraph


CompletionHook = Callable[[str], None]


class RunManager:
    """Execute persisted task graphs through a real orchestration engine."""

    def __init__(
        self,
        engine: OrchestrationEngine,
        checkpoint_store: Any,
        *,
        on_completed: CompletionHook | None = None,
    ) -> None:
        self.engine = engine
        self.checkpoint_store = checkpoint_store
        self.on_completed = on_completed
        self._threads: dict[str, Thread] = {}
        self._lock = Lock()

    def execute(
        self,
        graph: TaskGraph,
        *,
        context: dict[str, Any],
        run_id: str,
        streaming: bool = False,
    ) -> ExecutionResult | None:
        """Run synchronously or schedule one bounded background execution."""
        if not streaming:
            result = self.engine.run(graph, context=context, run_id=run_id)
            if self.on_completed:
                self.on_completed(run_id)
            return result
        with self._lock:
            existing = self._threads.get(run_id)
            if existing and existing.is_alive():
                return None
            thread = Thread(target=self._execute_background, args=(graph, context, run_id), daemon=True)
            self._threads[run_id] = thread
            thread.start()
        return None

    def is_running(self, run_id: str) -> bool:
        with self._lock:
            thread = self._threads.get(run_id)
            return bool(thread and thread.is_alive())

    def request_cancel(self, run_id: str) -> None:
        """Persist cancellation through the same checkpoint store as the engine."""
        checkpoint = self.checkpoint_store.load(run_id)
        checkpoint.context["cancel_requested"] = True
        self.checkpoint_store.save(checkpoint)

    def _execute_background(self, graph: TaskGraph, context: dict[str, Any], run_id: str) -> None:
        try:
            self.engine.run(graph, context=context, run_id=run_id)
            if self.on_completed:
                self.on_completed(run_id)
        finally:
            with self._lock:
                self._threads.pop(run_id, None)


__all__ = ["RunManager"]
