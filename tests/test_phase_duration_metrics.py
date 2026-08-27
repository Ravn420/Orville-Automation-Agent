"""Focused tests for planning, execution, verification, and recovery timings."""

import math

import pytest

from orville_core.telemetry import TelemetryRegistry


def test_phase_durations_are_aggregated_by_lifecycle_phase() -> None:
    registry = TelemetryRegistry()
    registry.record_phase_duration("Planning", 1.0)
    registry.record_phase_duration("execution", 2.0)
    registry.record_phase_duration("verification", 3.0)
    registry.record_phase_duration("recovery", 4.0)
    registry.record_phase_duration("execution", 4.0)

    phases = registry.snapshot()["phases"]
    assert set(phases) == {"planning", "execution", "verification", "recovery"}
    assert phases["planning"]["count"] == 1
    assert phases["execution"]["count"] == 2
    assert phases["execution"]["duration_mean"] == pytest.approx(3.0)
    assert phases["verification"]["duration_mean"] == pytest.approx(3.0)
    assert phases["recovery"]["duration_mean"] == pytest.approx(4.0)


def test_phase_duration_rejects_unknown_or_invalid_values() -> None:
    registry = TelemetryRegistry()
    with pytest.raises(ValueError, match="phase"):
        registry.record_phase_duration("deployment", 1.0)
    with pytest.raises(ValueError, match="finite"):
        registry.record_phase_duration("planning", math.inf)
    with pytest.raises(ValueError, match="non-negative"):
        registry.record_phase_duration("planning", -0.1)


def test_phase_metrics_export_with_existing_metrics() -> None:
    registry = TelemetryRegistry()
    registry.record("task.execute", duration_seconds=0.25, success=True)
    registry.record_phase_duration("execution", 0.25)
    snapshot = registry.snapshot()
    assert snapshot["metrics"]["task.execute"]["success_rate"] == 1.0
    assert snapshot["phases"]["execution"]["duration_mean"] == pytest.approx(0.25)
