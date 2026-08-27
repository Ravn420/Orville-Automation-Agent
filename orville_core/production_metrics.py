"""Tenant- and cohort-scoped production metrics and health sources.

This module provides a standalone contract for aggregating release health
signals without storing prompts, credentials, or arbitrary high-cardinality
payloads. Production adapters can implement ``HealthSource`` to pull metrics
from an approved monitoring system and normalize them into ``MetricSample``.
"""
from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass
from statistics import mean
from typing import Iterable, Mapping, Protocol


class MetricsError(ValueError):
    """Raised when a metric violates the production metrics contract."""


_ALLOWED_NAMES = frozenset({"requests", "errors", "latency_ms", "saturation", "business_health", "security_findings", "release_quality"})


@dataclass(frozen=True)
class MetricSample:
    tenant_id: str
    cohort: str
    release_id: str
    name: str
    value: float
    observed_at: float

    def validate(self) -> None:
        for label, value in (("tenant_id", self.tenant_id), ("cohort", self.cohort), ("release_id", self.release_id), ("name", self.name)):
            if not value or len(value) > 128 or any(char in value for char in "\r\n"):
                raise MetricsError(f"invalid {label}")
        if self.name not in _ALLOWED_NAMES:
            raise MetricsError("unsupported metric name")
        if not math.isfinite(self.value) or not math.isfinite(self.observed_at) or self.observed_at <= 0:
            raise MetricsError("metric value and timestamp must be finite; timestamp must be positive")
        if self.name in {"requests", "errors", "security_findings"} and self.value < 0:
            raise MetricsError("counter metrics cannot be negative")
        if self.name == "saturation" and not 0 <= self.value <= 1:
            raise MetricsError("saturation must be between 0 and 1")
        if self.name == "business_health" and not 0 <= self.value <= 1:
            raise MetricsError("business_health must be between 0 and 1")


@dataclass(frozen=True)
class HealthSummary:
    tenant_id: str
    cohort: str
    release_id: str
    sample_count: int
    requests: float
    errors: float
    error_rate: float
    latency_mean_ms: float
    latency_p95_ms: float
    saturation_mean: float
    business_health: float | None
    security_findings: float
    release_quality: float | None
    observed_at: float

    def to_dict(self) -> dict[str, object]:
        return self.__dict__.copy()

    def to_canary_observation(self):
        """Normalize this summary for the provider-neutral canary evaluator."""
        from .canary import HealthObservation
        return HealthObservation(
            samples=self.sample_count,
            error_rate=self.error_rate,
            p95_latency_ms=self.latency_p95_ms,
            p99_latency_ms=self.latency_p95_ms,
            saturation_ratio=self.saturation_mean,
            critical_security_findings=int(self.security_findings),
            business_health=self.business_health,
            observed_at=self.observed_at,
            release_id=self.release_id,
        )


class HealthSource(Protocol):
    def collect(self, tenant_id: str, cohort: str, release_id: str, *, since: float) -> Iterable[MetricSample]: ...


class InMemoryHealthSource:
    """Bounded local health source for tests, dry runs, and adapter development."""

    def __init__(self, max_samples: int = 10_000) -> None:
        if max_samples < 1:
            raise MetricsError("max_samples must be positive")
        self.max_samples = max_samples
        self._samples: list[MetricSample] = []
        self._lock = threading.RLock()

    def record(self, sample: MetricSample) -> None:
        sample.validate()
        with self._lock:
            self._samples.append(sample)
            if len(self._samples) > self.max_samples:
                del self._samples[: len(self._samples) - self.max_samples]

    def collect(self, tenant_id: str, cohort: str, release_id: str, *, since: float) -> tuple[MetricSample, ...]:
        with self._lock:
            return tuple(sample for sample in self._samples if sample.tenant_id == tenant_id and sample.cohort == cohort and sample.release_id == release_id and sample.observed_at >= since)


class ProductionMetrics:
    """Aggregate normalized health signals with explicit tenant/cohort scope."""

    def __init__(self, source: HealthSource) -> None:
        self.source = source

    def summarize(self, tenant_id: str, cohort: str, release_id: str, *, since: float | None = None) -> HealthSummary:
        if not tenant_id or not cohort or not release_id:
            raise MetricsError("tenant_id, cohort, and release_id are required")
        cutoff = time.time() - 300 if since is None else since
        samples = tuple(self.source.collect(tenant_id, cohort, release_id, since=cutoff))
        for sample in samples:
            sample.validate()
            if (sample.tenant_id, sample.cohort, sample.release_id) != (tenant_id, cohort, release_id):
                raise MetricsError("health source returned an out-of-scope sample")
        grouped: dict[str, list[float]] = {}
        for sample in samples:
            grouped.setdefault(sample.name, []).append(sample.value)
        requests = sum(grouped.get("requests", []))
        errors = sum(grouped.get("errors", []))
        latency = sorted(grouped.get("latency_ms", []))
        p95 = latency[max(0, math.ceil(len(latency) * 0.95) - 1)] if latency else 0.0
        observed_at = max((sample.observed_at for sample in samples), default=0.0)
        return HealthSummary(tenant_id, cohort, release_id, len(samples), requests, errors, errors / requests if requests else 0.0, mean(latency) if latency else 0.0, p95, mean(grouped["saturation"]) if grouped.get("saturation") else 0.0, mean(grouped["business_health"]) if grouped.get("business_health") else None, sum(grouped.get("security_findings", [])), mean(grouped["release_quality"]) if grouped.get("release_quality") else None, observed_at)

    def compare(self, candidate: HealthSummary, baseline: HealthSummary) -> Mapping[str, float]:
        if candidate.tenant_id != baseline.tenant_id or candidate.cohort != baseline.cohort:
            raise MetricsError("cannot compare metrics across tenant or cohort boundaries")
        return {"error_rate_delta": candidate.error_rate - baseline.error_rate, "latency_p95_delta_ms": candidate.latency_p95_ms - baseline.latency_p95_ms, "saturation_delta": candidate.saturation_mean - baseline.saturation_mean, "business_health_delta": (candidate.business_health or 0.0) - (baseline.business_health or 0.0)}
