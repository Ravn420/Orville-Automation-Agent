"""Deterministic acceptance evaluation for Orville task outputs."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Callable, Iterable


@dataclass(frozen=True)
class EvaluationCheck:
    name: str
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvaluationResult:
    passed: bool
    checks: tuple[EvaluationCheck, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"passed": self.passed, "checks": [check.to_dict() for check in self.checks]}


def evaluate_output(output: Any, acceptance_criteria: Iterable[str] = (), checks: Iterable[Callable[[Any], EvaluationCheck]] = ()) -> EvaluationResult:
    results: list[EvaluationCheck] = []
    if output is None:
        results.append(EvaluationCheck("non_empty_output", False, "output is None"))
    elif isinstance(output, str) and not output.strip():
        results.append(EvaluationCheck("non_empty_output", False, "output is blank"))
    else:
        results.append(EvaluationCheck("non_empty_output", True, "output is present"))
    for criterion in acceptance_criteria:
        needle = criterion.strip()
        if not needle:
            continue
        present = needle.lower() in str(output).lower()
        results.append(EvaluationCheck(f"criterion:{needle}", present, "criterion found" if present else "criterion not found"))
    for check in checks:
        results.append(check(output))
    return EvaluationResult(all(check.passed for check in results), tuple(results))
