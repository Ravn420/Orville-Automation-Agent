from __future__ import annotations

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from orville_core.api import create_app
from orville_core.connector_connections import ConnectorConnectionError, ConnectorConnectionStore


class FixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path == "/operations":
            body = json.dumps({"operations": ["files.list", "files.read"]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length))
        body = json.dumps({"ok": True, "operation": payload["operation"]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return


def fixture_server():
    server = HTTPServer(("127.0.0.1", 0), FixtureHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_port}"


def _configure_portable_master_key(monkeypatch) -> None:
    monkeypatch.setenv("ORVILLE_CONNECTOR_MASTER_KEY", Fernet.generate_key().decode("ascii"))


def test_manual_connection_is_redacted_and_persists_with_protected_storage(monkeypatch):
    _configure_portable_master_key(monkeypatch)
    with TemporaryDirectory() as directory:
        path = Path(directory) / "connections.json"
        store = ConnectorConnectionStore(path)
        record = store.connect_manual(uid="fixture", display_name="Fixture", auth_type="bearer", credential_header="Authorization", base_url="http://127.0.0.1:9000", credential="secret-token", scopes=["read"], allow_local=True)
        assert record["status"] == "connected"
        assert record["has_credential"] is True
        assert "secret-token" not in json.dumps(record)
        assert "secret-token" not in path.read_text(encoding="utf-8")
        reloaded = ConnectorConnectionStore(path)
        _, credential = reloaded.credential("fixture")
        assert credential == "secret-token"


def test_non_windows_connection_requires_runtime_master_key(monkeypatch):
    if os.name == "nt":
        pytest.skip("Windows uses DPAPI rather than the portable runtime master key")
    monkeypatch.delenv("ORVILLE_CONNECTOR_MASTER_KEY", raising=False)
    with TemporaryDirectory() as directory:
        store = ConnectorConnectionStore(Path(directory) / "connections.json")
        with pytest.raises(ConnectorConnectionError, match="ORVILLE_CONNECTOR_MASTER_KEY"):
            store.connect_manual(uid="fixture", display_name="Fixture", auth_type="bearer", credential_header="Authorization", base_url="https://example.test", credential="secret-token", scopes=["read"])


def test_api_manual_connection_operation_discovery_invocation_and_disconnect(monkeypatch):
    _configure_portable_master_key(monkeypatch)
    server, base_url = fixture_server()
    try:
        with TemporaryDirectory() as directory:
            app = create_app(api_token="test-token", storage="json", checkpoint_dir=Path(directory) / ".orville")
            client = TestClient(app)
            headers = {"Authorization": "Bearer test-token"}
            connected = client.post("/api/v1/connectors/fixture/connect/manual", headers=headers, json={"project_requirement": "connector fixture contract test", "approved": True, "approval_reference": "test-approval-1", "display_name": "Fixture", "auth_type": "bearer", "credential_header": "Authorization", "base_url": base_url, "credential": "secret-token", "scopes": ["read"], "allow_local": True})
            assert connected.status_code == 200
            assert "secret-token" not in connected.text
            listed = client.get("/api/v1/connector-connections", headers=headers)
            assert listed.status_code == 200
            assert listed.json()["connections"][0]["status"] == "connected"
            operations = client.get("/api/v1/connectors/fixture/operations", headers=headers)
            assert operations.status_code == 200
            assert operations.json()["operations"] == ["files.list", "files.read"]
            blocked = client.post("/api/v1/connectors/fixture/invoke", headers=headers, json={"operation": "files.list", "arguments": {}})
            assert blocked.status_code == 409
            invoked = client.post("/api/v1/connectors/fixture/invoke", headers=headers, json={"operation": "files.list", "arguments": {}, "approved": True})
            assert invoked.status_code == 200
            assert invoked.json()["result"]["ok"] is True
            assert "secret-token" not in invoked.text
            disconnected = client.post("/api/v1/connectors/fixture/disconnect", headers=headers, json={"project_requirement": "connector fixture contract test", "approved": True, "approval_reference": "test-approval-1"})
            assert disconnected.status_code == 200
            assert disconnected.json()["disconnected"] is True
    finally:
        server.shutdown()
        server.server_close()
