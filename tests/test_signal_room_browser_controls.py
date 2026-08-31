from pathlib import Path


GUI = Path(__file__).parents[1] / "windows_gui.py"


def test_signal_room_adds_browser_controls_without_removing_existing_menus() -> None:
    text = GUI.read_text(encoding="utf-8")
    for label in ("New Task", "Personal Agent", "Projects", "Task history", "Overview", "Active tasks", "Verification", "Artifacts", "Integrations", "Settings", "Import model", "Model manager", "Provider setup"):
        assert label in text
    assert '"  Browser controls"' in text
    assert "open_browser_controls" in text


def test_browser_controls_default_to_read_only_and_require_approval() -> None:
    text = GUI.read_text(encoding="utf-8")
    assert "Read-only by default" in text
    assert '"read_only": True' in text
    assert '"approved": True' in text
    assert "Approval is a separate action" in text
    assert "/api/v1/browser/sessions" in text


def test_takeover_prompt_explains_user_control_and_security_limits() -> None:
    text = GUI.read_text(encoding="utf-8")
    assert "Request browser takeover" in text
    assert "does not bypass login, CAPTCHA, or the domain allowlist" in text
    assert "/takeover" in text
    assert "/audit" in text
