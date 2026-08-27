from __future__ import annotations

import pytest

from orville_core.browser import BrowserSessionManager
from orville_core.security import SecurityViolation


def test_browser_session_allowlist_and_approval_state() -> None:
    manager = BrowserSessionManager()
    session = manager.create(["Example.com"], headless=True)

    pending = session.navigate("https://docs.example.com/guide", approved=False)
    assert pending["takeover_required"] is True
    assert session.status == "created"

    with pytest.raises(SecurityViolation, match="not allowlisted"):
        session.navigate("https://evil.example.net", approved=False)

    takeover = session.request_takeover(approved=False)
    assert takeover["takeover_required"] is True
    form = session.submit_form("form#login", {"Email": "user@example.com"}, approved=False)
    assert form["takeover_required"] is True
    download = session.download("https://docs.example.com/file.txt", approved=False)
    assert download["takeover_required"] is True
    assert any(item["event"] == "takeover.requested" for item in session.audit)
    assert any(item["event"] == "form_submission.approval_required" for item in session.audit)
    assert any(item["event"] == "download.approval_required" for item in session.audit)


def test_browser_session_rejects_invalid_domains() -> None:
    manager = BrowserSessionManager()
    with pytest.raises(ValueError):
        manager.create(["https://example.com"])
    with pytest.raises(ValueError):
        manager.create([])
