from pathlib import Path


EVIDENCE = Path(__file__).parents[1] / "docs" / "SECURITY_PERSISTENCE_FRONTEND_VERIFICATION_2026-08-28.md"


def test_verification_evidence_covers_all_requested_areas():
    text = EVIDENCE.read_text(encoding="utf-8")
    for area in ("Security", "Browser/session persistence", "Clean shutdown/recovery", "Run linkage and artifacts", "Frontend/API wiring"):
        assert area in text
    assert "36 passing tests and one pre-existing failure" in text


def test_verification_records_reproducible_commands_and_known_failure():
    text = EVIDENCE.read_text(encoding="utf-8")
    assert "python -m pytest" in text
    assert "python -m compileall" in text
    assert "git diff --check" in text
    assert "C:/model" in text
    assert "C:\\\\model" in text
    assert "not changed within this verification item" in text
