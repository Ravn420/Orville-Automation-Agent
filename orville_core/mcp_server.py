"""Local MCP bridge for the authenticated Orville REST API.

The bridge exposes a deliberately read-only MCP tool surface over the local
REST API. It keeps the REST bearer token server-side, validates resource IDs,
limits response sizes, and binds to localhost by default.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from fastapi import FastAPI, Request as FastAPIRequest
from fastapi.responses import JSONResponse, Response


JSONRPC_VERSION = "2.0"
DEFAULT_REST_URL = "http://127.0.0.1:8787"
DEFAULT_MCP_HOST = "127.0.0.1"
DEFAULT_MCP_PORT = 42069
MAX_RESPONSE_BYTES = 2_000_000
MAX_ARGUMENT_BYTES = 100_000
MUTATION_TOOLS_ENABLED_ENV = "ORVILLE_MCP_MUTATIONS_ENABLED"



class McpBridgeError(RuntimeError):
    """Raised when a REST-to-MCP operation cannot be completed safely."""


@dataclass(frozen=True)
class RestClient:
    """Bounded authenticated client for the local Orville REST API."""

    base_url: str
    token: str
    timeout_seconds: float = 10.0
    max_response_bytes: int = MAX_RESPONSE_BYTES

    def request(self, method: str, path: str, query: dict[str, Any] | None = None, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        if query:
            url = f"{url}?{urlencode({key: value for key, value in query.items() if value is not None})}"
        body = None
        headers = {"Accept": "application/json", "Authorization": f"Bearer {self.token}", "User-Agent": "Orville-MCP-Bridge/1"}
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            if len(body) > MAX_ARGUMENT_BYTES:
                raise McpBridgeError("REST request payload exceeds the safety limit")
            headers["Content-Type"] = "application/json"
        request = Request(url, data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read(self.max_response_bytes + 1)
        except HTTPError as exc:
            detail = exc.read(512).decode("utf-8", "replace")
            raise McpBridgeError(f"REST API returned HTTP {exc.code}: {detail[:240]}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise McpBridgeError(f"REST API unavailable: {type(exc).__name__}") from exc
        if len(raw) > self.max_response_bytes:
            raise McpBridgeError("REST API response exceeds the safety limit")
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise McpBridgeError("REST API returned invalid JSON") from exc
        if not isinstance(value, dict):
            raise McpBridgeError("REST API response must be a JSON object")
        return value


def _required_string(arguments: dict[str, Any], name: str) -> str:
    value = arguments.get(name)
    if not isinstance(value, str) or not value.strip() or len(value) > 240:
        raise McpBridgeError(f"argument '{name}' must be a non-empty string of at most 240 characters")
    return value.strip()


def _required_text(arguments: dict[str, Any], name: str, maximum: int = 100_000) -> str:
    value = arguments.get(name)
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise McpBridgeError(f"argument '{name}' must be a non-empty string of at most {maximum} characters")
    return value.strip()


def _mutation_approved(arguments: dict[str, Any]) -> None:
    """Require both bridge-level enablement and explicit per-call approval."""
    enabled = os.getenv(MUTATION_TOOLS_ENABLED_ENV, "0").strip().lower() in {"1", "true", "yes", "on"}
    if not enabled:
        raise McpBridgeError(f"mutation tools are disabled; set {MUTATION_TOOLS_ENABLED_ENV}=1 before starting the bridge")
    if arguments.get("approved") is not True:
        raise McpBridgeError("mutation requires explicit approved=true in the tool arguments")


def _bounded_limit(arguments: dict[str, Any], default: int = 100) -> int:
    value = arguments.get("limit", default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise McpBridgeError("argument 'limit' must be an integer")
    return max(1, min(value, 200))


def _tools() -> list[dict[str, Any]]:
    return [
        {"name": "orville_health", "description": "Read the authenticated health status of the local Orville REST API.", "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
        {"name": "orville_state", "description": "Read the redacted current Orville project execution state.", "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
        {"name": "orville_capabilities", "description": "Read the local Orville capability and adapter status.", "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
        {"name": "orville_list_projects", "description": "List projects visible to the authenticated local Orville API.", "inputSchema": {"type": "object", "properties": {"owner_id": {"type": "string", "maxLength": 200}}, "additionalProperties": False}},
        {"name": "orville_get_project", "description": "Read one Orville project by project ID.", "inputSchema": {"type": "object", "properties": {"project_id": {"type": "string", "minLength": 1, "maxLength": 240}}, "required": ["project_id"], "additionalProperties": False}},
        {"name": "orville_list_tasks", "description": "List tasks for an Orville project.", "inputSchema": {"type": "object", "properties": {"project_id": {"type": "string", "minLength": 1, "maxLength": 240}, "limit": {"type": "integer", "minimum": 1, "maximum": 200}}, "required": ["project_id"], "additionalProperties": False}},
        {"name": "orville_project_memory", "description": "Read project memory from Orville without exposing credentials.", "inputSchema": {"type": "object", "properties": {"project_id": {"type": "string", "minLength": 1, "maxLength": 240}}, "required": ["project_id"], "additionalProperties": False}},
        {"name": "orville_project_instructions", "description": "Read durable project instructions from Orville.", "inputSchema": {"type": "object", "properties": {"project_id": {"type": "string", "minLength": 1, "maxLength": 240}}, "required": ["project_id"], "additionalProperties": False}},
        {"name": "orville_list_connectors", "description": "Read the redacted connector catalog and local connection status.", "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
        {"name": "orville_personal_agent", "description": "Read the local personal-agent profile and status.", "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
        {"name": "orville_create_project", "description": "Create a project in Orville. Requires bridge mutation enablement and approved=true.", "inputSchema": {"type": "object", "properties": {"name": {"type": "string", "minLength": 1, "maxLength": 240}, "description": {"type": "string", "maxLength": 2000}, "owner_id": {"type": "string", "maxLength": 200}, "environment": {"type": "string", "maxLength": 40}, "approved": {"type": "boolean"}}, "required": ["name", "approved"], "additionalProperties": False}},
        {"name": "orville_create_task", "description": "Create a project task in Orville. Requires bridge mutation enablement and approved=true.", "inputSchema": {"type": "object", "properties": {"project_id": {"type": "string", "minLength": 1, "maxLength": 240}, "request": {"type": "string", "minLength": 1, "maxLength": 100000}, "mode": {"type": "string", "maxLength": 40}, "provider_id": {"type": ["string", "null"], "maxLength": 120}, "budget": {"type": "object"}, "tool_permissions": {"type": "array", "items": {"type": "string"}}, "approved": {"type": "boolean"}}, "required": ["project_id", "request", "approved"], "additionalProperties": False}},
        {"name": "orville_save_project_memory", "description": "Save project memory in Orville. Requires bridge mutation enablement and approved=true.", "inputSchema": {"type": "object", "properties": {"project_id": {"type": "string", "minLength": 1, "maxLength": 240}, "key": {"type": "string", "minLength": 1, "maxLength": 240}, "value": {"type": "string", "maxLength": 20000}, "source": {"type": "string", "maxLength": 80}, "approved": {"type": "boolean"}}, "required": ["project_id", "key", "value", "approved"], "additionalProperties": False}},
        {"name": "orville_update_personal_agent", "description": "Update the local personal-agent profile. Requires bridge mutation enablement and approved=true.", "inputSchema": {"type": "object", "properties": {"name": {"type": "string", "maxLength": 200}, "enabled": {"type": "boolean"}, "memory_enabled": {"type": "boolean"}, "approved": {"type": "boolean"}}, "required": ["approved"], "additionalProperties": False}},
    ]


def create_mcp_app(*, rest_client: RestClient | None = None) -> FastAPI:
    """Create the local JSON-RPC MCP application without starting a process."""
    token = os.getenv("ORVILLE_API_TOKEN", "")
    client = rest_client or RestClient(os.getenv("ORVILLE_REST_URL", DEFAULT_REST_URL).rstrip("/"), token)
    if not client.token:
        raise RuntimeError("ORVILLE_API_TOKEN is required for the MCP bridge")
    app = FastAPI(title="Orville Python MCP Bridge", version="0.1.0", docs_url=None, redoc_url=None)

    def rpc_result(request_id: Any, result: dict[str, Any]) -> JSONResponse:
        return JSONResponse({"jsonrpc": JSONRPC_VERSION, "id": request_id, "result": result})

    def rpc_error(request_id: Any, code: int, message: str) -> JSONResponse:
        return JSONResponse({"jsonrpc": JSONRPC_VERSION, "id": request_id, "error": {"code": code, "message": message}})

    def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "orville_health":
            value = client.request("GET", "/api/v1/health")
        elif name == "orville_state":
            value = client.request("GET", "/api/v1/state")
        elif name == "orville_capabilities":
            value = client.request("GET", "/api/v1/capabilities")
        elif name == "orville_list_projects":
            value = client.request("GET", "/api/v1/projects", query={"owner_id": arguments.get("owner_id")})
        elif name == "orville_get_project":
            value = client.request("GET", f"/api/v1/projects/{quote(_required_string(arguments, 'project_id'), safe='')}")
        elif name == "orville_list_tasks":
            project_id = quote(_required_string(arguments, "project_id"), safe="")
            value = client.request("GET", f"/api/v1/projects/{project_id}/tasks", query={"limit": _bounded_limit(arguments)})
        elif name == "orville_project_memory":
            value = client.request("GET", f"/api/v1/projects/{quote(_required_string(arguments, 'project_id'), safe='')}/memory")
        elif name == "orville_project_instructions":
            value = client.request("GET", f"/api/v1/projects/{quote(_required_string(arguments, 'project_id'), safe='')}/instructions")
        elif name == "orville_list_connectors":
            value = client.request("GET", "/api/v1/connectors")
        elif name == "orville_personal_agent":
            value = client.request("GET", "/api/v1/personal-agent")
        elif name == "orville_create_project":
            _mutation_approved(arguments)
            value = client.request("POST", "/api/v1/projects", payload={"name": _required_string(arguments, "name"), "description": str(arguments.get("description", ""))[:2000], "owner_id": str(arguments.get("owner_id", "local"))[:200], "environment": str(arguments.get("environment", "development"))[:40]})
        elif name == "orville_create_task":
            _mutation_approved(arguments)
            project_id = quote(_required_string(arguments, "project_id"), safe="")
            value = client.request("POST", f"/api/v1/projects/{project_id}/tasks", payload={"request": _required_text(arguments, "request"), "mode": str(arguments.get("mode", "general"))[:40], "provider_id": arguments.get("provider_id"), "budget": arguments.get("budget", {}), "tool_permissions": arguments.get("tool_permissions", [])})
        elif name == "orville_save_project_memory":
            _mutation_approved(arguments)
            project_id = quote(_required_string(arguments, "project_id"), safe="")
            value = client.request("POST", f"/api/v1/projects/{project_id}/memory", payload={"key": _required_string(arguments, "key"), "value": str(arguments.get("value", ""))[:20000], "source": str(arguments.get("source", "user"))[:80]})
        elif name == "orville_update_personal_agent":
            _mutation_approved(arguments)
            value = client.request("POST", "/api/v1/personal-agent", payload={key: arguments[key] for key in ("name", "enabled", "memory_enabled") if key in arguments})
        else:
            raise McpBridgeError(f"unknown tool: {name}")
        return {"content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False, sort_keys=True)}], "structuredContent": value, "isError": False}

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {"ok": True, "service": "orville-python-mcp-bridge", "rest_url": client.base_url}

    @app.post("/")
    @app.post("/mcp")
    async def handle_rpc(request: FastAPIRequest) -> Response:
        try:
            payload = await request.json()
        except Exception:
            return rpc_error(None, -32700, "invalid JSON")
        if not isinstance(payload, dict):
            return rpc_error(None, -32600, "request must be a JSON object")
        request_id = payload.get("id")
        method = payload.get("method")
        params = payload.get("params") or {}
        if not isinstance(method, str) or not isinstance(params, dict):
            return rpc_error(request_id, -32600, "invalid JSON-RPC request")
        if method == "notifications/initialized":
            return Response(status_code=202)
        if method == "initialize":
            requested = params.get("protocolVersion")
            protocol_version = requested if isinstance(requested, str) and requested else "2025-06-18"
            return rpc_result(request_id, {"protocolVersion": protocol_version, "capabilities": {"tools": {"listChanged": False}}, "serverInfo": {"name": "orville-python-mcp-bridge", "version": "0.1.0"}, "instructions": "MCP bridge to the authenticated local Orville REST API. Read-only tools are always available; mutation tools require ORVILLE_MCP_MUTATIONS_ENABLED=1 and approved=true per call."})
        if method == "tools/list":
            return rpc_result(request_id, {"tools": _tools()})
        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or {}
            if not isinstance(name, str) or not isinstance(arguments, dict):
                return rpc_error(request_id, -32602, "tools/call requires a tool name and object arguments")
            try:
                if len(json.dumps(arguments, ensure_ascii=False)) > MAX_ARGUMENT_BYTES:
                    raise McpBridgeError("tool arguments exceed the safety limit")
                return rpc_result(request_id, call_tool(name, arguments))
            except McpBridgeError as exc:
                return rpc_result(request_id, {"content": [{"type": "text", "text": str(exc)}], "isError": True})
        return rpc_error(request_id, -32601, f"method not found: {method}")

    return app


def main() -> None:
    """Start the MCP bridge using environment-configured localhost settings."""
    import uvicorn

    host = os.getenv("ORVILLE_MCP_HOST", DEFAULT_MCP_HOST)
    port = int(os.getenv("ORVILLE_MCP_PORT", str(DEFAULT_MCP_PORT)))
    uvicorn.run(create_mcp_app(), host=host, port=port, log_level=os.getenv("ORVILLE_MCP_LOG_LEVEL", "info"))


if __name__ == "__main__":
    main()
