"""Focused tests for privacy-safe per-run observability."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from orville_core import RunObservabilityRecord, RunObservabilityRecorder, elapsed_ms


def test_run_record_tracks_required_fields_without_raw_prompt() -> None:
    prompt = "Use token=secret_123456789 to fix the issue"
    record = RunObservabilityRecord.start(
        "run-123",
        task_id="task-1",
        agent_id="agent-code",
        provider="local",
        model="fixture-model",
        model_version="v1",
        prompt=prompt,
    )
    record.record_tool_call("pytest", outcome="success", latency_ms=12.5, approved=True)
    record.record_handoff("planner", "coder", reason="implementation")
    record.record_retry(attempt=1, reason="transient", backoff_ms=25)
    record.record_approval(approval_id="approval-1", action="write", scope="fixture", outcome="approved", reviewer="reviewer-1")
    record.record_artifact(artifact_id="artifact-1", media_type="text/plain", checksum="sha256:abc", size_bytes=12)
    record.record_cache(hit=True, key_hash="sha256:key", source="local")
    record.record_failure(error_class="none", message="no failure", retryable=False)
    record.finish(
        finish_reason="completed",
        latency_ms=42.0,
        token_usage={"input": 11, "output": 7},
        cost_metadata={"currency": "USD", "amount": 0.0, "api_key": "secret_123456789"},
    )

    payload = record.to_dict()
    assert payload["prompt_capture"] == "hash-only"
    assert payload["prompt_hash"] == RunObservabilityRecord.hash_prompt(prompt)
    assert prompt not in json.dumps(payload)
    assert payload["tool_calls"][0]["approved"] is True
    assert payload["agent_handoffs"][0]["from_agent"] == "planner"
    assert payload["retries"][0]["attempt"] == 1
    assert payload["approvals"][0]["approval_id"] == "approval-1"
    assert payload["artifacts"][0]["artifact_id"] == "artifact-1"
    assert payload["token_usage"]["total"] == 18
    assert payload["finish_reason"] == "completed"
    assert payload["cache"]["hit"] is True
    assert payload["cost_metadata"]["api_key"] == "[REDACTED]"
    assert payload["failure"]["message"] == "no failure"


def test_jsonl_recorder_persists_redacted_record(tmp_path: Path) -> None:
    recorder = RunObservabilityRecorder(tmp_path / "runs.jsonl")
    record = RunObservabilityRecord.start("run-1", prompt="Bearer tok_123456789")
    record.finish(finish_reason="failed", token_usage={"total": 1})
    written = recorder.write(record)
    loaded = recorder.read()

    assert written["prompt_hash"]
    assert "tok_123456789" not in json.dumps(written)
    assert loaded == [written]


def test_invalid_values_fail_closed_and_elapsed_is_bounded() -> None:
    with pytest.raises(ValueError):
        RunObservabilityRecord("")
    with pytest.raises(ValueError):
        RunObservabilityRecord("run-1", token_usage={"input": -1})
    with pytest.raises(ValueError):
        RunObservabilityRecord.start("run-1").record_retry(attempt=0, reason="bad")
    with pytest.raises(ValueError):
        RunObservabilityRecord.start("run-1").finish(finish_reason="", latency_ms=-1)
    with pytest.raises(ValueError):
        elapsed_ms(2.0, 1.0)
