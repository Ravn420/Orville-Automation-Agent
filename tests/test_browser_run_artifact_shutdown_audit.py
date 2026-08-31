from pathlib import Path


AUDIT = Path(__file__).parents[1] / "docs" / "BROWSER_RUN_ARTIFACT_SHUTDOWN_AUDIT_2026-08-28.md"


def test_audit_covers_all_requested_lifecycle_areas() -> None:
    text = AUDIT.read_text(encoding="utf-8")
    for area in ("Browser sessions", "Action state", "Run events", "Artifact storage", "Shutdown lifecycle", "Audit records"):
        assert area in text
    for evidence in ("orville_core/browser.py", "orville_core/api.py", "orville_core/observability.py", "artifacts/"):
        assert evidence in text


def test_audit_defines_security_and_state_invariants() -> None:
    text = AUDIT.read_text(encoding="utf-8")
    for phrase in ("cannot navigate to a non-allowlisted hostname", "read-only and headless", "without approval remains pending", "cannot silently reuse a browser handle", "does not replay pending external actions"):
        assert phrase in text
    assert "secrets and full payloads are excluded" in text


def test_audit_documents_reproducible_commands_and_limitations() -> None:
    text = AUDIT.read_text(encoding="utf-8")
    assert "python -m pytest" in text
    assert "python -m compileall -q orville_core windows_gui.py" in text
    assert "git diff --check" in text
    assert "does not verify a real Playwright installation" in text
    assert "production object store" in text
