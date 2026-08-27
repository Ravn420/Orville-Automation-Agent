"""Focused tests for task execution metrics."""

import pytest

from orville_core.telemetry import TelemetryRegistry


def test_snapshot_reports_duration_success_retries_failures_and_verification() -> None:
    registry = TelemetryRegistry()
    registry.record("task.execute", success=True, duration_seconds=1.5, retry_count=2, verification_outcome="passed")
    registry.record("task.execute", success=False, duration_seconds=0.5, retry_count=1, failure_class="provider_timeout", verification_outcome="failed")
    registry.record("task.execute", success=True, duration_seconds=2.0, verification_outcome="passed")

    metric = registry.snapshot()["metrics"]["task.execute"]
    assert metric["count"] == 3
    assert metric["failures"] == 1
    assert metric["success_rate"] == pytest.approx(2 / 3)
    assert metric["failure_rate"] == pytest.approx(1 / 3)
    assert metric["duration_mean"] == pytest.approx(4 / 3)
    assert metric["retry_count"] == 3
    assert metric["failure_classes"] == {"provider_timeout": 1}
    assert metric["verification_outcomes"] == {"passed": 2, "failed": 1}


def test_failure_classes_are_recorded_only_for_failures_and_values_are_bounded() -> None:
    registry = TelemetryRegistry()
    registry.record("task", success=True, failure_class="not-a-failure")
    registry.record("task", success=False, failure_class="x" * 200, verification_outcome="y" * 200)
    metric = registry.snapshot()["metrics"]["task"]
    assert "not-a-failure" not in metric["failure_classes"]
    assert list(metric["failure_classes"])[0] == "x" * 128
    assert list(metric["verification_outcomes"])[0] == "y" * 64


def test_negative_retry_counts_are_rejected() -> None:
    registry = TelemetryRegistry()
    with pytest.raises(ValueError, match="retry_count"):
        registry.record("task", retry_count=-1)
