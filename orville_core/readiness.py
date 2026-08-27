"""Deterministic production-readiness evaluation for Orville deployments."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Iterable

from .adapters import AdapterHealth, AdapterRegistry, AdapterStatus


@dataclass(frozen=True)
class ReadinessCheck:
    check_id: str
    passed: bool
    severity: str
    message: str
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReadinessReport:
    ready: bool
    checks: tuple[ReadinessCheck, ...]
    blocking_checks: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"ready": self.ready, "checks": [check.__dict__ for check in self.checks], "blocking_checks": list(self.blocking_checks)}


class ProductionReadiness:
    def __init__(self, adapters: AdapterRegistry) -> None:
        self.adapters = adapters

    def evaluate(self, *, tests_passed: bool, compile_passed: bool, required_adapters: Iterable[tuple[str, str]] = ()) -> ReadinessReport:
        checks: list[ReadinessCheck] = [
            ReadinessCheck("tests", tests_passed, "blocker", "Regression tests pass" if tests_passed else "Regression tests failed"),
            ReadinessCheck("compile", compile_passed, "blocker", "Compilation passes" if compile_passed else "Compilation failed"),
            ReadinessCheck("api_token", bool(os.getenv("ORVILLE_API_TOKEN")) and os.getenv("ORVILLE_API_TOKEN") != "replace-with-a-high-entropy-secret", "blocker", "API token is configured" if os.getenv("ORVILLE_API_TOKEN") else "API token is not configured"),
        ]
        for adapter_id, capability in required_adapters:
            try:
                health = self.adapters.require(adapter_id, capability)
                checks.append(ReadinessCheck(f"adapter:{adapter_id}:{capability}", True, "blocker", f"{adapter_id} supports {capability}", (health.status.value,)))
            except (KeyError, RuntimeError) as exc:
                checks.append(ReadinessCheck(f"adapter:{adapter_id}:{capability}", False, "blocker", str(exc)))
        blocking = tuple(check.check_id for check in checks if not check.passed and check.severity == "blocker")
        return ReadinessReport(not blocking, tuple(checks), blocking)
