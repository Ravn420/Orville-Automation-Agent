from __future__ import annotations

import json
from pathlib import Path

import pytest

from orville_core.observability import JsonlTraceRecorder
from orville_core.sensitive_capture import CapturePolicy, SensitiveCapture


def test_capture_is_opt_in_by_default(tmp_path: Path) -> None:
    recorder = JsonlTraceRecorder(tmp_path / "trace.jsonl")
    capture = SensitiveCapture(CapturePolicy(), recorder)
    assert capture.record("trace", "prompt", "private", role="reviewer") is False
    assert not (tmp_path / "trace.jsonl").exists()


def test_capture_requires_role_and_redacts_payload(tmp_path: Path) -> None:
    recorder = JsonlTraceRecorder(tmp_path / "trace.jsonl")
    capture = SensitiveCapture(CapturePolicy(True, frozenset({"reviewer"}), 60), recorder)
    with pytest.raises(PermissionError):
        capture.record("trace", "tool_result", {"api_key": "secret-value"}, role="viewer")
    assert capture.record("trace", "tool_result", {"api_key": "secret-value"}, role="reviewer") is True
    raw = (tmp_path / "trace.jsonl").read_text(encoding="utf-8")
    assert "secret-value" not in raw
    payload = json.loads(raw)
    assert payload["attributes"]["kind"] == "tool_result"
    assert payload["attributes"]["expires_at"]


def test_capture_truncates_large_payload_to_digest(tmp_path: Path) -> None:
    recorder = JsonlTraceRecorder(tmp_path / "trace.jsonl")
    capture = SensitiveCapture(CapturePolicy(True, frozenset({"reviewer"}), 60, 20), recorder)
    capture.record("trace", "completion", "x" * 100, role="reviewer")
    payload = json.loads((tmp_path / "trace.jsonl").read_text(encoding="utf-8"))
    assert payload["attributes"]["payload"]["truncated"] is True
    assert len(payload["attributes"]["payload"]["sha256"]) == 64
