"""Durable canary controller and deterministic health evaluation primitives."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from .canary_policy import CanaryPolicy


@dataclass(frozen=True)
class HealthWindow:
    """Metric window bound to one release and cohort."""

    release_id: str
    cohort: str
    samples: int
    error_rate: float
    p95_latency_ms: float
    p99_latency_ms: float
    saturation_ratio: float
    security_findings: int = 0
    business_health: float | None = None
    crash: bool = False
    provider_available: bool = True
    observed_seconds: int = 0
    decision_id: str = ""


@dataclass(frozen=True)
class HealthDecision:
    outcome: str
    reasons: tuple[str, ...]
    release_id: str
    cohort: str
    decision_id: str


class HealthEvaluator:
    """Evaluate a fresh metric window without treating sparse data as healthy."""

    def evaluate(self, policy: CanaryPolicy, window: HealthWindow, *, expected_release: str, expected_cohort: str) -> HealthDecision:
        policy.validate()
        reasons: list[str] = []
        if window.release_id != expected_release or window.cohort != expected_cohort:
            reasons.append("stale_or_mismatched_window")
        minimum = policy.health.min_samples
        cohort = next(item for item in policy.cohorts if item.name == expected_cohort)
        minimum = max(minimum, cohort.min_samples or 0)
        if window.samples < minimum:
            reasons.append("insufficient_samples")
        if window.observed_seconds < policy.observation_window_seconds:
            reasons.append("observation_window_incomplete")
        if window.error_rate > policy.health.max_error_rate:
            reasons.append("error_rate_threshold_exceeded")
        if window.p95_latency_ms > policy.health.max_p95_latency_ms:
            reasons.append("p95_latency_threshold_exceeded")
        if window.p99_latency_ms > policy.health.max_p99_latency_ms:
            reasons.append("p99_latency_threshold_exceeded")
        if window.saturation_ratio > policy.health.max_saturation_ratio:
            reasons.append("saturation_threshold_exceeded")
        if policy.health.min_business_health is not None and (window.business_health is None or window.business_health < policy.health.min_business_health):
            reasons.append("business_health_threshold_breached")
        if window.security_findings > policy.health.critical_security_findings:
            reasons.append("critical_security_findings")
        if window.crash:
            reasons.append("deployment_crash")
        if not window.provider_available:
            reasons.append("health_provider_unavailable")
        outcome = "pass" if not reasons else ("rollback" if any(reason in reasons for reason in ("critical_security_findings", "deployment_crash", "error_rate_threshold_exceeded", "p99_latency_threshold_exceeded")) else "pause")
        return HealthDecision(outcome, tuple(reasons), expected_release, expected_cohort, window.decision_id or datetime.now(UTC).strftime("health-%Y%m%d%H%M%S%f"))


class DeploymentAdapter(Protocol):
    def deploy(self, release_id: str) -> None: ...
    def set_traffic(self, release_id: str, traffic_percent: int) -> None: ...
    def rollback(self, release_id: str, target: str) -> None: ...
    def quarantine(self, release_id: str) -> None: ...


@dataclass
class CanaryState:
    state: str = "planned"
    release_id: str = ""
    rollback_target: str = ""
    cohort_index: int = -1
    traffic_percent: int = 0
    rollback_attempts: int = 0
    last_health_decision_id: str | None = None
    last_mutation_key: str | None = None
    audit: list[dict[str, Any]] = field(default_factory=list)
    state_version: int = 0


class DurableCanaryController:
    """Restart-safe controller with atomic JSON state replacement and idempotency."""

    def __init__(self, state_path: str | Path, adapter: DeploymentAdapter, evaluator: HealthEvaluator | None = None) -> None:
        self.state_path = Path(state_path)
        self.adapter = adapter
        self.evaluator = evaluator or HealthEvaluator()
        self.state = self._load()

    def _load(self) -> CanaryState:
        if not self.state_path.exists():
            return CanaryState()
        data = json.loads(self.state_path.read_text(encoding="utf-8"))
        return CanaryState(**data)

    def _save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        temporary.write_text(json.dumps(asdict(self.state), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self.state_path)

    def _event(self, event: str, **details: Any) -> None:
        self.state.audit.append({"event": event, "at": datetime.now(UTC).isoformat(), **details})
        self.state.state_version += 1
        self._save()

    def start(self, policy: CanaryPolicy) -> CanaryState:
        policy.validate()
        if self.state.state not in {"planned", "failed"}:
            return self.state
        self.state.release_id = policy.release_id
        self.state.rollback_target = policy.rollback_target
        self.state.cohort_index = 0
        self.state.state = "deploying"
        self._save()
        self.adapter.deploy(policy.release_id)
        cohort = policy.cohorts[0]
        self.adapter.set_traffic(policy.release_id, cohort.traffic_percent)
        self.state.traffic_percent = cohort.traffic_percent
        self.state.state = "observing"
        self.state.last_mutation_key = f"{policy.release_id}:{cohort.name}:{cohort.traffic_percent}"
        self._event("canary_started", release_id=policy.release_id, cohort=cohort.name, traffic_percent=cohort.traffic_percent)
        return self.state

    def observe(self, policy: CanaryPolicy, window: HealthWindow) -> CanaryState:
        policy.validate()
        if self.state.state != "observing":
            return self.state
        cohort = policy.cohorts[self.state.cohort_index]
        decision = self.evaluator.evaluate(policy, window, expected_release=self.state.release_id, expected_cohort=cohort.name)
        self.state.last_health_decision_id = decision.decision_id
        self._event("health_decision", outcome=decision.outcome, reasons=list(decision.reasons), cohort=cohort.name, decision_id=decision.decision_id)
        if decision.outcome == "pass":
            if self.state.cohort_index == len(policy.cohorts) - 1:
                self.state.state = "completed"
                self._event("canary_completed", release_id=self.state.release_id)
            else:
                self.state.cohort_index += 1
                next_cohort = policy.cohorts[self.state.cohort_index]
                self.adapter.set_traffic(self.state.release_id, next_cohort.traffic_percent)
                self.state.traffic_percent = next_cohort.traffic_percent
                self.state.last_mutation_key = f"{self.state.release_id}:{next_cohort.name}:{next_cohort.traffic_percent}"
                self._event("cohort_advanced", cohort=next_cohort.name, traffic_percent=next_cohort.traffic_percent)
        elif decision.outcome == "rollback":
            self.rollback(policy)
        else:
            self.state.state = "paused"
            self._event("canary_paused", reasons=list(decision.reasons))
        return self.state

    def rollback(self, policy: CanaryPolicy) -> CanaryState:
        if self.state.rollback_attempts >= policy.rollback.max_attempts:
            self.state.state = "failed"
            self._event("rollback_exhausted", attempts=self.state.rollback_attempts)
            return self.state
        self.state.rollback_attempts += 1
        try:
            self.adapter.rollback(self.state.release_id, policy.rollback_target)
            self.adapter.quarantine(self.state.release_id)
            self.state.state = "rolled_back"
            self._event("rollback_completed", target=policy.rollback_target, attempts=self.state.rollback_attempts)
        except Exception as exc:  # adapter errors are persisted, never treated as success
            self.state.state = "failed" if self.state.rollback_attempts >= policy.rollback.max_attempts else "paused"
            self._event("rollback_failed", attempts=self.state.rollback_attempts, error_type=type(exc).__name__)
        return self.state
