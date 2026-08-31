from pathlib import Path


CHECKPOINT = Path(__file__).parents[1] / "artifacts" / "BROWSER_SESSION_ADAPTER_CHECKPOINT_2026-08-28.md"


def test_checkpoint_covers_required_browser_adapter_capabilities() -> None:
    text = CHECKPOINT.read_text(encoding="utf-8")
    for phrase in ("Session creation and persistence", "Domain policy", "Navigation", "Takeover", "Audit", "API boundary", "GUI boundary"):
        assert phrase in text
    assert "read_only: true" in text
    assert "headless: true" in text


def test_checkpoint_contains_reproducible_validation_commands() -> None:
    text = CHECKPOINT.read_text(encoding="utf-8")
    assert "python -m pytest" in text
    assert "tests/test_local_browser_session_adapter.py" in text
    assert "python -m compileall -q orville_core windows_gui.py" in text
    assert "git diff --check" in text
    assert "16 passing tests" in text


def test_checkpoint_states_external_runtime_and_secret_boundaries() -> None:
    text = CHECKPOINT.read_text(encoding="utf-8")
    assert "does not retain credentials" in text
    assert "real external browser login" in text
    assert "requires explicit restart/approval" in text
    assert "new approval rather than automatic replay" in text
