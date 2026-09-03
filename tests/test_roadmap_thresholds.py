from __future__ import annotations

import pytest

from orville_core.roadmap_thresholds import RoadmapReleaseThresholds, evaluate_roadmap_release


GOOD = {
    "task_success_rate": 0.99,
    "test_pass_rate": 1.0,
    "safety_violations": 0,
    "latency_ms": 100.0,
    "cost_units": 10.0,
    "failure_recovery_rate": 0.95,
    "gui_accessibility_score": 1.0,
}


def test_all_release_dimensions_pass_with_good_evidence() -> None:
    decision = evaluate_roadmap_release(GOOD)
    assert decision["passed"] is True
    assert all(decision["checks"].values())


@pytest.mark.parametrize("field", ["task_success_rate", "test_pass_rate", "safety_violations", "latency_ms", "cost_units", "failure_recovery_rate", "gui_accessibility_score"])
def test_each_release_dimension_can_fail_closed(field: str) -> None:
    observed = dict(GOOD)
    observed[field] = 0 if field.endswith("rate") or field.endswith("score") else (1 if field == "safety_violations" else 10_000)
    assert evaluate_roadmap_release(observed)["passed"] is False


def test_threshold_policy_rejects_invalid_bounds() -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        RoadmapReleaseThresholds(min_test_pass_rate=2).validate()
