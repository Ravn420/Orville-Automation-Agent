from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json

from fastapi.testclient import TestClient

from orville_core.api import create_app


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, limit=-1):
        return json.dumps(self.payload).encode("utf-8")


def test_connector_bridge_health_and_approved_invocation_are_audited():
    calls = []

    def fake_urlopen(request, timeout):
        calls.append((request.full_url, request.get_method(), json.loads(request.data.decode("utf-8")) if request.data else None, request.headers.get("Authorization"), timeout))
        if request.get_method() == "GET":
            return FakeResponse({"ok": True, "status": "ready"})
        return FakeResponse({"ok": True, "data": {"id": "result-1"}})

    with TemporaryDirectory() as directory, patch.dict("os.environ", {"ORVILLE_CONNECTOR_BRIDGE_URL": "http://127.0.0.1:9999", "ORVILLE_CONNECTOR_BRIDGE_TOKEN": "bridge-secret"}, clear=False), patch("orville_core.connector_bridge.urlopen", fake_urlopen):
        app = create_app(api_token="orville-token", storage="json", checkpoint_dir=Path(directory) / ".orville")
        client = TestClient(app)
        headers = {"Authorization": "Bearer orville-token"}

        catalog = client.get("/api/v1/connectors", headers=headers)
        assert catalog.status_code == 200
        assert catalog.json()["bridge_configured"] is True
        assert catalog.json()["catalog_count"] == 372
        assert "bridge-secret" not in catalog.text

        health = client.get("/api/v1/connectors/health", headers=headers)
        assert health.status_code == 200
        assert health.json()["status"] == "ready"

        blocked = client.post("/api/v1/connectors/github/invoke", headers=headers, json={"operation": "issues.list", "arguments": {}})
        assert blocked.status_code == 409

        invoked = client.post("/api/v1/connectors/github/invoke", headers=headers, json={"operation": "issues.list", "arguments": {"repo": "orville"}, "approved": True, "run_id": "run-1"})
        assert invoked.status_code == 200
        assert invoked.json()["result"]["data"]["id"] == "result-1"
        assert invoked.json()["audit"]["outcome"] == "completed"
        assert len(calls) == 2
        assert calls[1][3] == "Bearer bridge-secret"
        assert calls[1][2]["connector_uid"] == "github"


def test_connector_invocation_requires_configured_bridge():
    with TemporaryDirectory() as directory, patch.dict("os.environ", {}, clear=True):
        app = create_app(api_token="orville-token", storage="json", checkpoint_dir=Path(directory) / ".orville")
        client = TestClient(app)
        headers = {"Authorization": "Bearer orville-token"}
        response = client.post("/api/v1/connectors/github/invoke", headers=headers, json={"operation": "issues.list", "approved": True})
        assert response.status_code == 503
        assert client.get("/api/v1/connectors/health", headers=headers).json()["status"] == "not_configured"
