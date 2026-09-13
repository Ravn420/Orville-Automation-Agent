"""Edge case and error handling tests for connector connections.

Tests focus on improving coverage for connector_connections.py by testing
error paths, validation failures, and edge cases not covered in integration tests.
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from cryptography.fernet import Fernet

from orville_core.connector_connections import (
    ConnectorConnection,
    ConnectorConnectionError,
    ConnectorConnectionStore,
)


def _configure_portable_master_key(monkeypatch) -> None:
    """Configure a synthetic master key for portable credential storage."""
    monkeypatch.setenv("ORVILLE_CONNECTOR_MASTER_KEY", Fernet.generate_key().decode("ascii"))


def test_connection_store_handles_corrupted_json(monkeypatch, tmp_path):
    """Test that connection store handles corrupted JSON gracefully."""
    _configure_portable_master_key(monkeypatch)
    
    # Write corrupted JSON
    (tmp_path / "connections.json").write_text("{invalid json", encoding="utf-8")
    
    # Store should initialize with empty records
    store = ConnectorConnectionStore(tmp_path / "connections.json")
    assert len(store._records) == 0


def test_connection_store_handles_malformed_record(monkeypatch, tmp_path):
    """Test that connection store skips malformed records."""
    _configure_portable_master_key(monkeypatch)
    
    # Write JSON with malformed record
    (tmp_path / "connections.json").write_text(
        json.dumps({
            "version": 1,
            "connections": [
                {"uid": "valid", "display_name": "Valid", "auth_type": "bearer", "credential_header": "Authorization", "base_url": "https://example.com", "status": "connected", "scopes": [], "_secret": "test"},
                {"invalid": "record"},  # Missing required fields
                {"uid": "", "display_name": "Empty", "auth_type": "bearer", "credential_header": "Authorization", "base_url": "https://example.com", "status": "connected", "scopes": []},  # Empty UID
            ],
        }),
        encoding="utf-8",
    )
    
    store = ConnectorConnectionStore(tmp_path / "connections.json")
    # Should only load the valid record
    assert len(store._records) == 1
    assert "valid" in store._records


def test_manual_connection_rejects_invalid_uid(monkeypatch, tmp_path):
    """Test that manual connection rejects invalid UIDs."""
    _configure_portable_master_key(monkeypatch)
    store = ConnectorConnectionStore(tmp_path / "connections.json")
    
    # Invalid characters
    with pytest.raises(ConnectorConnectionError, match="invalid connector UID"):
        store.connect_manual(
            uid="invalid uid!",  # Contains space and exclamation
            display_name="Test",
            auth_type="bearer",
            credential_header="Authorization",
            base_url="https://example.com",
            credential="token",
            scopes=["read"],
        )
    
    # Too long
    with pytest.raises(ConnectorConnectionError, match="invalid connector UID"):
        store.connect_manual(
            uid="x" * 161,  # Exceeds 160 character limit
            display_name="Test",
            auth_type="bearer",
            credential_header="Authorization",
            base_url="https://example.com",
            credential="token",
            scopes=["read"],
        )
    
    # Empty
    with pytest.raises(ConnectorConnectionError, match="invalid connector UID"):
        store.connect_manual(
            uid="",
            display_name="Test",
            auth_type="bearer",
            credential_header="Authorization",
            base_url="https://example.com",
            credential="token",
            scopes=["read"],
        )


def test_manual_connection_rejects_invalid_auth_type(monkeypatch, tmp_path):
    """Test that manual connection rejects unsupported auth types."""
    _configure_portable_master_key(monkeypatch)
    store = ConnectorConnectionStore(tmp_path / "connections.json")
    
    with pytest.raises(ConnectorConnectionError, match="manual authentication must use"):
        store.connect_manual(
            uid="test",
            display_name="Test",
            auth_type="oauth2",  # OAuth not allowed for manual connection
            credential_header="Authorization",
            base_url="https://example.com",
            credential="token",
            scopes=["read"],
        )


def test_manual_connection_rejects_invalid_credential_header(monkeypatch, tmp_path):
    """Test that manual connection validates credential header format."""
    _configure_portable_master_key(monkeypatch)
    store = ConnectorConnectionStore(tmp_path / "connections.json")
    
    # Contains invalid characters
    with pytest.raises(ConnectorConnectionError, match="credential header"):
        store.connect_manual(
            uid="test",
            display_name="Test",
            auth_type="bearer",
            credential_header="Invalid Header",  # Contains space
            base_url="https://example.com",
            credential="token",
            scopes=["read"],
        )
    
    # Empty
    with pytest.raises(ConnectorConnectionError, match="credential header"):
        store.connect_manual(
            uid="test",
            display_name="Test",
            auth_type="bearer",
            credential_header="",
            base_url="https://example.com",
            credential="token",
            scopes=["read"],
        )


def test_manual_connection_rejects_empty_credential(monkeypatch, tmp_path):
    """Test that manual connection rejects empty credentials."""
    _configure_portable_master_key(monkeypatch)
    store = ConnectorConnectionStore(tmp_path / "connections.json")
    
    with pytest.raises(ConnectorConnectionError, match="credential is required"):
        store.connect_manual(
            uid="test",
            display_name="Test",
            auth_type="bearer",
            credential_header="Authorization",
            base_url="https://example.com",
            credential="",  # Empty credential
            scopes=["read"],
        )
    
    with pytest.raises(ConnectorConnectionError, match="credential is required"):
        store.connect_manual(
            uid="test",
            display_name="Test",
            auth_type="bearer",
            credential_header="Authorization",
            base_url="https://example.com",
            credential="   ",  # Whitespace only
            scopes=["read"],
        )


def test_manual_connection_rejects_invalid_base_url(monkeypatch, tmp_path):
    """Test that manual connection validates base URL."""
    _configure_portable_master_key(monkeypatch)
    store = ConnectorConnectionStore(tmp_path / "connections.json")
    
    # Invalid scheme
    with pytest.raises(ConnectorConnectionError, match="HTTP"):
        store.connect_manual(
            uid="test",
            display_name="Test",
            auth_type="bearer",
            credential_header="Authorization",
            base_url="ftp://example.com",  # Invalid scheme
            credential="token",
            scopes=["read"],
        )
    
    # Private host without allow_local
    with pytest.raises(ConnectorConnectionError, match="private"):
        store.connect_manual(
            uid="test",
            display_name="Test",
            auth_type="bearer",
            credential_header="Authorization",
            base_url="http://192.168.1.1",  # Private IP
            credential="token",
            scopes=["read"],
            allow_local=False,
        )


def test_connection_public_redacts_sensitive_fields():
    """Test that connection.public() redacts sensitive fields."""
    connection = ConnectorConnection(
        uid="test",
        display_name="Test",
        auth_type="oauth2",
        credential_header="Authorization",
        base_url="https://example.com",
        status="connected",
        scopes=["read"],
        _secret="secret_token",
        client_secret="client_secret_value",
        state="state_value",
        code_verifier="verifier_value",
        refresh_token="refresh_token_value",
    )
    
    public = connection.public()
    
    assert "_secret" not in public
    assert "client_secret" not in public
    assert "state" not in public
    assert "code_verifier" not in public
    assert "refresh_token" not in public
    assert public["has_credential"] is True
    assert public["has_refresh_token"] is True


def test_connection_persists_operation_count(monkeypatch, tmp_path):
    """Test that operation count persists across store reloads."""
    _configure_portable_master_key(monkeypatch)
    
    # Create initial connection
    store1 = ConnectorConnectionStore(tmp_path / "connections.json")
    store1.connect_manual(
        uid="test",
        display_name="Test",
        auth_type="bearer",
        credential_header="Authorization",
        base_url="https://example.com",
        credential="token",
        scopes=["read"],
    )
    
    # Mark operations
    store1.mark_operation("test")
    store1.mark_operation("test")
    store1.mark_operation("test")
    
    # Reload store
    store2 = ConnectorConnectionStore(tmp_path / "connections.json")
    record = store2.get("test")
    assert record.operation_count == 3


def test_credential_retrieval_requires_connected_status(monkeypatch, tmp_path):
    """Test that credential retrieval requires connected status."""
    _configure_portable_master_key(monkeypatch)
    store = ConnectorConnectionStore(tmp_path / "connections.json")
    
    # Create connection in authorization_required state
    store.begin_oauth(
        uid="test",
        display_name="Test",
        base_url="https://example.com",
        auth_url="https://example.com/auth",
        token_url="https://example.com/token",
        client_id="test_client",
        client_secret="test_secret",
        scopes=["read"],
        redirect_uri="http://127.0.0.1:8080/callback",
        allow_local=True,
    )
    
    with pytest.raises(ConnectorConnectionError, match="sign-in before invocation"):
        store.credential("test")


def test_credential_retrieval_validates_owner_id(monkeypatch, tmp_path):
    """Test that credential retrieval validates owner ID."""
    _configure_portable_master_key(monkeypatch)
    store = ConnectorConnectionStore(tmp_path / "connections.json")
    
    store.connect_manual(
        uid="test",
        display_name="Test",
        auth_type="bearer",
        credential_header="Authorization",
        base_url="https://example.com",
        credential="token",
        scopes=["read"],
        owner_id="owner-1",
    )
    
    # Wrong owner
    with pytest.raises(ConnectorConnectionError, match="owner does not match"):
        store.credential("test", owner_id="owner-2")
    
    # Correct owner
    record, credential = store.credential("test", owner_id="owner-1")
    assert credential == "token"


def test_credential_retrieval_validates_scopes(monkeypatch, tmp_path):
    """Test that credential retrieval validates required scopes."""
    _configure_portable_master_key(monkeypatch)
    store = ConnectorConnectionStore(tmp_path / "connections.json")
    
    store.connect_manual(
        uid="test",
        display_name="Test",
        auth_type="bearer",
        credential_header="Authorization",
        base_url="https://example.com",
        credential="token",
        scopes=["read", "write"],
    )
    
    # Missing required scope
    with pytest.raises(ConnectorConnectionError, match="scopes are insufficient"):
        store.credential("test", required_scopes={"read", "write", "admin"})
    
    # Sufficient scopes
    record, credential = store.credential("test", required_scopes={"read"})
    assert credential == "token"


def test_disconnect_removes_connection(monkeypatch, tmp_path):
    """Test that disconnect removes connection from store."""
    _configure_portable_master_key(monkeypatch)
    store = ConnectorConnectionStore(tmp_path / "connections.json")
    
    store.connect_manual(
        uid="test",
        display_name="Test",
        auth_type="bearer",
        credential_header="Authorization",
        base_url="https://example.com",
        credential="token",
        scopes=["read"],
    )
    
    assert store.get("test") is not None
    
    result = store.disconnect("test")
    assert result is True
    assert store.get("test") is None


def test_disconnect_nonexistent_returns_false(monkeypatch, tmp_path):
    """Test that disconnecting nonexistent connection returns False."""
    _configure_portable_master_key(monkeypatch)
    store = ConnectorConnectionStore(tmp_path / "connections.json")
    
    result = store.disconnect("nonexistent")
    assert result is False


def test_connection_list_is_sorted(monkeypatch, tmp_path):
    """Test that connection list is sorted by display name."""
    _configure_portable_master_key(monkeypatch)
    store = ConnectorConnectionStore(tmp_path / "connections.json")
    
    store.connect_manual(
        uid="z",
        display_name="Zebra",
        auth_type="bearer",
        credential_header="Authorization",
        base_url="https://example.com",
        credential="token",
        scopes=["read"],
    )
    store.connect_manual(
        uid="a",
        display_name="Apple",
        auth_type="bearer",
        credential_header="Authorization",
        base_url="https://example.com",
        credential="token",
        scopes=["read"],
    )
    store.connect_manual(
        uid="m",
        display_name="Mango",
        auth_type="bearer",
        credential_header="Authorization",
        base_url="https://example.com",
        credential="token",
        scopes=["read"],
    )
    
    connections = store.list_public()
    assert [c["display_name"] for c in connections] == ["Apple", "Mango", "Zebra"]


def test_connection_store_is_thread_safe(monkeypatch, tmp_path):
    """Test that connection store handles concurrent operations."""
    _configure_portable_master_key(monkeypatch)
    store = ConnectorConnectionStore(tmp_path / "connections.json")
    
    errors = []
    
    def connect_worker(i):
        try:
            store.connect_manual(
                uid=f"test-{i}",
                display_name=f"Test {i}",
                auth_type="bearer",
                credential_header="Authorization",
                base_url="https://example.com",
                credential=f"token-{i}",
                scopes=["read"],
            )
        except Exception as e:
            errors.append(e)
    
    threads = [threading.Thread(target=connect_worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    assert len(errors) == 0
    assert len(store._records) == 10


def test_connection_store_atomic_write(monkeypatch, tmp_path):
    """Test that connection store uses atomic write with temp file."""
    _configure_portable_master_key(monkeypatch)
    store = ConnectorConnectionStore(tmp_path / "connections.json")
    
    store.connect_manual(
        uid="test",
        display_name="Test",
        auth_type="bearer",
        credential_header="Authorization",
        base_url="https://example.com",
        credential="token",
        scopes=["read"],
    )
    
    # Verify temp file was cleaned up
    assert not (tmp_path / "connections.json.tmp").exists()
    
    # Verify main file exists and is valid
    assert (tmp_path / "connections.json").exists()
    data = json.loads((tmp_path / "connections.json").read_text(encoding="utf-8"))
    assert "connections" in data


def test_oauth_token_exchange_failure_updates_status(monkeypatch, tmp_path):
    """Test that OAuth token exchange failure updates connection status."""
    _configure_portable_master_key(monkeypatch)
    store = ConnectorConnectionStore(tmp_path / "connections.json")
    
    # Begin OAuth with invalid token URL
    store.begin_oauth(
        uid="test-fail",
        display_name="Test Fail",
        base_url="https://example.com",
        auth_url="https://example.com/auth",
        token_url="https://invalid-nonexistent.example.com/token",  # Invalid URL
        client_id="test_client",
        client_secret="test_secret",
        scopes=["read"],
        redirect_uri="http://127.0.0.1:8080/callback",
        allow_local=True,
    )
    
    record = store.get("test-fail")
    
    # Token exchange should fail
    with pytest.raises(ConnectorConnectionError, match="token exchange"):
        store.complete_oauth("test-fail", "code", record.state)
    
    # Verify status was updated to error
    failed_record = store.get("test-fail")
    assert failed_record.status == "error"
    assert failed_record.last_error is not None


def test_oauth_refresh_failure_updates_status(monkeypatch, tmp_path):
    """Test that OAuth refresh failure updates connection status."""
    _configure_portable_master_key(monkeypatch)
    store = ConnectorConnectionStore(tmp_path / "connections.json")
    
    # Manually create a connection with refresh token
    from orville_core.connector_connections import _protect
    
    store._records["test-refresh-fail"] = ConnectorConnection(
        uid="test-refresh-fail",
        display_name="Test Refresh Fail",
        auth_type="oauth2",
        credential_header="Authorization",
        base_url="https://example.com",
        status="connected",
        scopes=["read"],
        _secret=_protect("access_token"),
        refresh_token=_protect("refresh_token"),
        token_url="https://invalid-nonexistent.example.com/token",  # Invalid URL
        client_id="test_client",
    )
    store._save()
    
    # Refresh should fail
    with pytest.raises(ConnectorConnectionError, match="refresh failed"):
        store.refresh("test-refresh-fail")
    
    # Verify status was updated
    failed_record = store.get("test-refresh-fail")
    assert failed_record.status == "reauthorization_required"
    assert failed_record.last_error is not None


def test_connection_without_refresh_token_cannot_refresh(monkeypatch, tmp_path):
    """Test that connection without refresh token cannot refresh."""
    _configure_portable_master_key(monkeypatch)
    store = ConnectorConnectionStore(tmp_path / "connections.json")
    
    from orville_core.connector_connections import _protect
    
    store._records["test-no-refresh"] = ConnectorConnection(
        uid="test-no-refresh",
        display_name="Test No Refresh",
        auth_type="oauth2",
        credential_header="Authorization",
        base_url="https://example.com",
        status="connected",
        scopes=["read"],
        _secret=_protect("access_token"),
        # No refresh_token
        token_url="https://example.com/token",
        client_id="test_client",
    )
    store._save()
    
    with pytest.raises(ConnectorConnectionError, match="no refresh token"):
        store.refresh("test-no-refresh")


def test_connection_status_validation():
    """Test ConnectorConnection status validation."""
    # Valid statuses
    for status in ["connected", "authorization_required", "error", "reauthorization_required"]:
        conn = ConnectorConnection(
            uid="test",
            display_name="Test",
            auth_type="bearer",
            credential_header="Authorization",
            base_url="https://example.com",
            status=status,
            scopes=["read"],
        )
        assert conn.status == status
    
    # Invalid status would be caught by higher-level validation


def test_mark_operation_on_nonexistent_connection(monkeypatch, tmp_path):
    """Test that marking operation on nonexistent connection is safe."""
    _configure_portable_master_key(monkeypatch)
    store = ConnectorConnectionStore(tmp_path / "connections.json")
    
    # Should not raise an error
    store.mark_operation("nonexistent")
