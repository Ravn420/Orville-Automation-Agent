"""Tests for integration health checks."""
import os
import sqlite3
from unittest.mock import MagicMock, patch

import pytest

from orville_core.health_integration import (
    IntegrationHealthChecker,
    IntegrationHealthResult,
    create_health_check_from_integration_result,
)
from orville_core.health_persistence import (
    HealthCheckPersistence,
    HealthCheckRecord,
)


def test_integration_health_result_creation():
    """Test creating an integration health result."""
    result = IntegrationHealthResult(
        integration_name="test-integration",
        available=True,
        version="1.0.0",
        detail="Test integration is working",
    )
    
    assert result.integration_name == "test-integration"
    assert result.available is True
    assert result.version == "1.0.0"
    assert result.detail == "Test integration is working"
    assert result.to_dict() == {
        "integration_name": "test-integration",
        "available": True,
        "version": "1.0.0",
        "detail": "Test integration is working",
        "last_checked_at": result.last_checked_at,
        "error": None,
    }


def test_integration_health_result_with_error():
    """Test creating an integration health result with an error."""
    result = IntegrationHealthResult(
        integration_name="test-integration",
        available=False,
        error="Connection failed",
    )
    
    assert result.available is False
    assert result.error == "Connection failed"
    assert result.to_dict()["error"] == "Connection failed"


def test_create_health_check_from_integration_result():
    """Test creating a HealthCheck from an IntegrationHealthResult."""
    integration_result = IntegrationHealthResult(
        integration_name="test-integration",
        available=True,
        version="1.0.0",
        detail="Test integration is working",
    )
    
    health_check = create_health_check_from_integration_result(integration_result)
    
    assert health_check.name == "test-integration"
    assert health_check.available is True
    assert health_check.version == "1.0.0"
    assert health_check.detail == "Test integration is working"
    assert health_check.required is False


def test_integration_health_checker_initialization():
    """Test initializing the integration health checker."""
    checker = IntegrationHealthChecker(
        enable_manus_mcp=False,
        enable_api_gateway=False,
        enable_database=False,
        enable_artifact_storage=False,
    )
    
    assert checker.enable_manus_mcp is False
    assert checker.enable_api_gateway is False
    assert checker.enable_database is False
    assert checker.enable_artifact_storage is False


def test_integration_health_checker_run_all_disabled():
    """Test running all checks when all are disabled."""
    checker = IntegrationHealthChecker(
        enable_manus_mcp=False,
        enable_api_gateway=False,
        enable_database=False,
        enable_artifact_storage=False,
    )
    
    results = checker.run_all()
    
    assert len(results) == 0


def test_integration_health_checker_manus_mcp_not_found(monkeypatch):
    """Test Manus MCP server check when not found."""
    monkeypatch.setattr("os.path.exists", lambda path: False)
    
    checker = IntegrationHealthChecker(enable_manus_mcp=True)
    result = checker.check_manus_mcp_server()
    
    assert result.integration_name == "manus-mcp-server"
    assert result.available is False
    assert "not found" in result.detail.lower()


def test_integration_health_checker_manus_mcp_found(monkeypatch):
    """Test Manus MCP server check when found."""
    monkeypatch.setattr("os.path.exists", lambda path: True)
    monkeypatch.setattr("subprocess.run", lambda cmd, **kwargs: MagicMock(
        returncode=0,
        stdout="manus-mcp-cli 1.2.3\n",
        stderr="",
    ))
    
    checker = IntegrationHealthChecker(enable_manus_mcp=True)
    result = checker.check_manus_mcp_server()
    
    assert result.available is True
    assert result.version == "manus-mcp-cli 1.2.3"
    assert "available" in result.detail.lower()


def test_integration_health_checker_api_gateway_unreachable(monkeypatch):
    """Test API gateway check when unreachable."""
    import urllib.request
    original_urlopen = urllib.request.urlopen
    
    def mock_urlopen(*args, **kwargs):
        raise Exception("Connection refused")
    
    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen)
    
    checker = IntegrationHealthChecker(enable_api_gateway=True)
    result = checker.check_api_gateway()
    
    assert result.integration_name == "api-gateway"
    assert result.available is False
    assert "connection refused" in result.detail.lower()
    
    monkeypatch.setattr("urllib.request.urlopen", original_urlopen)


def test_integration_health_checker_api_gateway_reachable(monkeypatch):
    """Test API gateway check when reachable."""
    import urllib.request
    original_urlopen = urllib.request.urlopen
    
    # Create a proper mock response with status
    mock_response = MagicMock()
    mock_response.status = 200
    
    # Create a context manager mock
    mock_context = MagicMock()
    mock_context.__enter__ = MagicMock(return_value=mock_response)
    mock_context.__exit__ = MagicMock(return_value=False)
    
    # Mock urlopen to return the context manager
    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: mock_context)
    
    checker = IntegrationHealthChecker(enable_api_gateway=True)
    result = checker.check_api_gateway()
    
    assert result.available is True
    assert result.version == "HTTP 200"
    assert "accessible" in result.detail.lower()
    
    monkeypatch.setattr("urllib.request.urlopen", original_urlopen)


def test_integration_health_checker_database_not_found(monkeypatch):
    """Test database check when file not found."""
    monkeypatch.setattr("os.path.exists", lambda path: False)
    
    checker = IntegrationHealthChecker(enable_database=True)
    result = checker.check_database()
    
    assert result.integration_name == "database"
    assert result.available is False
    assert "not found" in result.detail.lower()


