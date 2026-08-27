import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from orville_core.api import create_app


def test_startup_main_workflow_and_expected_failures():
    with tempfile.TemporaryDirectory() as directory:
        client = TestClient(create_app(checkpoint_dir=Path(directory), api_token="smoke-token"))
        assert client.get("/api/v1/health").status_code == 401
        headers = {"Authorization": "Bearer smoke-token"}
        health = client.get("/api/v1/health", headers=headers)
        assert health.status_code == 200
        objective = client.post("/api/v1/objectives", headers=headers, json={"objective": "Smoke-test a local Orville workflow", "deliverables": ["test result"]})
        assert objective.status_code == 200
        assert objective.json()["run_id"]
        invalid = client.post("/api/v1/objectives", headers=headers, json={"objective": ""})
        assert invalid.status_code == 422
        cloud_status = client.get("/api/v1/cloud/blackbox/status", headers=headers)
        assert cloud_status.status_code == 200
        assert cloud_status.json()["user_connected"]["status"] == "not_connected"
