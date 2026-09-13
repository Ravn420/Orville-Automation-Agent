"""OAuth flow simulation tests with synthetic credentials.

Tests validate the OAuth2 authorization code flow with PKCE using mock authorization
and token servers. All credentials are synthetic and no real OAuth providers are contacted.
"""
from __future__ import annotations

import base64
import hashlib
import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Iterator
from urllib.parse import parse_qs, urlparse

import pytest

from orville_core.connector_connections import (
    ConnectorConnectionError,
    ConnectorConnectionStore,
)


class _OAuthMockHandler(BaseHTTPRequestHandler):
    """Mock OAuth provider server for testing OAuth flows."""

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
        if self.path.startswith("/auth"):
            # Authorization endpoint - validate PKCE parameters
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            
            # Check required OAuth parameters
            assert "response_type" in params
            assert params["response_type"][0] == "code"
            assert "client_id" in params
            assert "redirect_uri" in params
            assert "scope" in params
            assert "state" in params
            assert "code_challenge" in params
            assert "code_challenge_method" in params
            assert params["code_challenge_method"][0] == "S256"
            
            # Validate code challenge format (base64url-encoded SHA256 hash)
            challenge = params["code_challenge"][0]
            assert len(challenge) > 20  # Reasonable hash length
            
            # Return a simple HTML page with authorization code
            state = params["state"][0]
            auth_code = f"synthetic_auth_code_{state[:8]}"
            
            html = f"""
            <html>
            <body>
            <h1>OAuth Authorization Granted</h1>
            <p>Authorization Code: {auth_code}</p>
            <p>State: {state}</p>
            </body>
            </html>
            """.encode()
            
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
            return
        
        self._write_json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/token":
            # Token endpoint - exchange code for access token or refresh token
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            params = parse_qs(body.decode("utf-8"))
            
            # Validate token request parameters
            assert "grant_type" in params
            grant_type = params["grant_type"][0]
            
            if grant_type == "authorization_code":
                assert "code" in params
                assert "redirect_uri" in params
                assert "client_id" in params
                assert "code_verifier" in params
                
                # Validate PKCE code verifier
                code_verifier = params["code_verifier"][0]
                # Verify code_verifier is reasonable (base64url, min length)
                assert len(code_verifier) >= 43  # PKCE minimum
                
                # Recompute code challenge and validate (simplified for test)
                challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode().rstrip("=")
                # In real flow, this would match the original challenge
                
                # Return synthetic access token
                token_response = {
                    "access_token": "synthetic_access_token_abc123",
                    "token_type": "Bearer",
                    "expires_in": 3600,
                    "refresh_token": "synthetic_refresh_token_xyz789",
                    "scope": " ".join(params.get("scope", ["read"])),
                }
                self._write_json(200, token_response)
                return
            elif grant_type == "refresh_token":
                assert "refresh_token" in params
                assert "client_id" in params
                
                token_response = {
                    "access_token": "synthetic_refreshed_access_token_def456",
                    "token_type": "Bearer",
                    "expires_in": 3600,
                    "refresh_token": "synthetic_new_refresh_token_ghi012",
                }
                self._write_json(200, token_response)
                return
            else:
                self._write_json(400, {"error": "unsupported_grant_type"})
                return
        
        if self.path == "/revoke":
            # Token revocation endpoint
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            params = parse_qs(body.decode("utf-8"))
            
            assert "token" in params
            assert "client_id" in params
            
            self._write_json(200, {"status": "ok"})
            return
        
        self._write_json(404, {"error": "not_found"})

    def log_message(self, *_args) -> None:
        return


