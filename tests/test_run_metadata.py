from __future__ import annotations

import json
from pathlib import Path

import pytest

from orville_core.observability import JsonlTraceRecorder
from orville_core.run_metadata import RunMetadata
from orville_core.security import SecretRedactor


def test_run_metadata_tracks_required_dimensions_without_raw_prompt(tmp_path: Path) -> None:
    prompt = "private user prompt"
    metadata = RunMetadata(
        run_id="run-1",
        task_id="task-1",
        provider="local",
        model="test-model",
        model_version="v1",
        prompt_hash=RunMetadata.hash_prompt(prompt),
        tool_calls=2,
        agent_handoffs=1,
        retries=1,
        approvals=1,
        artifacts=("artifact-1",),
        latency_ms=12.5,
        token_usage={"input": 10, "output": 20},
        finish_reason="stop",
        cache_hit=True,
        cost_metadata={"unit": "test"},
    )
    recorder = JsonlTraceRecorder(tmp_path / "run.jsonl", SecretRedactor())
    metadata.record(recorder)
    raw = (tmp_path / "run.jsonl").read_text(encoding="utf-8")
    payload = json.loads(raw)
    assert metadata.prompt_hash == RunMetadata.hash_prompt(prompt)
    assert prompt not in raw
    assert payload["attributes"]["usage_counts"] == {"input": 10, "output": 20}
    assert payload["attributes"]["tool_calls"] == 2


def test_run_metadata_rejects_negative_counts() -> None:
    with pytest.raises(ValueError, match="retries"):
        RunMetadata("run", "task", retries=-1)


def test_run_metadata_rejects_invalid_token_usage() -> None:
    with pytest.raises(ValueError, match="token_usage"):
        RunMetadata("run", "task", token_usage={"input": -1})
