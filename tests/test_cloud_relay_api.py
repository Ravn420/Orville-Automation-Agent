import os
import tempfile
from pathlib import Path

import pytest

try:
    from fastapi.testclient import TestClient
    from orville_core.api import create_app
    from orville_core.connector_connections import ConnectorConnectionStore
    from credential_test_support import protect, unprotect
except ImportError:  # pragma: no cover
    TestClient = None
    create_app = None
    ConnectorConnectionStore = None


pytestmark = pytest.mark.skipif(TestClient is None, reason="FastAPI API extras are not installed")


def _test_connection_store(directory: str) -> ConnectorConnectionStore:
    return ConnectorConnectionStore(Path(directory) / "connector-connections.json", protect=protect, unprotect=unprotect)


def test_cloud_status_reports_managed_and_user_access_separately(monkeypatch):
    with tempfile.TemporaryDirectory() as directory:
        monkeypatch.setenv("ORVILLE_BLACKBOX_RELAY_URL", "https://relay.example.test/v1")
        monkeypatch.setenv("ORVILLE_BLACKBOX_RELAY_ALLOWED_HOSTS", "relay.example.test")
        client = TestClient(create_app(checkpoint_dir=Path(directory), api_token="secret"))
        headers = {"Authorization": "Bearer secret"}
        response = client.get("/api/v1/cloud/blackbox/status", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["managed"]["status"] == "ready"
        assert body["user_connected"]["status"] == "not_connected"
        assert body["credential_in_client"] is False
        assert body["relay"]["credential_configured"] is False


def test_cloud_admission_requires_explicit_remote_approval_for_restricted_data(monkeypatch):
    with tempfile.TemporaryDirectory() as directory:
        monkeypatch.setenv("ORVILLE_BLACKBOX_RELAY_URL", "https://relay.example.test/v1")
        monkeypatch.setenv("ORVILLE_BLACKBOX_RELAY_ALLOWED_HOSTS", "relay.example.test")
        client = TestClient(create_app(checkpoint_dir=Path(directory), api_token="secret"))
        headers = {"Authorization": "Bearer secret"}
        blocked = client.post("/api/v1/cloud/blackbox/admit", headers=headers, json={"subject": "local-device", "privacy_class": "restricted"})
        assert blocked.status_code == 409
        allowed = client.post("/api/v1/cloud/blackbox/admit", headers=headers, json={"subject": "local-device", "privacy_class": "cloud_approved"})
        assert allowed.status_code == 200
        admission = allowed.json()["admission"]
        assert admission["provider_credential_in_client"] is False
        assert admission["provider"] == "blackbox"
        assert admission["model"] == "blackboxai/openai/gpt-5.5"
        assert admission["endpoint_family"] == "standard"
        assert admission["privacy_mode"] == "cloud_approved"
        assert admission["execution_location"] == "remote"


def test_cloud_admission_returns_unavailable_when_relay_not_configured(monkeypatch):
    with tempfile.TemporaryDirectory() as directory:
        monkeypatch.delenv("ORVILLE_BLACKBOX_RELAY_URL", raising=False)
        client = TestClient(create_app(checkpoint_dir=Path(directory), api_token="secret"))
        headers = {"Authorization": "Bearer secret"}
        response = client.post("/api/v1/cloud/blackbox/admit", headers=headers, json={"subject": "local-device"})
        assert response.status_code == 503


def test_user_blackbox_api_key_connection_is_redacted_and_disconnectable(monkeypatch):
    with tempfile.TemporaryDirectory() as directory:
        monkeypatch.setenv("ORVILLE_BLACKBOX_RELAY_URL", "https://relay.example.test/v1")
        monkeypatch.setenv("ORVILLE_BLACKBOX_RELAY_ALLOWED_HOSTS", "relay.example.test")
        client = TestClient(create_app(checkpoint_dir=Path(directory), api_token="secret", connector_connection_store=_test_connection_store(directory)))
        headers = {"Authorization": "Bearer secret"}
        connected = client.post("/api/v1/cloud/blackbox/user/api-key", headers=headers, json={"api_key": "sk-test-secret"})
        assert connected.status_code == 200
        body = connected.json()
        assert body["credential_returned"] is False
        assert "sk-test-secret" not in str(body)
        assert body["connection"]["has_credential"] is True
        for persisted in Path(directory).rglob("*"):
            if persisted.is_file():
                assert "sk-test-secret" not in persisted.read_bytes().decode("utf-8", errors="ignore")
        disconnected = client.post("/api/v1/cloud/blackbox/user/disconnect", headers=headers)
        assert disconnected.status_code == 200
        assert disconnected.json()["managed_access_unchanged"] is True
        assert disconnected.json()["local_mode_unchanged"] is True
        assert disconnected.json()["unrelated_task_state_unchanged"] is True


def test_user_blackbox_api_key_test_and_credential_delete_are_safe(monkeypatch):
    with tempfile.TemporaryDirectory() as directory:
        monkeypatch.setenv("ORVILLE_BLACKBOX_RELAY_URL", "https://relay.example.test/v1")
        monkeypatch.setenv("ORVILLE_BLACKBOX_RELAY_ALLOWED_HOSTS", "relay.example.test")
        client = TestClient(create_app(checkpoint_dir=Path(directory), api_token="secret", connector_connection_store=_test_connection_store(directory)))
        headers = {"Authorization": "Bearer secret"}
        tested = client.post(
            "/api/v1/cloud/blackbox/user/test",
            headers=headers,
            json={"api_key": "sk-test-secret", "base_url": "https://api.blackbox.ai", "model": "blackboxai/openai/gpt-5.5"},
        )
        assert tested.status_code == 200
        assert tested.json()["tested"] is True
        assert tested.json()["network_call_performed"] is False
        assert "sk-test-secret" not in tested.text

        connected = client.post("/api/v1/cloud/blackbox/user/api-key", headers=headers, json={"api_key": "sk-test-secret"})
        assert connected.status_code == 200
        deleted = client.delete("/api/v1/cloud/blackbox/user/credential", headers=headers)
        assert deleted.status_code == 200
        assert deleted.json() == {
            "provider": "blackbox",
            "credential_deleted": True,
            "managed_access_unchanged": True,
            "local_mode_unchanged": True,
        }
