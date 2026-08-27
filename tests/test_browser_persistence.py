from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from orville_core.browser import BrowserSessionManager


def test_browser_session_metadata_recovers_after_shutdown() -> None:
    with TemporaryDirectory() as directory:
        state_path = Path(directory) / "browser-sessions.json"
        first = BrowserSessionManager(state_path)
        session = first.create(["docs.example.com"])
        session.navigate("https://docs.example.com/guide", approved=False)
        first.persist()

        recovered = BrowserSessionManager(state_path)
        restored = recovered.get(session.session_id)
        assert restored.status == "recovered"
        assert restored.takeover_required is True
        assert restored.current_url is None
        assert any(item["event"] == "session.recovered" for item in restored.audit)

        recovered.shutdown()
        final = BrowserSessionManager(state_path)
        assert final.get(session.session_id).status == "recovered"
