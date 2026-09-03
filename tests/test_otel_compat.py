from __future__ import annotations

import json
from pathlib import Path

import pytest

from orville_core.observability import JsonlTraceRecorder
from orville_core.otel_compat import OTelCompatibleRecorder
from orville_core.security import SecretRedactor


@pytest.mark.parametrize("category", ["graph.node", "agent", "model.call", "tool.call", "mcp.call", "approval", "artifact"])
def test_otel_event_categories_are_recorded_and_redacted(tmp_path: Path, category: str) -> None:
    path = tmp_path / "trace.jsonl"
    exporter = OTelCompatibleRecorder(JsonlTraceRecorder(path, SecretRedactor()))
    event = exporter.emit("trace-1", category, {"api_key": "synthetic-secret", "status": "ok"}, span_id="span-1")
    assert event.name == f"orville.{category}"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["attributes"]["span_id"] == "span-1"
    assert payload["attributes"]["category"] == category
    assert payload["attributes"]["api_key"] != "synthetic-secret"


def test_otel_rejects_unknown_categories(tmp_path: Path) -> None:
    exporter = OTelCompatibleRecorder(JsonlTraceRecorder(tmp_path / "trace.jsonl"))
    with pytest.raises(ValueError, match="unsupported event category"):
        exporter.emit("trace-1", "unknown")
