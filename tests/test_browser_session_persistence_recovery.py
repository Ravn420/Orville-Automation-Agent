import json
from pathlib import Path

from orville_core.browser import BrowserSessionManager


def test_shutdown_persists_recovered_session_without_browser_handle(tmp_path: Path) -> None:
    state_path = tmp_path / "browser-sessions.json"
    manager = BrowserSessionManager(state_path)
    session = manager.create(["example.com"])
    session.status = "active"
    manager.shutdown()

    persisted = json.loads(state_path.read_text(encoding="utf-8"))
    assert persisted[0]["session_id"] == session.session_id
    assert persisted[0]["status"] == "recovered"
    assert persisted[0]["takeover_required"] is True
    assert any(event["event"] == "session.shutdown" for event in persisted[0]["audit"])

    recovered = BrowserSessionManager(state_path).get(session.session_id)
    assert recovered.status == "recovered"
    assert recovered.takeover_required is True
    assert recovered._page is None


def test_recovery_does_not_reopen_a_browser_or_replay_actions(tmp_path: Path) -> None:
    state_path = tmp_path / "browser-sessions.json"
    state_path.write_text(json.dumps([{"session_id": "browser-old", "allowed_domains": ["example.com"], "status": "active", "current_url": "https://example.com/", "audit": [{"event": "navigation.approved", "detail": "https://example.com/"}]}]), encoding="utf-8")

    manager = BrowserSessionManager(state_path)
    recovered = manager.get("browser-old")
    assert recovered.status == "recovered"
    assert recovered.takeover_required is True
    assert recovered._playwright is None
    assert recovered._browser is None
    assert recovered.audit[-1]["event"] == "session.recovered"


def test_shutdown_is_safe_to_repeat_for_recovered_sessions(tmp_path: Path) -> None:
    state_path = tmp_path / "browser-sessions.json"
    manager = BrowserSessionManager(state_path)
    manager.create(["example.com"])
    manager.shutdown()
    manager.shutdown()
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    assert payload[0]["status"] == "recovered"