def test_integration_health_checker_database_accessible(monkeypatch):
    """Test database check when accessible."""
    monkeypatch.setattr("os.path.exists", lambda path: True)
    monkeypatch.setattr("sqlite3.connect", lambda path, **kwargs: MagicMock(
        cursor=lambda: MagicMock(
            execute=lambda query: MagicMock(fetchone=lambda: (1,)),
            close=lambda: None,
        ),
    ))
    
    checker = IntegrationHealthChecker(enable_database=True)
    result = checker.check_database()
    
    assert result.available is True
    assert result.version == "SQLite"
    assert "accessible" in result.detail.lower()


def test_integration_health_checker_artifact_dir_not_found(monkeypatch):
    """Test artifact storage check when directory not found."""
    monkeypatch.setattr("os.path.exists", lambda path: False)
    
    checker = IntegrationHealthChecker(enable_artifact_storage=True)
    result = checker.check_artifact_storage()
    
    assert result.integration_name == "artifact-storage"
    assert result.available is False
    assert "not found" in result.detail.lower()


def test_integration_health_checker_artifact_dir_accessible(monkeypatch):
    """Test artifact storage check when accessible."""
    monkeypatch.setattr("os.path.exists", lambda path: True)
    monkeypatch.setattr("os.path.isdir", lambda path: True)
    monkeypatch.setattr("builtins.open", MagicMock())
    monkeypatch.setattr("os.remove", MagicMock())
    
    checker = IntegrationHealthChecker(enable_artifact_storage=True)
    result = checker.check_artifact_storage()
    
    assert result.available is True
    assert result.version == "local"
    assert "accessible" in result.detail.lower()


def test_health_check_persistence_initialization(tmp_path):
    """Test initializing health check persistence."""
    db_path = tmp_path / "test_health.db"
    persistence = HealthCheckPersistence(db_path)
    
    assert str(persistence.db_path) == str(db_path)


def test_health_check_persistence_save_and_retrieve(tmp_path):
    """Test saving and retrieving a health check record."""
    db_path = tmp_path / "test_health.db"
    persistence = HealthCheckPersistence(db_path)
    
    record = HealthCheckRecord(
        check_name="test-check",
        available=True,
        version="1.0.0",
        detail="Test check",
        required=True,
    )
    
    persistence.save_record(record)
    
    retrieved = persistence.get_latest_record("test-check")
    
    assert retrieved is not None
    assert retrieved.check_name == "test-check"
    assert retrieved.available is True
    assert retrieved.version == "1.0.0"


def test_health_check_persistence_get_history(tmp_path):
    """Test getting history for a check."""
    db_path = tmp_path / "test_health.db"
    persistence = HealthCheckPersistence(db_path)
    
    for i in range(3):
        record = HealthCheckRecord(
            check_name="test-check",
            available=True,
            version=f"1.0.{i}",
            detail=f"Test check {i}",
            required=True,
        )
        persistence.save_record(record)
    
    history = persistence.get_history("test-check", limit=2)
    
    assert len(history) == 2
    assert history[0].version == "1.0.2"
    assert history[1].version == "1.0.1"


def test_health_check_persistence_get_summary(tmp_path):
    """Test getting a summary of health checks."""
    db_path = tmp_path / "test_health.db"
    persistence = HealthCheckPersistence(db_path)
    
    # Add some records
    for i in range(5):
        record = HealthCheckRecord(
            check_name="test-check",
            available=True,
            version=f"1.0.{i}",
            detail=f"Test check {i}",
            required=True,
        )
        persistence.save_record(record)
    
    summary = persistence.get_summary()
    
    # Debug output
    print(f"DEBUG: summary = {summary}")
    
    assert summary["total_checks"] == 5
    assert summary["available"] == 5
    assert summary["unavailable"] == 0
    assert summary["required_available"] == 5
    assert summary["required_unavailable"] == 0
    assert summary["overall_status"] == "ok"  # All required checks are available


def test_health_check_persistence_export_to_json(tmp_path):
    """Test exporting health check records to JSON."""
    import json
    db_path = tmp_path / "test_health.db"
    persistence = HealthCheckPersistence(db_path)
    
    record = HealthCheckRecord(
        check_name="test-check",
        available=True,
        version="1.0.0",
        detail="Test check",
        required=True,
    )
    persistence.save_record(record)
    
    output_path = tmp_path / "health_export.json"
    persistence.export_to_json(output_path)
    
    assert output_path.exists()
    
    with open(output_path) as f:
        data = json.load(f)
    
    assert len(data) == 1
    assert data[0]["check_name"] == "test-check"
    assert data[0]["available"] is True


def test_health_check_persistence_clear_history(tmp_path):
    """Test clearing health check history."""
    db_path = tmp_path / "test_health.db"
    persistence = HealthCheckPersistence(db_path)
    
    # Add some records
    for i in range(3):
        record = HealthCheckRecord(
            check_name="test-check",
            available=True,
            version=f"1.0.{i}",
            detail=f"Test check {i}",
            required=True,
        )
        persistence.save_record(record)
    
    assert persistence.get_summary()["total_checks"] == 3
    
    persistence.clear_history()
    
    assert persistence.get_summary()["total_checks"] == 0
