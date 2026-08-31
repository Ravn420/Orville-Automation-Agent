from pathlib import Path


GUI = Path(__file__).parents[1] / "windows_gui.py"


def test_signal_room_exposes_approval_and_recovery_evidence():
    text = GUI.read_text(encoding="utf-8")
    assert "View approvals & recovery" in text
    assert "Session status:" in text
    assert "Recovery/takeover required:" in text
    assert "Approval records:" in text
    assert "local, bounded, and redacted" in text


def test_execution_monitor_surfaces_run_sources_and_citations():
    text = GUI.read_text(encoding="utf-8")
    assert "Source records:" in text
    assert "Citations:" in text
    assert 'result.get("source_records", [])' in text
    assert 'result.get("citations", [])' in text


def test_existing_signal_room_browser_workflow_remains_present():
    text = GUI.read_text(encoding="utf-8")
    for label in ("Create read-only session", "Approve navigation", "Navigate", "Request takeover", "View audit"):
        assert label in text
