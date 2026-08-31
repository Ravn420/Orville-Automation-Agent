import json
from pathlib import Path

import pytest

from orville_core.browser import BrowserSessionManager
from orville_core.security import SecurityViolation


def test_new_session_is_read_only_and_headless_by_default(tmp_path: Path) -> None:
    manager = BrowserSessionManager(tmp_path / "browser-sessions.json")
    session = manager.create(["Example.COM."])

    assert session.read_only is True
    assert session.headless is True
    assert session.allowed_domains == {"example.com"}
    assert session.to_dict()["read_only"] is True
    assert session.audit[-1]["event"] == "session.created"


def test_navigation_requires_approval_and_rejects_non_allowlisted_urls(tmp_path: Path) -> None:
    manager = BrowserSessionManager(tmp_path / "browser-sessions.json")
    session = manager.create(["example.com"])

    pending = session.navigate("https://example.com/docs")
    assert pending["takeover_required"] is True
    assert session.audit[-1]["event"] == "navigation.approval_required"

    with pytest.raises(SecurityViolation, match="not allowlisted"):
        session.navigate("https://notexample.com/")


def test_read_only_policy_survives_persistence_and_recovery(tmp_path: Path) -> None:
    state_path = tmp_path / "browser-sessions.json"
    manager = BrowserSessionManager(state_path)
    session = manager.create(["example.com"], read_only=True)
    manager.persist()

    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert payload[0]["read_only"] is True

    recovered = BrowserSessionManager(state_path).get(session.session_id)
    assert recovered.read_only is True
    assert recovered.status == "recovered"
    assert recovered.takeover_required is True
