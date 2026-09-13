"""Fixture-based integration tests for priority provider connector manifests.

Tests validate the priority provider manifests (GitHub, Slack, Notion, Google services,
Microsoft Outlook, Stripe, HubSpot, n8n) using mock HTTP servers and synthetic credentials.
No real external services are contacted per security rules.
"""
from __future__ import annotations

import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Iterator
from urllib.error import HTTPError

import pytest

from orville_core.connector_adapters import (
    AdapterResult,
    ConnectorAdapterRegistry,
    ConnectorManifest,
    GenericHttpAdapter,
    OperationSpec,
    priority_manifests,
    provider_default_headers,
)
from orville_core.connector_capability import ConnectorCapabilityAudit


class _PriorityProviderHandler(BaseHTTPRequestHandler):
    """Mock HTTP handler that simulates priority provider API responses."""

    protocol_version = "HTTP/1.1"

    def _write_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        # GitHub repository read
        if self.path.startswith("/repos/"):
            self._write_json(200, {"id": 12345, "name": "orville", "full_name": "test/orville", "private": False})
            return
        # Slack channels list
        if self.path == "/conversations.list":
            self._write_json(200, {"ok": True, "channels": [{"id": "C123", "name": "general"}]})
            return
        # Gmail messages list
        if self.path.startswith("/gmail/v1/users/me/messages"):
            self._write_json(200, {"messages": [{"id": "msg1", "threadId": "thread1"}], "resultSizeEstimate": 1})
            return
        # Google Calendar events list
        if self.path.startswith("/calendar/v3/calendars/primary/events"):
            self._write_json(200, {"items": [{"id": "evt1", "summary": "Team meeting"}]})
            return
        # Outlook messages list
        if self.path.startswith("/v1.0/me/messages"):
            self._write_json(200, {"value": [{"id": "msg1", "subject": "Test"}]})
            return
        # Stripe customers list
        if self.path.startswith("/v1/customers"):
            self._write_json(200, {"data": [{"id": "cus_123", "email": "test@example.com"}], "object": "list"})
            return
        # HubSpot contacts list
        if self.path.startswith("/crm/v3/objects/contacts"):
            self._write_json(200, {"results": [{"id": "1", "properties": {"email": "test@example.com"}}]})
            return
        # n8n workflows list
        if self.path.startswith("/api/v1/workflows"):
            self._write_json(200, {"data": [{"id": "1", "name": "Test Workflow"}]})
            return
        self._write_json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        # Notion search
        if self.path == "/v1/search":
            length = int(self.headers.get("Content-Length", "0"))
            self.rfile.read(length)
            self._write_json(200, {"results": [{"object": "page", "id": "page1"}]})
            return
        # GitHub issue creation (sensitive - should require approval)
        if self.path.startswith("/repos/") and "/issues" in self.path:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            self._write_json(201, {"id": 67890, "title": body.get("title", "Test"), "state": "open"})
            return
        # Slack message send (sensitive)
        if self.path == "/chat.postMessage":
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            self._write_json(200, {"ok": True, "ts": "1234567890.123456", "channel": body.get("channel")})
            return
        # Notion page update (sensitive)
        if self.path.startswith("/v1/pages/"):
            length = int(self.headers.get("Content-Length", "0"))
            self.rfile.read(length)
            self._write_json(200, {"object": "page", "id": "page1"})
            return
        # Gmail send (critical - should require approval)
        if self.path.startswith("/gmail/v1/users/me/messages/send"):
            length = int(self.headers.get("Content-Length", "0"))
            self.rfile.read(length)
            self._write_json(200, {"id": "msg2", "threadId": "thread2"})
            return
        # Google Calendar event creation (sensitive)
        if self.path.startswith("/calendar/v3/calendars/primary/events"):
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            self._write_json(200, {"id": "evt2", "summary": body.get("summary", "Test")})
            return
        # Outlook send (critical)
        if self.path.startswith("/v1.0/me/sendMail"):
            length = int(self.headers.get("Content-Length", "0"))
            self.rfile.read(length)
            self._write_json(202, {})
            return
        # Stripe payment creation (critical)
        if self.path.startswith("/v1/payment_intents"):
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            self._write_json(200, {"id": "pi_123", "amount": body.get("amount", 0), "status": "requires_payment_method"})
            return
        # HubSpot contact creation (sensitive)
        if self.path.startswith("/crm/v3/objects/contacts"):
            length = int(self.headers.get("Content-Length", "0"))
            self.rfile.read(length)
            self._write_json(201, {"id": "2", "properties": {"email": "new@example.com"}})
            return
        # n8n workflow execution (critical)
        if self.path.startswith("/api/v1/workflows/") and "/run" in self.path:
            length = int(self.headers.get("Content-Length", "0"))
            self.rfile.read(length)
            self._write_json(200, {"data": {"executionId": "exec1", "finished": True}})
            return
        self._write_json(404, {"error": "not_found"})

    def do_PATCH(self) -> None:  # noqa: N802
        if self.path.startswith("/v1/pages/"):
            length = int(self.headers.get("Content-Length", "0"))
            self.rfile.read(length)
            self._write_json(200, {"object": "page", "id": "page1"})
            return
        self._write_json(404, {"error": "not_found"})

    def log_message(self, *_args) -> None:
        return


