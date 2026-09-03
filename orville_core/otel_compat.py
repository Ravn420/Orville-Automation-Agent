"""Small OpenTelemetry-compatible span/event envelope for local operation.

The exporter is intentionally JSONL and dependency-free. It preserves stable
trace/span identifiers and semantic attributes while delegating redaction to
the existing recorder.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Mapping

from .observability import JsonlTraceRecorder


EVENT_CATEGORIES = {
    "graph.node",
    "agent",
    "model.call",
    "tool.call",
    "mcp.call",
    "approval",
    "artifact",
}


@dataclass(frozen=True)
class OTelEvent:
    trace_id: str
    span_id: str
    name: str
    category: str
    attributes: Mapping[str, Any]

    def to_attributes(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "category": self.category,
            **dict(self.attributes),
        }


class OTelCompatibleRecorder:
    def __init__(self, recorder: JsonlTraceRecorder) -> None:
        self.recorder = recorder

    def emit(self, trace_id: str, category: str, attributes: Mapping[str, Any] | None = None, *, span_id: str | None = None) -> OTelEvent:
        if not trace_id.strip():
            raise ValueError("trace_id is required")
        if category not in EVENT_CATEGORIES:
            raise ValueError(f"unsupported event category: {category}")
        event = OTelEvent(trace_id, span_id or uuid.uuid4().hex[:16], f"orville.{category}", category, dict(attributes or {}))
        self.recorder.record(trace_id, event.name, event.to_attributes())
        return event
