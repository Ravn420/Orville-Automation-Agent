from pathlib import Path


CHECKPOINT = Path(__file__).parents[1] / "artifacts" / "BROWSER_WORKFLOW_EXPANSION_CHECKPOINT_2026-08-28.md"


def test_checkpoint_covers_expanded_browser_workflow():
    text = CHECKPOINT.read_text(encoding="utf-8")
    for capability in ("Session creation", "Navigation", "Page extraction", "Form submission", "File download", "Takeover", "Audit and recovery", "Provenance"):
        assert capability in text
    for evidence in ("orville_core/api.py", "orville_core/browser.py", "Signal Room", "SourceRecord", "Citation"):
        assert evidence in text


def test_checkpoint_requires_reproducible_validation():
    text = CHECKPOINT.read_text(encoding="utf-8")
    assert "python -m pytest" in text
    assert "python -m compileall -q orville_core windows_gui.py" in text
    assert "git diff --check" in text
    assert "not literal parity" in text
    assert "approval-gated" in text
