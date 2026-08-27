"""Deterministic M13.7 security release-gate aggregation."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib.util import find_spec
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class SecurityGateResult:
    """Redacted, serializable result for one security gate run."""

    passed: bool
    checks: Mapping[str, bool]
    diagnostics: tuple[dict[str, Any], ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {"passed": self.passed, "checks": dict(self.checks), "diagnostics": list(self.diagnostics)}


def run_security_gate(*, root: Path, sandbox_available: bool, required_attestation_verified: bool, dependency_names: tuple[str, ...] = ("cryptography",), audit_evidence_present: bool = True) -> SecurityGateResult:
    """Evaluate M13.7 prerequisites without executing model or external code."""

    checks: dict[str, bool] = {
        "sandbox_boundary": bool(sandbox_available),
        "attestation_boundary": bool(required_attestation_verified),
        "dependency_validation": all(find_spec(name) is not None for name in dependency_names),
        "audit_evidence": bool(audit_evidence_present),
        "security_sources_present": all((root / path).is_file() for path in ("orville_core/sandbox.py", "orville_core/attestations.py", "orville_core/tuf_metadata.py")),
    }
    diagnostics: list[dict[str, Any]] = []
    for check, passed in checks.items():
        if not passed:
            diagnostics.append({"code": f"security_gate_{check}_failed", "severity": "error", "message": f"security gate check failed: {check}"})
    return SecurityGateResult(all(checks.values()), checks, tuple(diagnostics))
