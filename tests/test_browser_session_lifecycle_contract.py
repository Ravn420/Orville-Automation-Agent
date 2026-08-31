from pathlib import Path


DOC = Path(__file__).parents[1] / "docs" / "BROWSER_SESSION_LIFECYCLE_CONTRACT.md"


def test_browser_contract_defines_lifecycle_and_allowlist_rules() -> None:
    text = DOC.read_text(encoding="utf-8")
    for value in ("created", "active", "user_takeover", "recovered", "closed"):
        assert f"`{value}`" in text
    assert "hostnames only" in text
    assert "http" in text and "https" in text
    assert "notexample.com" in text


def test_browser_contract_defines_approval_and_audit_requirements() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert "explicit approval record" in text
    assert "session, action, target or domain" in text
    assert "takeover_required" in text
    assert "bounded audit event" in text
    assert "approval request" in text


def test_browser_contract_is_fail_closed_and_secret_safe() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert "fail closed" in text
    assert "does not store passwords or cookies" in text
    assert "authorization headers" in text
    assert "must not be automatically replayed" in text
    assert "does not claim that a real browser runtime" in text
