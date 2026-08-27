"""Approval-gated rollback planning and local recovery verification."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RecoveryVerification:
    """Value-only evidence result for a previously performed recovery drill."""

    passed: bool
    checks: tuple[dict[str, Any], ...]
    residual_risks: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"passed": self.passed, "checks": [dict(item) for item in self.checks], "residual_risks": list(self.residual_risks)}


def build_rollback_plan(*, failed_release: str, rollback_target: str, approval_reference: str) -> tuple[dict[str, str], ...]:
    """Return reviewable rollback steps; never invokes a deployment command."""
    values = {"failed_release": failed_release.strip(), "rollback_target": rollback_target.strip(), "approval_reference": approval_reference.strip()}
    if not all(values.values()):
        raise ValueError("failed_release, rollback_target, and approval_reference are required")
    return (
        {"step": "stop_promotion", "target": values["failed_release"], "approval": values["approval_reference"]},
        {"step": "preserve_evidence", "target": values["failed_release"], "approval": values["approval_reference"]},
        {"step": "restore_approved_target", "target": values["rollback_target"], "approval": values["approval_reference"]},
        {"step": "verify_health_and_smoke", "target": values["rollback_target"], "approval": values["approval_reference"]},
    )


def verify_recovery_evidence(
    backup_path: str | Path,
    *,
    expected_sha256: str,
    health_ok: bool,
    read_only_state_ok: bool,
    smoke_ok: bool,
) -> RecoveryVerification:
    """Verify retained backup and post-recovery evidence without restoring data."""
    path = Path(backup_path).expanduser().resolve()
    checks: list[dict[str, Any]] = []
    if not path.is_file():
        checks.append({"name": "backup_exists", "passed": False})
        return RecoveryVerification(False, tuple(checks), ("backup file is unavailable",))
    checks.append({"name": "backup_exists", "passed": True})
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    checksum_ok = bool(expected_sha256) and digest == expected_sha256.lower()
    checks.append({"name": "backup_checksum", "passed": checksum_ok, "observed_sha256": digest})
    checks.extend(
        (
            {"name": "authenticated_health", "passed": bool(health_ok)},
            {"name": "read_only_state", "passed": bool(read_only_state_ok)},
            {"name": "smoke_workflow", "passed": bool(smoke_ok)},
        )
    )
    passed = all(bool(check["passed"]) for check in checks)
    risks = () if passed else ("recovery evidence is incomplete; do not declare rollback successful",)
    return RecoveryVerification(passed, tuple(checks), risks)
