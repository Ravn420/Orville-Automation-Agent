"""Dependency-free operational telemetry for Orville."""

from __future__ import annotations

import json
import math
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any


@dataclass
class MetricSeries:
    name: str
    count: int = 0
    failures: int = 0
    durations: list[float] = field(default_factory=list)
    values: list[float] = field(default_factory=list)
    retry_count: int = 0
    failure_classes: dict[str, int] = field(default_factory=dict)
    verification_outcomes: dict[str, int] = field(default_factory=dict)

    def snapshot(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "count": self.count,
            "failures": self.failures,
            "failure_rate": self.failures / self.count if self.count else 0.0,
            "success_rate": (self.count - self.failures) / self.count if self.count else 0.0,
            "duration_mean": mean(self.durations) if self.durations else 0.0,
            "value_mean": mean(self.values) if self.values else 0.0,
            "retry_count": self.retry_count,
            "failure_classes": dict(self.failure_classes),
            "verification_outcomes": dict(self.verification_outcomes),
        }


class TelemetryRegistry:
    def __init__(self) -> None:
        self._series: dict[str, MetricSeries] = {}
        self._phases: dict[str, MetricSeries] = {}
        self._lock = threading.RLock()

    def record(
        self,
        name: str,
        *,
        success: bool = True,
        duration_seconds: float | None = None,
        value: float | None = None,
        retry_count: int = 0,
        failure_class: str | None = None,
        verification_outcome: str | None = None,
    ) -> None:
        """Record bounded operational metrics without retaining sensitive payloads."""
        if retry_count < 0:
            raise ValueError("retry_count must not be negative")
        normalized_failure = failure_class.strip()[:128] if failure_class and failure_class.strip() else None
        normalized_verification = verification_outcome.strip()[:64] if verification_outcome and verification_outcome.strip() else None
        with self._lock:
            series = self._series.setdefault(name, MetricSeries(name))
            series.count += 1
            if not success:
                series.failures += 1
                if normalized_failure:
                    series.failure_classes[normalized_failure] = series.failure_classes.get(normalized_failure, 0) + 1
            series.retry_count += int(retry_count)
            if normalized_verification:
                series.verification_outcomes[normalized_verification] = series.verification_outcomes.get(normalized_verification, 0) + 1
            if duration_seconds is not None:
                series.durations.append(float(duration_seconds))
            if value is not None:
                series.values.append(float(value))

    def record_phase_duration(self, phase: str, duration_seconds: float) -> None:
        """Record one bounded planning, execution, verification, or recovery duration."""
        normalized_phase = phase.strip().lower()
        if normalized_phase not in {"planning", "execution", "verification", "recovery"}:
            raise ValueError("phase must be planning, execution, verification, or recovery")
        if not math.isfinite(duration_seconds) or duration_seconds < 0:
            raise ValueError("duration_seconds must be finite and non-negative")
        with self._lock:
            series = self._phases.setdefault(normalized_phase, MetricSeries(normalized_phase))
            series.count += 1
            series.durations.append(float(duration_seconds))

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "recorded_at": datetime.now(UTC).isoformat(),
                "metrics": {name: series.snapshot() for name, series in self._series.items()},
                "phases": {name: series.snapshot() for name, series in self._phases.items()},
            }

    def export(self, path: str | Path) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(self.snapshot(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return destination
