from pathlib import Path


ROOT = Path(__file__).parents[1]
AUDIT = ROOT / "docs" / "PLATFORM_CAPABILITY_AUDIT_2026-08-28.md"


def test_audit_covers_all_requested_platform_areas() -> None:
    text = AUDIT.read_text(encoding="utf-8")
    for area in ("Browser adapter", "Security policy", "API initialization", "GUI capability status"):
        assert area in text
    for evidence in ("orville_core/browser.py", "orville_core/browser_relay.py", "orville_core/security.py", "orville_core/api.py", "orville_core/gui_state.py", "windows_gui.py"):
        assert evidence in text


def test_audit_records_fail_closed_and_approval_boundaries() -> None:
    text = AUDIT.read_text(encoding="utf-8")
    assert "fail-closed" in text
    assert "require approval" in text
    assert "allowlists" in text
    assert "bounded audit events" in text
    assert "No credential, token, cookie" in text


def test_audit_does_not_claim_live_external_operation() -> None:
    text = AUDIT.read_text(encoding="utf-8")
    assert "claim live external browser" in text
    assert "remain deployment-owned" in text
    assert "separately approved environment-specific test plan" in text
