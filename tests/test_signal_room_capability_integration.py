from pathlib import Path


GUI = Path(__file__).parents[1] / "windows_gui.py"


def test_signal_room_preserves_existing_navigation() -> None:
    text = GUI.read_text(encoding="utf-8")
    for label in ("New Task", "Personal Agent", "Projects", "Task history", "Overview", "Active tasks", "Verification", "Artifacts", "Integrations", "Settings", "Import model", "Model manager", "Provider setup"):
        assert label in text


def test_signal_room_exposes_additive_operations_navigation() -> None:
    text = GUI.read_text(encoding="utf-8")
    for label, handler in (
        ("Connectors", "open_connectors"),
        ("Schedules", "open_schedules"),
        ("Notifications", "open_notifications"),
        ("Observability", "open_observability"),
        ("Deployment helpers", "open_deployment_helpers"),
    ):
        assert f'"  {label}"' in text
        assert f"self.{handler}" in text


def test_operations_views_are_local_and_approval_safe() -> None:
    text = GUI.read_text(encoding="utf-8")
    assert '"/api/v1/capabilities"' in text
    assert "without invoking an external side effect" in text
    assert "explicitly approved" in text
    assert "OTLP export is optional" in text
