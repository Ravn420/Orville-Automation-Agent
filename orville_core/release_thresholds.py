"""Deterministic release thresholds for local and production-like evidence.

The evaluator consumes the normalized ``HealthSummary`` contract and returns
serializable, redacted decision evidence. It does not contact providers or
change deployment state.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Mapping


@dataclass(frozen=True)
class ReleaseThresholds:
    """Bounded release acceptance limits."""

    min_samples: int = 1
    max_error_rate: float = 0.05
    max_latency_p95_ms: float = 2_000.0
    max_saturation_ratio: float = 0.90
    max_security_findings: int = 0
    min_business_health: float = 0.80
    min_release_quality: float = 0.90

    def validate(self) -> None:
        if self.min_samples < 1:
            raise ValueError("min_samples must be positive")
        if not 0 <= self.max_error_rate <= 1:
            raise ValueError("max_error_rate must be between 0 and 1")
        if self.max_latency_p95_ms < 0:
            raise ValueError("max_latency_p95_ms must be non-negative")
        if not 0 <= self.max_saturation_ratio <= 1:
            raise ValueError("max_saturation_ratio must be between 0 and 1")
        if self.max_security_findings < 0:
            raise ValueError("max_security_findings must be non-negative")
        if not 0 <= self.min_business_health <= 1:
            raise ValueError("min_business_health must be between 0 and 1")
        if not 0 <= self.min_release_quality <= 1:
            raise ValueError("min_release_quality must be between 0 and 1")


@dataclass(frozen=True)
class ThresholdDecision:
    """Release decision with one boolean result per acceptance threshold."""

    passed: bool
    checks: Mapping[str, bool]
    observed: Mapping[str, Any]
    thresholds: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "checks": dict(self.checks),
            "observed": dict(self.observed),
            "thresholds": dict(self.thresholds),
        }


def evaluate_release_thresholds(summary: Any, thresholds: ReleaseThresholds | None = None) -> ThresholdDecision:
    """Evaluate a normalized health summary without persisting sensitive payloads."""
    policy = thresholds or ReleaseThresholds()
    policy.validate()
    observed = {
        "sample_count": int(summary.sample_count),
        "error_rate": float(summary.error_rate),
        "latency_p95_ms": float(summary.latency_p95_ms),
        "saturation_ratio": float(summary.saturation_mean),
        "security_findings": int(summary.security_findings),
        "business_health": summary.business_health,
        "release_quality": summary.release_quality,
    }
    checks = {
        "minimum_samples": observed["sample_count"] >= policy.min_samples,
        "error_rate": observed["error_rate"] <= policy.max_error_rate,
        "latency_p95": observed["latency_p95_ms"] <= policy.max_latency_p95_ms,
        "saturation": observed["saturation_ratio"] <= policy.max_saturation_ratio,
        "security_findings": observed["security_findings"] <= policy.max_security_findings,
        "business_health": observed["business_health"] is not None and observed["business_health"] >= policy.min_business_health,
        "release_quality": observed["release_quality"] is not None and observed["release_quality"] >= policy.min_release_quality,
    }
    return ThresholdDecision(all(checks.values()), checks, observed, asdict(policy))
