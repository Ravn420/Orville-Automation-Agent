from __future__ import annotations

import pytest

from orville_core.signal_room_browser import browser_signal_room_projection, validate_signal_room_action


def test_projection_is_structured_and_handle_safe() -> None:
    projection = browser_signal_room_projection({"session_id": "browser-1", "status": "active", "current_url": "https://example.test", "title": "Example", "allowed_domains": ["example.test"], "audit": [{}], "_browser": "secret-handle"})
    assert projection["available_actions"] == ["refresh", "close", "extract", "screenshot"]
    assert "_browser" not in projection
    assert projection["audit_count"] == 1


def test_takeover_requires_approval() -> None:
    with pytest.raises(PermissionError, match="approval"):
        validate_signal_room_action("request_takeover")
    validate_signal_room_action("request_takeover", approved=True)


def test_unknown_action_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported"):
        validate_signal_room_action("submit_password")
