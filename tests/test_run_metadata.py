from pathlib import Path

import pytest

from orville_core.observability import RunMetadata, RunMetadataRecorder, hash_prompt


def test_run_metadata_records_requested_fields_without_prompt_content(tmp_path: Path):
    path = tmp_path / "runs.jsonl"
    prompt = "private prompt"
    metadata = RunMetadata(
        run_id="run-1",
        model_provider="local",
        model_version="v1",
        prompt_hash=hash_prompt(prompt),
        tool_calls=({"name": "pytest", "outcome": "ok"},),
        agent_handoffs=({"from": "research", "to": "code"},),
        retries=1,
        approvals=({"action": "execute", "status": "approved"},),
        artifacts=({"path": "dist/app.whl", "sha256": "abc"},),
        latency_ms=12.5,
        token_usage={"input": 10, "output": 4},
        finish_reason="stop",
        cache_hit=False,
        cost_metadata={"currency": "USD", "amount": 0},
        failure=None,
    )
    record = RunMetadataRecorder(path).record_run(metadata)
    assert record.event == "run.metadata"
    raw = path.read_text(encoding="utf-8")
    assert prompt not in raw
    assert metadata.prompt_hash in raw
    assert RunMetadataRecorder(path).read()[0].attributes["run_id"] == "run-1"


def test_run_metadata_rejects_invalid_values():
    with pytest.raises(ValueError):
        RunMetadata(run_id="run", prompt_hash="bad").validate()
    with pytest.raises(ValueError):
        RunMetadata(run_id="run", retries=-1).validate()