@contextmanager
def _priority_provider_mock_server() -> Iterator[str]:
    """Run an isolated mock server for priority provider testing."""
    server = HTTPServer(("127.0.0.1", 0), _PriorityProviderHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_priority_manifests_contain_all_expected_providers():
    """Validate that priority manifests include the 9 key providers."""
    manifests = priority_manifests()
    assert len(manifests) == 9
    connector_ids = {m.connector_id for m in manifests}
    expected_ids = {"github", "slack", "notion", "google-gmail", "google-calendar", "microsoft-outlook", "stripe", "hubspot", "n8n"}
    assert expected_ids == connector_ids


def test_priority_manifests_have_proper_risk_classification():
    """Ensure critical operations are properly marked for approval."""
    manifests = priority_manifests()
    for manifest in manifests:
        for operation in manifest.operations:
            assert operation.risk_class in {"read", "write", "sensitive", "critical"}
            # Email sending and payment operations should be critical
            if "send" in operation.operation_id.lower() and "message" in operation.operation_id.lower():
                assert operation.risk_class in {"sensitive", "critical"}
            if "payment" in operation.operation_id.lower():
                assert operation.risk_class == "critical"


def test_github_read_operation_with_mock_server():
    """Test GitHub repository read operation with mock server."""
    with _priority_provider_mock_server() as base_url:
        registry = ConnectorAdapterRegistry()
        github_manifest = next(m for m in priority_manifests() if m.connector_id == "github")
        
        def handler(operation: OperationSpec, arguments: dict) -> AdapterResult:
            adapter = GenericHttpAdapter(
                base_url,
                provider_default_headers("github"),
                allowed_hosts={"127.0.0.1"},
                allow_private=True,
            )
            return adapter(operation, arguments)
        
        registry.register(github_manifest, handler)
        result = registry.invoke("github", "get_repository", {"owner": "test", "repo": "orville"}, approved=False)
        assert result.success is True
        assert result.data["name"] == "orville"
        assert result.status_code == 200


def test_sensitive_operation_requires_approval_github():
    """Test that GitHub issue creation requires explicit approval."""
    with _priority_provider_mock_server() as base_url:
        registry = ConnectorAdapterRegistry()
        github_manifest = next(m for m in priority_manifests() if m.connector_id == "github")
        
        def handler(operation: OperationSpec, arguments: dict) -> AdapterResult:
            adapter = GenericHttpAdapter(
                base_url,
                provider_default_headers("github"),
                allowed_hosts={"127.0.0.1"},
                allow_private=True,
            )
            return adapter(operation, arguments)
        
        registry.register(github_manifest, handler)
        with pytest.raises(PermissionError, match="explicit approval"):
            registry.invoke("github", "create_issue", {"owner": "test", "repo": "orville", "title": "Test", "body": "Test body"}, approved=False)


def test_slack_operations_with_mock_server():
    """Test Slack channel list and message send operations."""
    with _priority_provider_mock_server() as base_url:
        registry = ConnectorAdapterRegistry()
        slack_manifest = next(m for m in priority_manifests() if m.connector_id == "slack")
        
        def handler(operation: OperationSpec, arguments: dict) -> AdapterResult:
            adapter = GenericHttpAdapter(
                base_url,
                provider_default_headers("slack"),
                allowed_hosts={"127.0.0.1"},
                allow_private=True,
            )
            return adapter(operation, arguments)
        
        registry.register(slack_manifest, handler)
        
        # Read operation should work without approval
        result = registry.invoke("slack", "list_channels", {}, approved=False)
        assert result.success is True
        assert result.data["ok"] is True
        
        # Sensitive operation requires approval
        with pytest.raises(PermissionError, match="explicit approval"):
            registry.invoke("slack", "send_message", {"channel": "C123", "text": "Test"}, approved=False)


def test_notion_operations_with_mock_server():
    """Test Notion search and page update operations."""
    with _priority_provider_mock_server() as base_url:
        registry = ConnectorAdapterRegistry()
        notion_manifest = next(m for m in priority_manifests() if m.connector_id == "notion")
        
        def handler(operation: OperationSpec, arguments: dict) -> AdapterResult:
            adapter = GenericHttpAdapter(
                base_url,
                provider_default_headers("notion"),
                allowed_hosts={"127.0.0.1"},
                allow_private=True,
            )
            return adapter(operation, arguments)
        
        registry.register(notion_manifest, handler)
        
        # Read operation
        result = registry.invoke("notion", "search", {"query": "test"}, approved=False)
        assert result.success is True
        assert len(result.data["results"]) > 0
        
        # Sensitive operation requires approval
        with pytest.raises(PermissionError, match="explicit approval"):
            registry.invoke("notion", "update_page", {"page_id": "page1", "properties": {}}, approved=False)


def test_google_services_operations_with_mock_server():
    """Test Google Gmail and Calendar operations."""
    with _priority_provider_mock_server() as base_url:
        registry = ConnectorAdapterRegistry()
        
        for connector_id in ["google-gmail", "google-calendar"]:
            manifest = next(m for m in priority_manifests() if m.connector_id == connector_id)
            
            def handler(operation: OperationSpec, arguments: dict) -> AdapterResult:
                adapter = GenericHttpAdapter(
                    base_url,
                    provider_default_headers(connector_id),
                    allowed_hosts={"127.0.0.1"},
                    allow_private=True,
                )
                return adapter(operation, arguments)
            
            registry.register(manifest, handler)
            
            # Read operation
            read_op = manifest.operations[0]
            result = registry.invoke(connector_id, read_op.operation_id, {}, approved=False)
            assert result.success is True
            
            # Write/sensitive operations require approval
            write_op = manifest.operations[1]
            with pytest.raises(PermissionError, match="explicit approval"):
                registry.invoke(connector_id, write_op.operation_id, {}, approved=False)


def test_microsoft_outlook_operations_with_mock_server():
    """Test Microsoft Outlook mail operations."""
    with _priority_provider_mock_server() as base_url:
        registry = ConnectorAdapterRegistry()
        outlook_manifest = next(m for m in priority_manifests() if m.connector_id == "microsoft-outlook")
        
        def handler(operation: OperationSpec, arguments: dict) -> AdapterResult:
            adapter = GenericHttpAdapter(
                base_url,
                provider_default_headers("microsoft-outlook"),
                allowed_hosts={"127.0.0.1"},
                allow_private=True,
            )
            return adapter(operation, arguments)
        
        registry.register(outlook_manifest, handler)
        
        # Read operation
        result = registry.invoke("microsoft-outlook", "list_messages", {}, approved=False)
        assert result.success is True
        
        # Critical send operation requires approval
        with pytest.raises(PermissionError, match="explicit approval"):
            registry.invoke("microsoft-outlook", "send_message", {"message": {}}, approved=False)


def test_stripe_operations_with_mock_server():
    """Test Stripe customer and payment operations."""
    with _priority_provider_mock_server() as base_url:
        registry = ConnectorAdapterRegistry()
        stripe_manifest = next(m for m in priority_manifests() if m.connector_id == "stripe")
        
        def handler(operation: OperationSpec, arguments: dict) -> AdapterResult:
            adapter = GenericHttpAdapter(
                base_url,
                provider_default_headers("stripe"),
                allowed_hosts={"127.0.0.1"},
                allow_private=True,
            )
            return adapter(operation, arguments)
        
        registry.register(stripe_manifest, handler)
        
        # Read operation
        result = registry.invoke("stripe", "list_customers", {}, approved=False)
        assert result.success is True
        assert result.data["object"] == "list"
        
        # Critical payment operation requires approval
        with pytest.raises(PermissionError, match="explicit approval"):
            registry.invoke("stripe", "create_payment", {"amount": 1000, "currency": "usd"}, approved=False)


def test_hubspot_operations_with_mock_server():
    """Test HubSpot contact operations."""
    with _priority_provider_mock_server() as base_url:
        registry = ConnectorAdapterRegistry()
        hubspot_manifest = next(m for m in priority_manifests() if m.connector_id == "hubspot")
        
        def handler(operation: OperationSpec, arguments: dict) -> AdapterResult:
            adapter = GenericHttpAdapter(
                base_url,
                provider_default_headers("hubspot"),
                allowed_hosts={"127.0.0.1"},
                allow_private=True,
            )
            return adapter(operation, arguments)
        
        registry.register(hubspot_manifest, handler)
        
        # Read operation
        result = registry.invoke("hubspot", "list_contacts", {}, approved=False)
        assert result.success is True
        
        # Sensitive operation requires approval
        with pytest.raises(PermissionError, match="explicit approval"):
            registry.invoke("hubspot", "create_contact", {"properties": {}}, approved=False)


def test_n8n_operations_with_mock_server():
    """Test n8n workflow operations."""
    with _priority_provider_mock_server() as base_url:
        registry = ConnectorAdapterRegistry()
        n8n_manifest = next(m for m in priority_manifests() if m.connector_id == "n8n")
        
        def handler(operation: OperationSpec, arguments: dict) -> AdapterResult:
            adapter = GenericHttpAdapter(
                base_url,
                provider_default_headers("n8n"),
                allowed_hosts={"127.0.0.1"},
                allow_private=True,
            )
            return adapter(operation, arguments)
        
        registry.register(n8n_manifest, handler)
        
        # Read operation
        result = registry.invoke("n8n", "list_workflows", {}, approved=False)
        assert result.success is True
        
        # Critical workflow execution requires approval
        with pytest.raises(PermissionError, match="explicit approval"):
            registry.invoke("n8n", "execute_workflow", {"workflow_id": "1", "data": {}}, approved=False)


def test_capability_audit_with_priority_providers():
    """Test that capability audit works with priority provider manifests."""
    registry = ConnectorAdapterRegistry()
    for manifest in priority_manifests():
        # Register with a dummy handler that always succeeds
        registry.register(manifest, lambda op, args: AdapterResult(True, 200, {"ok": True}))
    
    audit = ConnectorCapabilityAudit(registry)
    connector_ids = [m.connector_id for m in priority_manifests()]
    
    # Dry run should not invoke
    dry_results = audit.verify(connector_ids, invoke=False)
    assert all(not r.invoked for r in dry_results)
    assert all(r.success for r in dry_results)
    
    # Actual invocation should succeed for read operations
    invoke_results = audit.verify(connector_ids, invoke=True)
    assert all(r.invoked for r in invoke_results)
    assert all(r.success for r in invoke_results)


def test_provider_default_headers_are_safe():
    """Verify that provider default headers contain no credentials."""
    for connector_id in ["github", "slack", "notion", "google-gmail", "google-calendar", "microsoft-outlook", "stripe", "hubspot", "n8n"]:
        headers = provider_default_headers(connector_id)
        assert "Authorization" not in headers
        assert "api_key" not in headers
        assert "token" not in headers
        assert "password" not in headers
        assert "User-Agent" in headers
        assert "Orville" in headers["User-Agent"]


def test_priority_manifests_have_required_metadata():
    """Ensure all priority manifests have complete metadata."""
    for manifest in priority_manifests():
        assert manifest.connector_id
        assert manifest.display_name
        assert manifest.auth_type in {"oauth2", "api_key"}
        assert manifest.documentation_url.startswith("https://")
        assert manifest.supported is True
        assert len(manifest.operations) >= 2
        assert manifest.version
        assert manifest.limits
        assert manifest.limits["timeout_seconds"] > 0
        assert manifest.limits["max_response_bytes"] > 0
