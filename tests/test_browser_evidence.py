from __future__ import annotations

import pytest

from orville_core.browser_evidence import build_browser_evidence


def test_browser_evidence_links_run_session_and_artifacts() -> None:
    evidence = build_browser_evidence("run-1", {"session_id": "browser-1", "status": "active", "current_url": "https://docs.example", "audit": [{"at": "now", "event": "navigation.approved", "detail": "docs.example"}]}, artifact_ids=["artifact-1"])
    assert evidence.to_dict()["run_id"] == "run-1"
    assert evidence.to_dict()["artifact_ids"] == ["artifact-1"]
    assert evidence.to_dict()["events"][0]["event"] == "navigation.approved"


def test_browser_evidence_redacts_sensitive_event_details() -> None:
    evidence = build_browser_evidence("run-1", {"audit": [{"event": "form", "detail": "password=secret-value"}]})
    assert evidence.events[0]["detail"] == "[redacted browser detail]"


def test_browser_evidence_requires_run_id() -> None:
    with pytest.raises(ValueError, match="run_id"):
        build_browser_evidence("", {})
