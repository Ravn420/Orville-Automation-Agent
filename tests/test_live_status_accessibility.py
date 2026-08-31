from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (ROOT / "docs" / "LIVE_STATUS_ACCESSIBILITY.md").read_text(encoding="utf-8")


def test_live_status_contract_covers_required_states_and_semantics():
    for phrase in (
        'role="status"',
        'aria-live="polite"',
        'role="alert"',
        "Running",
        "Paused",
        "Completed",
        "Partial failure",
        "Failed",
        "Approval required",
        "Offline/cancelled",
        "No focus steal",
    ):
        assert phrase in CONTRACT


def test_live_status_contract_rejects_color_only_communication():
    assert "must never depend on color alone" in CONTRACT
    assert "visible text" in CONTRACT
    assert "recovery guidance" in CONTRACT