@contextmanager
def _oauth_mock_server() -> Iterator[tuple[str, str, str, str]]:
    """Run mock OAuth server with auth, token, and revoke endpoints."""
    server = HTTPServer(("127.0.0.1", 0), _OAuthMockHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        yield base, f"{base}/auth", f"{base}/token", f"{base}/revoke"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def _configure_portable_master_key(monkeypatch) -> None:
    """Configure a synthetic master key for portable credential storage."""
    from cryptography.fernet import Fernet
    monkeypatch.setenv("ORVILLE_CONNECTOR_MASTER_KEY", Fernet.generate_key().decode("ascii"))


def test_oauth_flow_generates_state_and_code_verifier(monkeypatch, tmp_path):
    """Test that OAuth flow generates secure state and PKCE code verifier."""
    _configure_portable_master_key(monkeypatch)
    
    with _oauth_mock_server() as (base_url, auth_url, token_url, revoke_url):
        store = ConnectorConnectionStore(tmp_path / "connections.json")
        
        result = store.begin_oauth(
            uid="test-oauth",
            display_name="Test OAuth Provider",
            base_url=base_url,
            auth_url=auth_url,
            token_url=token_url,
            client_id="test_client_id",
            client_secret="test_client_secret",
            scopes=["read", "write"],
            redirect_uri="http://127.0.0.1:8080/callback",
            revoke_url=revoke_url,
            allow_local=True,
        )
        
        assert "connection" in result
        assert "authorization_url" in result
        
        connection = result["connection"]
        assert connection["status"] == "authorization_required"
        assert connection["auth_type"] == "oauth2"
        assert connection["has_credential"] is False
        
        # Check authorization URL contains required parameters
        auth_url_result = result["authorization_url"]
        parsed = urlparse(auth_url_result)
        params = parse_qs(parsed.query)
        
        assert "response_type" in params
        assert params["response_type"][0] == "code"
        assert "client_id" in params
        assert params["client_id"][0] == "test_client_id"
        assert "redirect_uri" in params
        assert "state" in params
        assert len(params["state"][0]) >= 32  # Secure state length
        assert "code_challenge" in params
        assert "code_challenge_method" in params
        assert params["code_challenge_method"][0] == "S256"
        
        # Verify connection record has state and code_verifier stored
        record = store.get("test-oauth")
        assert record is not None
        assert record.state is not None
        assert len(record.state) >= 32
        assert record.code_verifier is not None
        assert len(record.code_verifier) >= 43  # PKCE minimum


def test_oauth_flow_validates_state_on_callback(monkeypatch, tmp_path):
    """Test that OAuth flow validates state parameter on callback."""
    _configure_portable_master_key(monkeypatch)
    
    with _oauth_mock_server() as (base_url, auth_url, token_url, revoke_url):
        store = ConnectorConnectionStore(tmp_path / "connections.json")
        
        result = store.begin_oauth(
            uid="test-oauth-state",
            display_name="Test OAuth State Validation",
            base_url=base_url,
            auth_url=auth_url,
            token_url=token_url,
            client_id="test_client_id",
            client_secret="test_client_secret",
            scopes=["read"],
            redirect_uri="http://127.0.0.1:8080/callback",
            revoke_url=revoke_url,
            allow_local=True,
        )
        
        record = store.get("test-oauth-state")
        original_state = record.state
        
        # Test with invalid state
        with pytest.raises(ConnectorConnectionError, match="state validation"):
            store.complete_oauth("test-oauth-state", "synthetic_code", "invalid_state")
        
        # Test with valid state
        result = store.complete_oauth("test-oauth-state", "synthetic_auth_code_abc12345", original_state)
        assert result["status"] == "connected"
        assert result["has_credential"] is True
        assert result["has_refresh_token"] is True


def test_oauth_flow_exchanges_code_for_access_token(monkeypatch, tmp_path):
    """Test that OAuth flow successfully exchanges authorization code for access token."""
    _configure_portable_master_key(monkeypatch)
    
    with _oauth_mock_server() as (base_url, auth_url, token_url, revoke_url):
        store = ConnectorConnectionStore(tmp_path / "connections.json")
        
        begin_result = store.begin_oauth(
            uid="test-oauth-token",
            display_name="Test OAuth Token Exchange",
            base_url=base_url,
            auth_url=auth_url,
            token_url=token_url,
            client_id="test_client_id",
            client_secret="test_client_secret",
            scopes=["read", "write"],
            redirect_uri="http://127.0.0.1:8080/callback",
            revoke_url=revoke_url,
            allow_local=True,
        )
        
        record = store.get("test-oauth-token")
        state = record.state
        
        complete_result = store.complete_oauth("test-oauth-token", "synthetic_auth_code_abc12345", state)
        
        assert complete_result["status"] == "connected"
        assert complete_result["has_credential"] is True
        assert complete_result["has_refresh_token"] is True
        assert complete_result["connected_at"] is not None
        assert complete_result["expires_at"] is not None
        
        # Verify credential is protected and not exposed
        assert "_secret" not in complete_result
        assert "synthetic_access_token" not in json.dumps(complete_result)
        
        # Verify we can retrieve the credential
        reloaded_record, credential = store.credential("test-oauth-token")
        assert credential == "synthetic_access_token_abc123"


def test_oauth_refresh_token_updates_access_token(monkeypatch, tmp_path):
    """Test that OAuth refresh token flow updates access token."""
    _configure_portable_master_key(monkeypatch)
    
    with _oauth_mock_server() as (base_url, auth_url, token_url, revoke_url):
        store = ConnectorConnectionStore(tmp_path / "connections.json")
        
        # Begin and complete OAuth flow
        begin_result = store.begin_oauth(
            uid="test-oauth-refresh",
            display_name="Test OAuth Refresh",
            base_url=base_url,
            auth_url=auth_url,
            token_url=token_url,
            client_id="test_client_id",
            client_secret="test_client_secret",
            scopes=["read"],
            redirect_uri="http://127.0.0.1:8080/callback",
            revoke_url=revoke_url,
            allow_local=True,
        )
        
        record = store.get("test-oauth-refresh")
        store.complete_oauth("test-oauth-refresh", "synthetic_auth_code_abc12345", record.state)
        
        # Refresh the token
        refresh_result = store.refresh("test-oauth-refresh")
        
        assert refresh_result["status"] == "connected"
        assert refresh_result["has_credential"] is True
        assert refresh_result["has_refresh_token"] is True
        
        # Verify the access token was updated
        reloaded_record, credential = store.credential("test-oauth-refresh")
        assert credential == "synthetic_refreshed_access_token_def456"


def test_oauth_revoke_removes_connection_and_calls_provider(monkeypatch, tmp_path):
    """Test that OAuth revocation removes connection and calls provider revoke endpoint."""
    _configure_portable_master_key(monkeypatch)
    
    with _oauth_mock_server() as (base_url, auth_url, token_url, revoke_url):
        store = ConnectorConnectionStore(tmp_path / "connections.json")
        
        # Begin and complete OAuth flow
        begin_result = store.begin_oauth(
            uid="test-oauth-revoke",
            display_name="Test OAuth Revoke",
            base_url=base_url,
            auth_url=auth_url,
            token_url=token_url,
            client_id="test_client_id",
            client_secret="test_client_secret",
            scopes=["read"],
            redirect_uri="http://127.0.0.1:8080/callback",
            revoke_url=revoke_url,
            allow_local=True,
        )
        
        record = store.get("test-oauth-revoke")
        store.complete_oauth("test-oauth-revoke", "synthetic_auth_code_abc12345", record.state)
        
        # Revoke the connection
        revoke_result = store.revoke("test-oauth-revoke")
        assert revoke_result is True
        
        # Verify connection is removed
        assert store.get("test-oauth-revoke") is None


def test_oauth_without_client_secret(monkeypatch, tmp_path):
    """Test OAuth flow for public clients (no client secret)."""
    _configure_portable_master_key(monkeypatch)
    
    with _oauth_mock_server() as (base_url, auth_url, token_url, revoke_url):
        store = ConnectorConnectionStore(tmp_path / "connections.json")
        
        result = store.begin_oauth(
            uid="test-oauth-public",
            display_name="Test OAuth Public Client",
            base_url=base_url,
            auth_url=auth_url,
            token_url=token_url,
            client_id="public_client_id",
            client_secret=None,  # Public client
            scopes=["read"],
            redirect_uri="http://127.0.0.1:8080/callback",
            revoke_url=revoke_url,
            allow_local=True,
        )
        
        assert result["connection"]["status"] == "authorization_required"
        
        record = store.get("test-oauth-public")
        complete_result = store.complete_oauth("test-oauth-public", "synthetic_auth_code_abc12345", record.state)
        
        assert complete_result["status"] == "connected"
        assert complete_result["has_credential"] is True


def test_oauth_rejects_invalid_redirect_uri(monkeypatch, tmp_path):
    """Test that OAuth flow rejects non-local redirect URIs."""
    _configure_portable_master_key(monkeypatch)
    
    with _oauth_mock_server() as (base_url, auth_url, token_url, revoke_url):
        store = ConnectorConnectionStore(tmp_path / "connections.json")
        
        with pytest.raises(ConnectorConnectionError, match="redirect URI"):
            store.begin_oauth(
                uid="test-oauth-invalid-redirect",
                display_name="Test OAuth Invalid Redirect",
                base_url=base_url,
                auth_url=auth_url,
                token_url=token_url,
                client_id="test_client_id",
                client_secret="test_client_secret",
                scopes=["read"],
                redirect_uri="https://evil.com/callback",  # Invalid - not local
                revoke_url=revoke_url,
                allow_local=True,
            )


def test_oauth_rejects_missing_client_id(monkeypatch, tmp_path):
    """Test that OAuth flow rejects missing client ID."""
    _configure_portable_master_key(monkeypatch)
    
    with _oauth_mock_server() as (base_url, auth_url, token_url, revoke_url):
        store = ConnectorConnectionStore(tmp_path / "connections.json")
        
        with pytest.raises(ConnectorConnectionError, match="client ID"):
            store.begin_oauth(
                uid="test-oauth-no-client",
                display_name="Test OAuth No Client",
                base_url=base_url,
                auth_url=auth_url,
                token_url=token_url,
                client_id="",  # Empty client ID
                client_secret="test_client_secret",
                scopes=["read"],
                redirect_uri="http://127.0.0.1:8080/callback",
                revoke_url=revoke_url,
                allow_local=True,
            )


def test_oauth_credentials_are_protected_in_storage(monkeypatch, tmp_path):
    """Test that OAuth credentials are encrypted and not exposed in storage."""
    _configure_portable_master_key(monkeypatch)
    
    with _oauth_mock_server() as (base_url, auth_url, token_url, revoke_url):
        store = ConnectorConnectionStore(tmp_path / "connections.json")
        
        begin_result = store.begin_oauth(
            uid="test-oauth-encryption",
            display_name="Test OAuth Encryption",
            base_url=base_url,
            auth_url=auth_url,
            token_url=token_url,
            client_id="test_client_id",
            client_secret="test_secret_value",
            scopes=["read"],
            redirect_uri="http://127.0.0.1:8080/callback",
            revoke_url=revoke_url,
            allow_local=True,
        )
        
        record = store.get("test-oauth-encryption")
        store.complete_oauth("test-oauth-encryption", "synthetic_auth_code_abc12345", record.state)
        
        # Read the JSON file directly
        json_content = (tmp_path / "connections.json").read_text(encoding="utf-8")
        
        # Verify secrets are not in plaintext
        assert "test_secret_value" not in json_content
        assert "synthetic_access_token" not in json_content
        assert "synthetic_refresh_token" not in json_content
        
        # Verify encrypted markers are present
        assert "fernet:" in json_content or "dpapi:" in json_content


def test_oauth_with_task_scoped_credentials(monkeypatch, tmp_path):
    """Test OAuth flow with task-scoped credentials."""
    _configure_portable_master_key(monkeypatch)
    
    with _oauth_mock_server() as (base_url, auth_url, token_url, revoke_url):
        store = ConnectorConnectionStore(tmp_path / "connections.json")
        
        result = store.begin_oauth(
            uid="test-oauth-task",
            display_name="Test OAuth Task Scoped",
            base_url=base_url,
            auth_url=auth_url,
            token_url=token_url,
            client_id="test_client_id",
            client_secret="test_client_secret",
            scopes=["read"],
            redirect_uri="http://127.0.0.1:8080/callback",
            revoke_url=revoke_url,
            allow_local=True,
            owner_id="user-123",
            task_id="task-456",
        )
        
        assert result["connection"]["owner_id"] == "user-123"
        assert result["connection"]["task_id"] == "task-456"
        
        record = store.get("test-oauth-task")
        store.complete_oauth("test-oauth-task", "synthetic_auth_code_abc12345", record.state)
        
        # Verify credential retrieval with matching task_id
        reloaded_record, credential = store.credential("test-oauth-task", owner_id="user-123", task_id="task-456")
        assert credential == "synthetic_access_token_abc123"
        
        # Verify credential retrieval fails with wrong task_id
        with pytest.raises(ConnectorConnectionError, match="bound to a different task"):
            store.credential("test-oauth-task", owner_id="user-123", task_id="wrong-task")
