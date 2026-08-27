"""Local-fixture integration coverage for supported external boundaries."""

from __future__ import annotations

import hashlib
import hmac
import io
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

import pytest

from orville_core.automation import AutomationDispatcher, TriggerType, WorkflowExecutor, WorkflowStep, WorkflowStore
from orville_core.browser import BrowserSessionManager
from orville_core.local_models import LocalModelCatalog
from orville_core.scheduler import ScheduleStore
from orville_core.workspace import WorkspaceSession


class FakeResponse:
    def __init__(self, payload: dict[str, object], status: int = 200) -> None:
        self.payload = payload
        self.status = status

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> bool:
        return False

    def read(self, *_args: object) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_filesystem_and_model_boundaries_share_a_local_fixture() -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "source"
        source.mkdir()
        (source / "app.py").write_text("print('safe')\n", encoding="utf-8")
        (source / ".env").write_text("SYNTHETIC_SECRET=not-for-context\n", encoding="utf-8")
        workspace = WorkspaceSession.create(source, workspace_parent=root, workspace_id="integration")
        try:
            assert workspace.list_files() == ["app.py"]
            assert workspace.read_file("app.py") == "print('safe')\n"
            catalog = LocalModelCatalog(root / "catalog.json")
            asset = root / "demo.gguf"
            asset.write_bytes(b"synthetic-model")
            record = catalog.import_model(asset, model_id="local/integration", runtime="ollama", endpoint="http://localhost:11434", provenance={"source": "fixture"})
            assert record.checksum_sha256
            assert catalog.verify_checksum("local/integration")["matches"] is True
        finally:
            workspace.cleanup()


def test_github_connector_boundary_uses_local_stub_and_approval_gate() -> None:
    from fastapi.testclient import TestClient
    from orville_core.api import create_app

    calls: list[tuple[str, str]] = []

    def fake_urlopen(request: object, timeout: float) -> FakeResponse:
        calls.append((request.full_url, request.get_method()))  # type: ignore[attr-defined]
        return FakeResponse({"ok": True, "data": {"id": "fixture-result"}})

    with tempfile.TemporaryDirectory() as directory, patch.dict("os.environ", {"ORVILLE_CONNECTOR_BRIDGE_URL": "http://127.0.0.1:9999", "ORVILLE_CONNECTOR_BRIDGE_TOKEN": "synthetic-bridge-token"}, clear=False), patch("orville_core.connector_bridge.urlopen", fake_urlopen):
        app = create_app(api_token="synthetic-orville-token", storage="json", checkpoint_dir=Path(directory) / ".orville")
        client = TestClient(app)
        headers = {"Authorization": "Bearer synthetic-orville-token"}
        blocked = client.post("/api/v1/connectors/github/invoke", headers=headers, json={"operation": "issues.list", "arguments": {}})
        assert blocked.status_code == 409
        invoked = client.post("/api/v1/connectors/github/invoke", headers=headers, json={"operation": "issues.list", "arguments": {"repo": "fixture"}, "approved": True, "run_id": "integration-run"})
        assert invoked.status_code == 200
        assert invoked.json()["result"]["data"]["id"] == "fixture-result"
        assert invoked.json()["audit"]["outcome"] == "completed"
        assert calls == [("http://127.0.0.1:9999/invoke", "POST")]


def test_browser_boundary_persists_approval_required_recovery() -> None:
    with tempfile.TemporaryDirectory() as directory:
        state_path = Path(directory) / "browser.json"
        manager = BrowserSessionManager(state_path=state_path)
        session = manager.create(["Example.com"], headless=True)
        pending = session.navigate("https://docs.example.com/guide", approved=False)
        assert pending["takeover_required"] is True
        manager.persist()
        recovered = BrowserSessionManager(state_path=state_path).get(session.session_id)
        assert recovered is not None
        assert recovered.status == "recovered"
        assert recovered.takeover_required is True
        assert recovered.current_url is None


def test_scheduling_boundary_dispatches_and_releases_local_lease() -> None:
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "integration.db"
        workflows = WorkflowStore(database)
        schedules = ScheduleStore(database)
        workflow_id = workflows.create_workflow("Scheduled integration")
        version = workflows.add_version(workflow_id, TriggerType.SCHEDULED, (WorkflowStep("echo", "echo", {"value": "done"}),))
        workflows.set_enabled(workflow_id, version.version_id, True)
        schedule = schedules.create("schedule-integration", workflow_id, 60)
        schedules.set_enabled(schedule.schedule_id, True)
        dispatcher = AutomationDispatcher(schedules, workflows, WorkflowExecutor({"echo": lambda payload: {"result": payload["value"]}}))
        run = dispatcher.dispatch_schedule(schedule.schedule_id, {"input": "fixture"}, worker_id="integration-worker")
        assert run.status.value == "completed"
        assert schedules.list()[0].lease_owner is None
        assert workflows.list_runs(workflow_id)[0].status.value == "completed"


def test_model_and_provider_failure_boundaries_remain_safe() -> None:
    from orville_core.providers import JsonHttpClient, ProviderError

    error = HTTPError("https://provider.example.test", 401, "unauthorized", {}, io.BytesIO(b"Bearer sk-live-secret"))
    with patch("orville_core.providers.urlopen", side_effect=error):
        with pytest.raises(ProviderError) as raised:
            JsonHttpClient().request("GET", "https://provider.example.test/health")
    assert "sk-live-secret" not in str(raised.value)


def test_webhook_boundary_rejects_invalid_signature_without_dispatch() -> None:
    from orville_core.scheduler import EventIntake

    secret = "synthetic-signing-secret"
    intake = EventIntake(secret)
    body = b'{"fixture":true}'
    valid = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert intake.accept("fixture-event", "github", "push", {"fixture": True}, signature_body=body, signature=valid).accepted is True
    assert intake.accept("fixture-event-2", "github", "push", {"fixture": True}, signature_body=body, signature="invalid").accepted is False
