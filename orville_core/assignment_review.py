"""Aggregate review of agent assignment performance."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from statistics import mean
from typing import Any


_MAX_AGENT_LABEL = 96
_MAX_RECORDS = 10_000


@dataclass
class AssignmentStats:
    """Non-identifying aggregate performance statistics for one assignment label."""

    agent: str
    tasks: int = 0
    completed: int = 0
    failed: int = 0
    verification_failures: int = 0
    attempts: list[int] | None = None
    durations: list[float] | None = None

    def __post_init__(self) -> None:
        self.attempts = [] if self.attempts is None else self.attempts
        self.durations = [] if self.durations is None else self.durations

    def snapshot(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "tasks": self.tasks,
            "completed": self.completed,
            "failed": self.failed,
            "failure_rate": self.failed / self.tasks if self.tasks else 0.0,
            "verification_failures": self.verification_failures,
            "attempts_mean": mean(self.attempts) if self.attempts else 0.0,
            "duration_mean": mean(self.durations) if self.durations else 0.0,
        }


def _label(value: Any, fallback: str = "unassigned") -> str:
    if not isinstance(value, str) or not value.strip():
        return fallback
    return value.strip()[:_MAX_AGENT_LABEL]


def review_assignment_performance(runs: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate assignment outcomes from bounded, sanitized terminal run records.

    The report does not retain task titles, prompts, outputs, raw errors, paths,
    credentials, or personal data, and it does not rank or automatically reassign agents.
    """
    stats: dict[str, AssignmentStats] = {}
    considered_runs = 0
    records = 0
    for run in runs:
        if records >= _MAX_RECORDS:
            break
        status = str(run.get("run_status", run.get("status", ""))).lower()
        if status and status not in {"completed", "failed", "blocked", "cancelled"}:
            continue
        considered_runs += 1
        tasks = run.get("tasks", [])
        if not isinstance(tasks, Iterable) or isinstance(tasks, (str, bytes, Mapping)):
            continue
        for task in tasks:
            if records >= _MAX_RECORDS or not isinstance(task, Mapping):
                break
            records += 1
            details = task.get("details") if isinstance(task.get("details"), Mapping) else {}
            agent = _label(task.get("agent") or task.get("owner") or details.get("agent"))
            current = stats.setdefault(agent, AssignmentStats(agent))
            current.tasks += 1
            task_status = str(task.get("status", "")).lower()
            if task_status in {"verified", "completed", "success"}:
                current.completed += 1
            if task_status in {"failed", "blocked", "cancelled"}:
                current.failed += 1
            if bool(task.get("verification_failed")) or task_status == "verification_failed":
                current.verification_failures += 1
            attempts = task.get("attempts")
            if isinstance(attempts, int) and attempts >= 0:
                current.attempts.append(attempts)
            duration = task.get("duration_seconds")
            if isinstance(duration, (int, float)) and duration >= 0:
                current.durations.append(float(duration))
    rows = [item.snapshot() for item in sorted(stats.values(), key=lambda item: item.agent)]
    return {
        "considered_runs": considered_runs,
        "considered_tasks": records,
        "assignment_count": len(rows),
        "assignments": rows,
        "recommendation": (
            "Review high-failure or high-verification-failure assignments with context before changing role mappings."
            if any(row["failed"] or row["verification_failures"] for row in rows)
            else "No assignment-level failure signal was present in the reviewed records."
        ),
    }
