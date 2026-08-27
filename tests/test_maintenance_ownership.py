"""Focused tests for maintenance ownership and upgrade cadence documentation."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "MAINTENANCE_OWNERSHIP_AND_UPGRADE_CADENCE.md"


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def test_maintenance_document_exists_with_owner_roles_and_boundaries() -> None:
    text = _read()
    for term in (
        "Core engine",
        "Provider, connector, browser, and model adapters",
        "Security, secrets, permissions",
        "Windows GUI and accessibility",
        "Packaging, deployment, backup, rollback",
        "Incident response and recovery",
        "Orchestration Agent",
        "environment owner",
    ):
        assert term in text


def test_maintenance_document_defines_required_cadences() -> None:
    text = _read()
    for cadence in ("Every change", "Weekly", "Monthly", "Quarterly", "Before every release", "After every release"):
        assert cadence in text
    assert "backup freshness" in text
    assert "recovery evidence" in text
    assert "observation window" in text


def test_upgrade_and_escalation_rules_are_explicit_and_secret_safe() -> None:
    text = _read()
    for term in ("Security advisories", "compatibility assessment", "migration plan", "rollback target", "explicit approval", "secret exposure", "ambiguous"):
        assert term in text
    assert "secrets and personal data must never appear" in text
    assert "Live schedules" in text
