"""Versioned, deterministic canary-deployment policy contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


class CanaryPolicyError(ValueError):
    """Raised when a canary policy violates safety or boundedness rules."""


@dataclass(frozen=True)
class HealthThresholds:
    """Minimum-sample health thresholds evaluated over an observation window."""

    min_samples: int = 100
    max_error_rate: float = 0.02
    max_p95_latency_ms: float = 1000.0
    max_p99_latency_ms: float = 2000.0
    max_saturation_ratio: float = 0.90
    critical_security_findings: int = 0
    min_business_health: float | None = None
    confidence_level: float = 0.95

    def validate(self) -> None:
        if self.min_samples < 1:
            raise CanaryPolicyError("min_samples must be positive")
        if not 0 <= self.max_error_rate <= 1:
            raise CanaryPolicyError("max_error_rate must be between 0 and 1")
        if self.max_p95_latency_ms <= 0 or self.max_p99_latency_ms < self.max_p95_latency_ms:
            raise CanaryPolicyError("latency thresholds must be positive and p99 >= p95")
        if not 0 < self.max_saturation_ratio <= 1:
            raise CanaryPolicyError("max_saturation_ratio must be in (0, 1]")
        if self.critical_security_findings < 0:
            raise CanaryPolicyError("critical_security_findings cannot be negative")
        if self.min_business_health is not None and not 0 <= self.min_business_health <= 1:
            raise CanaryPolicyError("min_business_health must be between 0 and 1")
        if not 0 < self.confidence_level < 1:
            raise CanaryPolicyError("confidence_level must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        return {
            "min_samples": self.min_samples,
            "max_error_rate": self.max_error_rate,
            "max_p95_latency_ms": self.max_p95_latency_ms,
            "max_p99_latency_ms": self.max_p99_latency_ms,
            "max_saturation_ratio": self.max_saturation_ratio,
            "critical_security_findings": self.critical_security_findings,
            "min_business_health": self.min_business_health,
            "confidence_level": self.confidence_level,
        }


@dataclass(frozen=True)
class CanaryCohort:
    """One monotonic traffic step and its bounded observation hold."""

    name: str
    traffic_percent: int
    hold_seconds: int = 300
    min_samples: int | None = None
    selector: Mapping[str, str] = field(default_factory=dict)

    def validate(self, previous_percent: int = 0, max_hold_seconds: int = 3600) -> None:
        if not self.name.strip():
            raise CanaryPolicyError("cohort name must not be empty")
        if not 0 < self.traffic_percent <= 100:
            raise CanaryPolicyError("cohort traffic_percent must be in 1..100")
        if self.traffic_percent <= previous_percent:
            raise CanaryPolicyError("cohort traffic percentages must increase monotonically")
        if not 0 < self.hold_seconds <= max_hold_seconds:
            raise CanaryPolicyError("cohort hold_seconds exceeds policy bounds")
        if self.min_samples is not None and self.min_samples < 1:
            raise CanaryPolicyError("cohort min_samples must be positive")
        if any(not str(key).strip() or not str(value).strip() for key, value in self.selector.items()):
            raise CanaryPolicyError("cohort selectors must contain non-empty keys and values")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "traffic_percent": self.traffic_percent,
            "hold_seconds": self.hold_seconds,
            "min_samples": self.min_samples,
            "selector": dict(self.selector),
        }


@dataclass(frozen=True)
class RollbackLimits:
    """Bounded rollback and quarantine behavior."""

    max_attempts: int = 3
    timeout_seconds: int = 300
    quarantine_seconds: int = 3600
    require_known_good_target: bool = True
    pause_on_critical_security: bool = True

    def validate(self) -> None:
        if not 1 <= self.max_attempts <= 10:
            raise CanaryPolicyError("rollback max_attempts must be between 1 and 10")
        if not 1 <= self.timeout_seconds <= 3600:
            raise CanaryPolicyError("rollback timeout_seconds must be between 1 and 3600")
        if not 0 <= self.quarantine_seconds <= 86400:
            raise CanaryPolicyError("quarantine_seconds must be between 0 and 86400")
        if not self.require_known_good_target:
            raise CanaryPolicyError("rollback requires a known-good target")

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_attempts": self.max_attempts,
            "timeout_seconds": self.timeout_seconds,
            "quarantine_seconds": self.quarantine_seconds,
            "require_known_good_target": self.require_known_good_target,
            "pause_on_critical_security": self.pause_on_critical_security,
        }


@dataclass(frozen=True)
class CanaryPolicy:
    """Complete M13.8 policy, safe to serialize and validate before mutation."""

    policy_version: int = 1
    policy_id: str = "default-canary-v1"
    release_id: str = ""
    rollback_target: str = ""
    cohorts: tuple[CanaryCohort, ...] = ()
    health: HealthThresholds = field(default_factory=HealthThresholds)
    rollback: RollbackLimits = field(default_factory=RollbackLimits)
    max_hold_seconds: int = 3600
    approval_mode: str = "per_step"
    observation_window_seconds: int = 300
    require_fresh_health_decision: bool = True

    def validate(self) -> None:
        if self.policy_version != 1:
            raise CanaryPolicyError("unsupported canary policy_version")
        if not self.policy_id.strip() or not self.release_id.strip():
            raise CanaryPolicyError("policy_id and release_id are required")
        if not self.rollback_target.strip():
            raise CanaryPolicyError("rollback_target is required")
        if not self.cohorts:
            raise CanaryPolicyError("at least one canary cohort is required")
        if self.max_hold_seconds < 1 or self.max_hold_seconds > 86400:
            raise CanaryPolicyError("max_hold_seconds must be bounded")
        if self.approval_mode not in {"none", "initial", "per_step", "always"}:
            raise CanaryPolicyError("approval_mode is invalid")
        if not 1 <= self.observation_window_seconds <= self.max_hold_seconds:
            raise CanaryPolicyError("observation_window_seconds is invalid")
        if not self.require_fresh_health_decision:
            raise CanaryPolicyError("fresh health decisions are mandatory")
        self.health.validate()
        self.rollback.validate()
        previous = 0
        for cohort in self.cohorts:
            cohort.validate(previous, self.max_hold_seconds)
            previous = cohort.traffic_percent
        if previous != 100:
            raise CanaryPolicyError("final cohort must reach 100 percent traffic")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema": "orville.canary.policy",
            "policy_version": self.policy_version,
            "policy_id": self.policy_id,
            "release_id": self.release_id,
            "rollback_target": self.rollback_target,
            "cohorts": [cohort.to_dict() for cohort in self.cohorts],
            "health": self.health.to_dict(),
            "rollback": self.rollback.to_dict(),
            "max_hold_seconds": self.max_hold_seconds,
            "approval_mode": self.approval_mode,
            "observation_window_seconds": self.observation_window_seconds,
            "require_fresh_health_decision": self.require_fresh_health_decision,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CanaryPolicy":
        try:
            health_data = data.get("health", {})
            rollback_data = data.get("rollback", {})
            cohorts = tuple(CanaryCohort(**item) for item in data.get("cohorts", []))
            policy = cls(
                policy_version=int(data.get("policy_version", 0)),
                policy_id=str(data.get("policy_id", "")),
                release_id=str(data.get("release_id", "")),
                rollback_target=str(data.get("rollback_target", "")),
                cohorts=cohorts,
                health=HealthThresholds(**health_data),
                rollback=RollbackLimits(**rollback_data),
                max_hold_seconds=int(data.get("max_hold_seconds", 3600)),
                approval_mode=str(data.get("approval_mode", "per_step")),
                observation_window_seconds=int(data.get("observation_window_seconds", 300)),
                require_fresh_health_decision=bool(data.get("require_fresh_health_decision", True)),
            )
        except (TypeError, ValueError) as exc:
            raise CanaryPolicyError(f"invalid canary policy shape: {exc}") from exc
        policy.validate()
        return policy
