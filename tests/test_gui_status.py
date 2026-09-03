from __future__ import annotations

from orville_core.gui_status import accessible_status


def test_normal_status_is_polite_and_text_first() -> None:
    result = accessible_status("long_running")
    assert result.role == "status"
    assert result.live == "polite"
    assert result.color_independent is True
    assert "Still working" in result.text


def test_urgent_status_uses_assertive_alert() -> None:
    result = accessible_status("failed", urgent=True)
    assert result.role == "alert"
    assert result.live == "assertive"
    assert "Could not complete" in result.text


def test_unknown_state_fails_safe_to_error_message() -> None:
    result = accessible_status("provider-secret-state")
    assert result.state == "failed"
    assert "provider-secret-state" not in result.text
    assert result.color_independent is True
