"""Structured, correlation-safe logging for multi-agent executions."""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
import json
from pathlib import Path
import sys
from typing import Any, Iterator, TextIO
from uuid import uuid4

from .boundary import sanitize_external_output


_correlation_id: ContextVar[str | None] = ContextVar("orville_correlation_id", default=None)


class StructuredLogger:
    """Emit one bounded JSON object per event with stable execution correlation fields."""

    def __init__(self, stream: TextIO | None = None, *, max_message: int = 1_000) -> None:
        if max_message < 100:
            raise ValueError("max_message must be at least 100")
        self.stream = stream or sys.stderr
        self.max_message = max_message

    @contextmanager
    def execution(self, execution_id: str, *, task_id: str | None = None, agent_id: str | None = None) -> Iterator[str]:
        """Bind one correlation ID for all nested multi-agent execution events."""
        correlation_id = f"corr-{uuid4().hex}"
        token = _correlation_id.set(correlation_id)
        try:
            self.event("execution.started", execution_id=execution_id, task_id=task_id, agent_id=agent_id)
            yield correlation_id
        finally:
            _correlation_id.reset(token)

    def event(self, event: str, *, execution_id: str, task_id: str | None = None, agent_id: str | None = None, level: str = "info", **fields: Any) -> dict[str, Any]:
        """Write a secret-safe structured event and return the emitted record."""
        correlation_id = _correlation_id.get() or f"corr-{uuid4().hex}"
        record: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": level,
            "event": event,
            "correlation_id": correlation_id,
            "execution_id": execution_id,
        }
        if task_id is not None:
            record["task_id"] = task_id
        if agent_id is not None:
            record["agent_id"] = agent_id
        safe_fields = sanitize_external_output(fields, max_items=30, max_text=self.max_message)
        if isinstance(safe_fields, dict):
            record.update(safe_fields)
        self.stream.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        self.stream.flush()
        return record


def write_jsonl_event(path: str | Path, record: dict[str, Any]) -> Path:
    """Append an already-sanitized event to a caller-owned JSONL log path."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return destination
