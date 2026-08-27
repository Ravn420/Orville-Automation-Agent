from orville_core import RuntimeHealth


def test_runtime_health_reports_required_and_optional_checks(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda command: "C:/bin/" + command)
    monkeypatch.setattr(RuntimeHealth, "_command_version", staticmethod(lambda command: command + " 1.0"))
    report = RuntimeHealth(required_commands=("python",), optional_commands=("manus-mcp-cli",), optional_modules=()).run()
    assert report["status"] == "ok"
    assert report["checks"][0]["version"] == "python 1.0"
    assert report["checks"][1]["detail"].startswith("optional MCP")


def test_runtime_health_degrades_when_required_command_missing(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda command: None)
    report = RuntimeHealth(required_commands=("git",), optional_commands=(), optional_modules=()).run()
    assert report["status"] == "degraded"
    assert report["checks"][0]["available"] is False


def test_runtime_health_does_not_include_environment_secrets(monkeypatch):
    monkeypatch.setenv("BLACKBOX_API_KEY", "must-not-appear")
    monkeypatch.setattr("shutil.which", lambda command: None)
    report = RuntimeHealth(required_commands=(), optional_commands=(), optional_modules=()).run()
    assert "BLACKBOX_API_KEY" not in str(report)
    assert "must-not-appear" not in str(report)
