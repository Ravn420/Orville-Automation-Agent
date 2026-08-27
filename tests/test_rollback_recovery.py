"""Focused tests for rollback planning and local recovery verification."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from orville_core import RecoveryVerification, build_rollback_plan, verify_recovery_evidence


def test_rollback_plan_requires_explicit_target_and_approval() -> None:
    plan = build_rollback_plan(failed_release="release-bad", rollback_target="release-good", approval_reference="approval-17")
    assert [step["step"] for step in plan] == ["stop_promotion", "preserve_evidence", "restore_approved_target", "verify_health_and_smoke"]
    assert all(step["approval"] == "approval-17" for step in plan)
    with pytest.raises(ValueError):
        build_rollback_plan(failed_release="release-bad", rollback_target="", approval_reference="approval-17")


def test_recovery_verification_requires_matching_backup_and_all_checks(tmp_path: Path) -> None:
    backup = tmp_path / "backup.sqlite"
    backup.write_bytes(b"synthetic backup")
    digest = hashlib.sha256(backup.read_bytes()).hexdigest()
    result = verify_recovery_evidence(backup, expected_sha256=digest, health_ok=True, read_only_state_ok=True, smoke_ok=True)
    assert isinstance(result, RecoveryVerification)
    assert result.passed is True
    assert {check["name"] for check in result.checks} == {"backup_exists", "backup_checksum", "authenticated_health", "read_only_state", "smoke_workflow"}
    assert result.residual_risks == ()


def test_failed_recovery_evidence_is_not_success(tmp_path: Path) -> None:
    backup = tmp_path / "backup.sqlite"
    backup.write_bytes(b"synthetic backup")
    result = verify_recovery_evidence(backup, expected_sha256="0" * 64, health_ok=True, read_only_state_ok=False, smoke_ok=True)
    assert result.passed is False
    assert result.residual_risks
    assert any(check["name"] == "read_only_state" and check["passed"] is False for check in result.checks)


def test_missing_backup_fails_closed_without_restoration(tmp_path: Path) -> None:
    result = verify_recovery_evidence(tmp_path / "missing.sqlite", expected_sha256="a" * 64, health_ok=True, read_only_state_ok=True, smoke_ok=True)
    assert result.passed is False
    assert result.checks == ({"name": "backup_exists", "passed": False},)
    assert "unavailable" in result.residual_risks[0]
