"""Privacy-safe comparison of two Orville trace runs."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import Any, Iterable, Mapping

from .observability import TraceRecord


@dataclass(frozen=True)
class TraceComparisonResult:
    """Stable findings produced by comparing a baseline and candidate run."""

    passed: bool
    nondeterminism: tuple[str, ...]
    regressions: tuple[str, ...]
    repeated_failure_patterns: dict[str, int]
    unexpected_tool_calls: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _as_record(value: TraceRecord | Mapping[str, Any]) -> TraceRecord:
    if isinstance(value, TraceRecord):
        return value
    return TraceRecord(
        str(value["trace_id"]),
        str(value["timestamp"]),
        str(value["event"]),
        dict(value.get("attributes", {})),
    )


def _stable_attributes(attributes: Mapping[str, Any]) -> str:
    ignored = {"timestamp", "started_at", "finished_at", "duration_ms", "run_id", "trace_id", "span_id"}
    stable = {key: value for key, value in attributes.items() if key not in ignored}
    return json.dumps(stable, sort_keys=True, default=str)


def compare_traces(
    baseline: Iterable[TraceRecord | Mapping[str, Any]],
    candidate: Iterable[TraceRecord | Mapping[str, Any]],
    *,
    allowed_tool_calls: Iterable[str] = (),
    latency_regression_ratio: float = 0.20,
) -> TraceComparisonResult:
    """Compare ordered event behavior without comparing volatile IDs/timestamps."""
    if not 0 <= latency_regression_ratio:
        raise ValueError("latency_regression_ratio must be non-negative")
    before = tuple(_as_record(item) for item in baseline)
    after = tuple(_as_record(item) for item in candidate)
    nondeterminism: list[str] = []
    regressions: list[str] = []
    if [item.event for item in before] != [item.event for item in after]:
        nondeterminism.append("event sequence differs")
    for index, (left, right) in enumerate(zip(before, after)):
        if left.event == right.event and _stable_attributes(left.attributes) != _stable_attributes(right.attributes):
            nondeterminism.append(f"attributes differ at event index {index}: {left.event}")
    if len(after) < len(before):
        regressions.append(f"candidate emitted {len(before) - len(after)} fewer events")
    before_durations = [float(item.attributes["duration_ms"]) for item in before if "duration_ms" in item.attributes]
    after_durations = [float(item.attributes["duration_ms"]) for item in after if "duration_ms" in item.attributes]
    if before_durations and after_durations and sum(after_durations) > sum(before_durations) * (1 + latency_regression_ratio):
        regressions.append("candidate total duration regressed")
    failures: dict[str, int] = {}
    for item in after:
        failure = item.attributes.get("failure") or item.attributes.get("error_class")
        if failure:
            key = str(failure)[:128]
            failures[key] = failures.get(key, 0) + 1
    repeated = {key: count for key, count in failures.items() if count > 1}
    allowed = set(allowed_tool_calls)
    unexpected = tuple(sorted({item.event for item in after if item.event.startswith("tool.") and item.event not in allowed}))
    return TraceComparisonResult(not (nondeterminism or regressions or unexpected), tuple(nondeterminism), tuple(regressions), repeated, unexpected)
