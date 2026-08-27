from __future__ import annotations

from pathlib import Path

from orville_core.scheduler import ScheduleStore
from tools.signal_room_checks import check_ui


def test_execution_history_persists_outputs_artifacts_costs_and_approvals(tmp_path: Path) -> None:
    store = ScheduleStore(tmp_path / "history.sqlite3")
    store.create("schedule-1", "workflow-1", 60)
    store.start_execution("schedule-1", execution_id="execution-1")
    result = store.finish_execution(
        "execution-1",
        status="completed",
        outputs={"summary": "done"},
        artifacts=[{"path": "artifacts/report.md", "sha256": "abc"}],
        cost_units=1.25,
        cost_currency="USD",
        connector_actions=[{"connector": "github", "operation": "get_repository", "status": "success"}],
        approvals=[{"step": "publish", "approved": True}],
    )
    assert result.outputs == {"summary": "done"}
    assert result.artifacts[0]["path"] == "artifacts/report.md"
    assert result.cost_units == 1.25
    assert result.cost_currency == "USD"
    assert result.connector_actions[0]["connector"] == "github"
    assert result.approvals[0]["approved"] is True

    reopened = ScheduleStore(tmp_path / "history.sqlite3")
    persisted = reopened.history("schedule-1")[0]
    assert persisted.outputs == {"summary": "done"}
    assert persisted.cost_units == 1.25
    assert persisted.artifacts[0]["sha256"] == "abc"


def test_execution_history_rejects_negative_cost(tmp_path: Path) -> None:
    store = ScheduleStore(tmp_path / "history.sqlite3")
    store.create("schedule-1", "workflow-1", 60)
    store.start_execution("schedule-1", execution_id="execution-1")
    try:
        store.finish_execution("execution-1", status="failed", cost_units=-1)
    except ValueError as exc:
        assert "cost_units" in str(exc)
    else:
        raise AssertionError("negative costs must be rejected")


def test_signal_room_bundle_passes_local_smoke_accessibility_and_contrast_checks() -> None:
    root = Path(__file__).parents[1] / "webui"
    assert check_ui(root) == []


def test_execution_history_api_presents_outputs_artifacts_and_costs(tmp_path: Path) -> None:
    from fastapi.testclient import TestClient
    from orville_core.api import create_app

    app = create_app(checkpoint_dir=tmp_path / "checkpoints", database_path=tmp_path / "api.sqlite3", storage="sqlite", api_token="test-token")
    client = TestClient(app)
    headers = {"Authorization": "Bearer test-token"}
    assert client.post("/api/v1/schedules", json={"schedule_id": "schedule-1", "workflow_id": "workflow-1", "interval_seconds": 60}, headers=headers).status_code == 200
    assert client.post("/api/v1/schedules/schedule-1/executions/start", json={"execution_id": "execution-1"}, headers=headers).status_code == 200
    response = client.post("/api/v1/schedule-executions/execution-1/finish", json={"status": "completed", "outputs": {"answer": "ok"}, "artifacts": [{"path": "report.md"}], "cost_units": 2.5, "cost_currency": "USD"}, headers=headers)
    assert response.status_code == 200
    history = client.get("/api/v1/schedules/schedule-1/history", headers=headers)
    assert history.status_code == 200
    execution = history.json()["executions"][0]
    assert execution["outputs"]["answer"] == "ok"
    assert execution["artifacts"][0]["path"] == "report.md"
    assert execution["cost_units"] == 2.5
