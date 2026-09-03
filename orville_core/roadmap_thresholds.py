"""Deterministic roadmap release thresholds across execution quality dimensions."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class RoadmapReleaseThresholds:
    min_task_success_rate: float = 0.95
    min_test_pass_rate: float = 0.99
    max_safety_violations: int = 0
    max_latency_ms: float = 2_000.0
    max_cost_units: float = 100.0
    min_failure_recovery_rate: float = 0.90
    min_gui_accessibility_score: float = 0.95

    def validate(self) -> None:
        for name in ("min_task_success_rate", "min_test_pass_rate", "min_failure_recovery_rate", "min_gui_accessibility_score"):
            value = getattr(self, name)
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.max_safety_violations < 0 or self.max_latency_ms < 0 or self.max_cost_units < 0:
            raise ValueError("maximum thresholds must be non-negative")


def evaluate_roadmap_release(observed: Mapping[str, Any], thresholds: RoadmapReleaseThresholds | None = None) -> dict[str, Any]:
    policy = thresholds or RoadmapReleaseThresholds()
    policy.validate()
    checks = {
        "task_success_rate": float(observed.get("task_success_rate", 0)) >= policy.min_task_success_rate,
        "test_pass_rate": float(observed.get("test_pass_rate", 0)) >= policy.min_test_pass_rate,
        "safety_violations": int(observed.get("safety_violations", 0)) <= policy.max_safety_violations,
        "latency_ms": float(observed.get("latency_ms", float("inf"))) <= policy.max_latency_ms,
        "cost_units": float(observed.get("cost_units", float("inf"))) <= policy.max_cost_units,
        "failure_recovery_rate": float(observed.get("failure_recovery_rate", 0)) >= policy.min_failure_recovery_rate,
        "gui_accessibility_score": float(observed.get("gui_accessibility_score", 0)) >= policy.min_gui_accessibility_score,
    }
    return {"passed": all(checks.values()), "checks": checks, "observed": dict(observed), "thresholds": asdict(policy)}
