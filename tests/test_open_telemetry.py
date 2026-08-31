from pathlib import Path

import pytest

from orville_core.telemetry import OpenTelemetryRecorder, SUPPORTED_OPERATION_KINDS


def test_open_telemetry_records_all_operation_boundaries_and_exports(tmp_path: Path):
    recorder = OpenTelemetryRecorder()
    for kind in sorted(SUPPORTED_OPERATION_KINDS):
        event = recorder.record_operation(
            f"{kind}.run",
            kind,
            attributes={"token": "sk-secret", "prompt": "do not retain", "count": 1},
            duration_seconds=0.25,
            retry_count=1,
        )
        assert event.operation_kind == kind
        assert "prompt" not in event.attributes
    payload = recorder.export_otlp()
    assert len(payload["events"]) == len(SUPPORTED_OPERATION_KINDS)
    assert payload["metrics"]["graph_node.run"]["retry_count"] == 1


def test_open_telemetry_rejects_unknown_kind_and_negative_duration():
    recorder = OpenTelemetryRecorder()
    with pytest.raises(ValueError):
        recorder.record_operation("bad", "unknown")
    with pytest.raises(ValueError):
        recorder.record_operation("bad", "model", duration_seconds=-1)
