from __future__ import annotations

import json
from pathlib import Path

from orville_core.trace_compare import compare_trace_runs


def _write(path: Path, events: list[tuple[str, dict]]) -> None:
    path.write_text("".join(json.dumps({"event": name, "attributes": attrs, "timestamp": "different"}) + "\n" for name, attrs in events), encoding="utf-8")


def test_identical_trace_content_passes_despite_timestamp_changes(tmp_path: Path) -> None:
    left, right = tmp_path / "left.jsonl", tmp_path / "right.jsonl"
    _write(left, [("start", {"status": "ok"}), ("finish", {"status": "ok"})])
    _write(right, [("start", {"status": "ok"}), ("finish", {"status": "ok"})])
    assert compare_trace_runs(left, right).passed is True


def test_trace_comparison_reports_missing_unexpected_and_changed_events(tmp_path: Path) -> None:
    left, right = tmp_path / "left.jsonl", tmp_path / "right.jsonl"
    _write(left, [("start", {"status": "ok"}), ("tool", {"action": "read"})])
    _write(right, [("start", {"status": "changed"}), ("extra", {"action": "write"})])
    result = compare_trace_runs(left, right)
    assert result.passed is False
    assert result.missing_events == ("tool",)
    assert result.unexpected_events == ("extra",)
    assert result.changed_events == ("start",)
