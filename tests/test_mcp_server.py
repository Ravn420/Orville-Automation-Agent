from __future__ import annotations

import json

from fastapi.testclient import TestClient

from orville_core.mcp_server import RestClient, create_mcp_app


class FakeRestClient:
    base_url = "http://127.0.0.1:8787"
    token = "synthetic-token"

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict | None, dict | None]] = []

    def request(self, method: str, path: str, query=None, payload=None):
        self.calls.append((method, path, query, payload))
        if path == "/api/v1/health":
            return {"ok": True, "status": "ready"}
        if path == "/api/v1/projects":
            return {"projects": [{"project_id": "p-1"}]}
        if path == "/api/v1/projects/p-1/tasks":
            return {"tasks": []}
        return {"path": path}


def test_initialize_and_list_tools() -> None:
    client = FakeRestClient()
    response = TestClient(create_mcp_app(rest_client=client)).post("/", json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}})
    assert response.status_code == 200
    assert response.json()["result"]["serverInfo"]["name"] == "orville-python-mcp-bridge"

    response = TestClient(create_mcp_app(rest_client=client)).post("/", json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    names = {tool["name"] for tool in response.json()["result"]["tools"]}
    assert "orville_health" in names
    assert "orville_list_projects" in names


def test_tool_call_forwards_to_rest_api() -> None:
    client = FakeRestClient()
    response = TestClient(create_mcp_app(rest_client=client)).post("/mcp", json={"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "orville_list_tasks", "arguments": {"project_id": "p-1", "limit": 25}}})
    assert response.status_code == 200
    assert response.json()["result"]["isError"] is False
    assert client.calls == [("GET", "/api/v1/projects/p-1/tasks", {"limit": 25}, None)]


def test_tool_call_rejects_invalid_project_id() -> None:
    client = FakeRestClient()
    response = TestClient(create_mcp_app(rest_client=client)).post("/", json={"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "orville_get_project", "arguments": {"project_id": ""}}})
    assert response.json()["result"]["isError"] is True
    assert client.calls == []


def test_unknown_method_returns_jsonrpc_error() -> None:
    client = FakeRestClient()
    response = TestClient(create_mcp_app(rest_client=client)).post("/", json={"jsonrpc": "2.0", "id": 5, "method": "unknown", "params": {}})
    assert response.json()["error"]["code"] == -32601


def test_rest_client_requires_token() -> None:
    assert RestClient("http://127.0.0.1:8787", "synthetic-token").token == "synthetic-token"


def test_mutation_requires_global_enablement_and_per_call_approval(monkeypatch) -> None:
    client = FakeRestClient()
    monkeypatch.delenv("ORVILLE_MCP_MUTATIONS_ENABLED", raising=False)
    response = TestClient(create_mcp_app(rest_client=client)).post("/", json={"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "orville_create_project", "arguments": {"name": "blocked", "approved": True}}})
    assert response.json()["result"]["isError"] is True
    assert "disabled" in response.json()["result"]["content"][0]["text"]
    assert client.calls == []

    monkeypatch.setenv("ORVILLE_MCP_MUTATIONS_ENABLED", "1")
    response = TestClient(create_mcp_app(rest_client=client)).post("/", json={"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": "orville_create_project", "arguments": {"name": "blocked", "approved": False}}})
    assert response.json()["result"]["isError"] is True
    assert "approved=true" in response.json()["result"]["content"][0]["text"]
    assert client.calls == []


def test_approved_mutation_forwards_only_allowlisted_fields(monkeypatch) -> None:
    monkeypatch.setenv("ORVILLE_MCP_MUTATIONS_ENABLED", "true")
    client = FakeRestClient()
    response = TestClient(create_mcp_app(rest_client=client)).post("/", json={"jsonrpc": "2.0", "id": 8, "method": "tools/call", "params": {"name": "orville_create_project", "arguments": {"name": "new project", "description": "desc", "owner_id": "local", "environment": "development", "approved": True, "unexpected": "discarded"}}})
    assert response.json()["result"]["isError"] is False
    assert client.calls == [("POST", "/api/v1/projects", None, {"name": "new project", "description": "desc", "owner_id": "local", "environment": "development"})]


def test_approved_task_mutation_preserves_long_request(monkeypatch) -> None:
    monkeypatch.setenv("ORVILLE_MCP_MUTATIONS_ENABLED", "1")
    client = FakeRestClient()
    request_text = "x" * 500
    response = TestClient(create_mcp_app(rest_client=client)).post("/", json={"jsonrpc": "2.0", "id": 9, "method": "tools/call", "params": {"name": "orville_create_task", "arguments": {"project_id": "p/1", "request": request_text, "approved": True}}})
    assert response.json()["result"]["isError"] is False
    assert client.calls[0][1] == "/api/v1/projects/p%2F1/tasks"
    assert client.calls[0][3]["request"] == request_text
