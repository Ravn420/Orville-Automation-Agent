"""Structured validation and bounded repair contracts for Orville workspaces."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .workspace import CommandResult, WorkspaceSession


@dataclass(frozen=True)
class ValidationCheck:
    check_id: str
    label: str
    command: tuple[str, ...]
    status: str
    returncode: int | None = None
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class ValidationReport:
    passed: bool
    checks: tuple[ValidationCheck, ...]
    failure_classes: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "checks": [check.__dict__ for check in self.checks],
            "failure_classes": list(self.failure_classes),
        }


@dataclass
class RepairBudget:
    max_attempts_per_failure: int = 3
    attempts: dict[str, int] = field(default_factory=dict)

    def can_attempt(self, failure_class: str) -> bool:
        return self.attempts.get(failure_class, 0) < self.max_attempts_per_failure

    def record(self, failure_class: str) -> int:
        if not self.can_attempt(failure_class):
            raise RuntimeError(f"repair budget exhausted for failure class: {failure_class}")
        self.attempts[failure_class] = self.attempts.get(failure_class, 0) + 1
        return self.attempts[failure_class]


class ValidationRunner:
    """Run an explicit, bounded validation ladder inside a workspace."""

    DEFAULT_LADDER: tuple[tuple[str, str, tuple[str, ...]], ...] = (
        ("compile", "Python compile check", ("python", "-m", "compileall", "-q", ".")),
        ("tests", "Unit tests", ("python", "-m", "unittest", "discover", "-s", "tests", "-q")),
    )

    def __init__(self, workspace: WorkspaceSession, *, timeout_seconds: float = 120.0) -> None:
        self.workspace = workspace
        self.timeout_seconds = timeout_seconds

    def run(self, ladder: tuple[tuple[str, str, tuple[str, ...]], ...] | None = None) -> ValidationReport:
        checks: list[ValidationCheck] = []
        failures: list[str] = []
        for check_id, label, command in ladder or self.DEFAULT_LADDER:
            result: CommandResult = self.workspace.run(command, timeout_seconds=self.timeout_seconds)
            status = "passed" if result.returncode == 0 and not result.timed_out else "failed"
            check = ValidationCheck(check_id, label, result.command, status, result.returncode, result.stdout, result.stderr, result.duration_seconds)
            checks.append(check)
            if status != "passed":
                failures.append(check_id)
                break
        return ValidationReport(not failures, tuple(checks), tuple(failures))

    def repair_until_passed(self, repair: Callable[[ValidationCheck, int], None], *, budget: RepairBudget | None = None, ladder: tuple[tuple[str, str, tuple[str, ...]], ...] | None = None) -> tuple[ValidationReport, RepairBudget]:
        active_budget = budget or RepairBudget()
        while True:
            report = self.run(ladder)
            if report.passed or not report.failure_classes:
                return report, active_budget
            failure_class = report.failure_classes[0]
            if not active_budget.can_attempt(failure_class):
                return report, active_budget
            attempt = active_budget.record(failure_class)
            repair(report.checks[-1], attempt)
