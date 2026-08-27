"""Secret-safe repeated-failure analysis for completed task-graph runs."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import re
from typing import Any


_FAILURE_EVENTS = frozenset({"task_failed", "task_verification_failed", "run_failed", "task_blocked"})
_MAX_LABEL_LENGTH = 96
_MAX_PATTERNS = 32


@dataclass(frozen=True)
class FailurePattern:
    """An aggregate failure pattern with no raw error or payload data."""

    pattern: str
    count: int
    run_count: int
    task_count: int
    event_types: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern": self.pattern,
            "count": self.count,
            "run_count": self.run_count,
            "task_count": self.task_count,
            "event_types": list(self.event_types),
        }


def _safe_failure_class(event: Mapping[str, Any]) -> str:
    """Extract a bounded class label from event metadata, never raw error text."""
    details = event.get("details") if isinstance(event.get("details"), Mapping) else {}
    explicit = details.get("failure_class")
    if isinstance(explicit, str) and explicit.strip():
        return re.sub(r"[^a-zA-Z0-9_.-]+", "_", explicit.strip().lower())[:_MAX_LABEL_LENGTH]
    error = details.get("error")
    if isinstance(error, str) and error.strip():
        prefix = error.split(":", 1)[0].strip().lower()
        return re.sub(r"[^a-zA-Z0-9_.-]+", "_", prefix)[:_MAX_LABEL_LENGTH] or "unknown"
    reason = details.get("reason")
    if isinstance(reason, str) and reason.strip():
        return re.sub(r"[^a-zA-Z0-9_.-]+", "_", reason.strip().lower())[:_MAX_LABEL_LENGTH]
    return "unknown"


def review_completed_task_graphs(
    runs: Iterable[Mapping[str, Any]],
    *,
    minimum_occurrences: int = 2,
    max_patterns: int = _MAX_PATTERNS,
) -> dict[str, Any]:
    """Return repeated failure patterns from completed run records.

    Only failure event types and safe class labels are retained. Raw errors,
    prompts, outputs, URLs, credentials, and event payloads are not returned.
    """
    if minimum_occurrences < 2:
        raise ValueError("minimum_occurrences must be >= 2")
    if max_patterns < 1:
        raise ValueError("max_patterns must be >= 1")

    completed_runs = 0
    failures_by_pattern: dict[str, list[tuple[str, str, str]]] = {}
    for index, run in enumerate(runs):
        run_status = str(run.get("run_status", run.get("status", ""))).lower()
        if run_status and run_status not in {"completed", "failed", "blocked", "cancelled"}:
            continue
        completed_runs += 1
        fallback_run_id = f"run-{index + 1}"
        run_id = str(run.get("run_id") or fallback_run_id)[:96]
        events = run.get("events", [])
        if not isinstance(events, Iterable) or isinstance(events, (str, bytes, Mapping)):
            continue
        for event in events:
            if not isinstance(event, Mapping):
                continue
            event_type = str(event.get("event_type", event.get("type", "")))
            if event_type not in _FAILURE_EVENTS:
                continue
            failure_class = _safe_failure_class(event)
            pattern = f"{event_type}:{failure_class}"
            task_id = str(event.get("task_id") or "unknown")[:96]
            failures_by_pattern.setdefault(pattern, []).append((run_id, task_id, event_type))

    patterns: list[FailurePattern] = []
    for pattern, occurrences in failures_by_pattern.items():
        if len(occurrences) < minimum_occurrences:
            continue
        patterns.append(
            FailurePattern(
                pattern=pattern,
                count=len(occurrences),
                run_count=len({item[0] for item in occurrences}),
                task_count=len({item[1] for item in occurrences}),
                event_types=tuple(sorted({item[2] for item in occurrences})),
            )
        )
    patterns.sort(key=lambda item: (-item.count, item.pattern))
    patterns = patterns[:max_patterns]
    return {
        "completed_runs": completed_runs,
        "failure_event_count": sum(len(items) for items in failures_by_pattern.values()),
        "repeated_pattern_count": len(patterns),
        "patterns": [pattern.to_dict() for pattern in patterns],
        "recommendation": (
            "Review the highest-count patterns and convert confirmed recurring fixes into tests, templates, or runbook changes."
            if patterns
            else "No repeated failure pattern met the configured occurrence threshold."
        ),
    }
