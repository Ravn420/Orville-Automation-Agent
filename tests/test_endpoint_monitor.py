"""Tests for persistent endpoint monitoring."""
import gc
import json
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from orville_core import (
    EndpointMonitor,
    EndpointMonitorConfig,
    EndpointMonitorError,
    EndpointMonitorPersistenceError,
    EndpointHealthStatus,
    EnvironmentConfig,
    ProviderEndpointSpec,
)


def cleanup_monitor(monitor: EndpointMonitor, path: Path):
    """Helper to properly cleanup monitor and database file on Windows."""
    monitor.close()
    # Force garbage collection to release file handles on Windows
    gc.collect()
    # Small delay to ensure file is released
    time.sleep(0.1)
    path.unlink(missing_ok=True)


def test_endpoint_monitor_config_creation():
    """Test creating EndpointMonitorConfig."""
    config = EndpointMonitorConfig(
        database_path=Path(".orville/endpoint_monitor.db"),
        check_interval_seconds=120,
        failure_threshold=5,
        success_threshold=3,
    )
    assert config.check_interval_seconds == 120
    assert config.failure_threshold == 5


def test_endpoint_monitor_initialization():
    """Test initializing endpoint monitor."""
    config = EndpointMonitorConfig(
        database_path=Path(".orville/test_monitor.db"),
    )
    monitor = EndpointMonitor(config)
    assert monitor._initialized is False


def test_endpoint_monitor_initialize():
    """Test initializing monitor database."""
    config = EndpointMonitorConfig(
        database_path=Path(".orville/test_monitor_init.db"),
    )
    monitor = EndpointMonitor(config)
    monitor.initialize()
    assert monitor._initialized is True

    # Clean up
    cleanup_monitor(monitor, config.database_path)


def test_endpoint_monitor_add_endpoint():
    """Test adding endpoint to monitor."""
    config = EndpointMonitorConfig(
        database_path=Path(".orville/test_monitor_add.db"),
    )
    monitor = EndpointMonitor(config)
    monitor.initialize()

    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
    )
    monitor.add_endpoint("https://example.test/v1")
    assert len(monitor.get_all_health()) == 1

    # Clean up
    cleanup_monitor(monitor, config.database_path)


def test_endpoint_monitor_remove_endpoint():
    """Test removing endpoint from monitor."""
    config = EndpointMonitorConfig(
        database_path=Path(".orville/test_monitor_remove.db"),
    )
    monitor = EndpointMonitor(config)
    monitor.initialize()

    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
    )
    monitor.add_endpoint("https://example.test/v1")
    assert len(monitor.get_all_health()) == 1

    result = monitor.remove_endpoint("https://example.test/v1")
    assert result is True
    assert len(monitor.get_all_health()) == 0

    # Clean up
    cleanup_monitor(monitor, config.database_path)


def test_endpoint_monitor_get_endpoint_health():
    """Test getting endpoint health."""
    config = EndpointMonitorConfig(
        database_path=Path(".orville/test_monitor_get.db"),
    )
    monitor = EndpointMonitor(config)
    monitor.initialize()

    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
    )
    monitor.add_endpoint("https://example.test/v1")
    health = monitor.get_endpoint_health("https://example.test/v1")
    assert health is not None
    assert health.endpoint_url == "https://example.test/v1"

    # Clean up
    cleanup_monitor(monitor, config.database_path)


def test_endpoint_monitor_run_probes():
    """Test running probes with persistence."""
    config = EndpointMonitorConfig(
        database_path=Path(".orville/test_monitor_run.db"),
    )
    monitor = EndpointMonitor(config)
    monitor.initialize()

    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
    )
    monitor.add_endpoint("https://example.test/v1")

    with patch("orville_core.endpoint_health.probe_endpoint") as mock_probe:
        mock_probe.return_value = type("Response", (), {"status": 200, "reachable": True})()
        report = monitor.run_probes()

        assert report.total_endpoints == 1
        assert report.healthy_count == 1

    # Verify persistence
    health = monitor.get_endpoint_health("https://example.test/v1")
    assert health is not None
    assert health.probe_count == 1

    # Clean up
    cleanup_monitor(monitor, config.database_path)


def test_endpoint_monitor_persistence_error():
    """Test handling persistence errors."""
    config = EndpointMonitorConfig(
        database_path=Path(".orville/test_monitor_error.db"),
    )
    monitor = EndpointMonitor(config)
    monitor.initialize()

    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
    )
    monitor.add_endpoint("https://example.test/v1")

    # Simulate database error
    with patch("sqlite3.connect") as mock_connect:
        mock_connect.side_effect = sqlite3.Error("Database error")
        with pytest.raises(EndpointMonitorPersistenceError, match="Failed to persist"):
            monitor.run_probes()

    # Clean up
    cleanup_monitor(monitor, config.database_path)


def test_endpoint_monitor_get_history():
    """Test getting health history."""
    config = EndpointMonitorConfig(
        database_path=Path(".orville/test_monitor_history.db"),
    )
    monitor = EndpointMonitor(config)
    monitor.initialize()

    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
    )
    monitor.add_endpoint("https://example.test/v1")

    with patch("orville_core.endpoint_health.probe_endpoint") as mock_probe:
        mock_probe.return_value = type("Response", (), {"status": 200, "reachable": True})()
        monitor.run_probes()

    history = monitor.get_history("https://example.test/v1", limit=10)
    assert len(history) >= 1
    assert history[0]["endpoint_url"] == "https://example.test/v1"
    assert history[0]["status"] == "healthy"

    # Clean up
    cleanup_monitor(monitor, config.database_path)


def test_endpoint_monitor_get_summary():
    """Test getting monitoring summary."""
    import uuid
    config = EndpointMonitorConfig(
        database_path=Path(f".orville/test_monitor_summary_{uuid.uuid4().hex}.db"),
    )
    monitor = EndpointMonitor(config)
    monitor.initialize()

    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
    )
    monitor.add_endpoint("https://example.test/v1")

    # Run a probe first to populate the database
    with patch("orville_core.endpoint_health.probe_endpoint") as mock_probe:
        mock_probe.return_value = type("Response", (), {"status": 200, "reachable": True})()
        monitor.run_probes()

    summary = monitor.get_summary()
    assert summary["total_endpoints"] == 1
    assert summary["healthy_count"] == 1

    # Clean up
    cleanup_monitor(monitor, config.database_path)


def test_endpoint_monitor_get_alerts():
    """Test getting recent alerts."""
    config = EndpointMonitorConfig(
        database_path=Path(".orville/test_monitor_alerts.db"),
    )
    monitor = EndpointMonitor(config)
    monitor.initialize()

    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
    )
    monitor.add_endpoint("https://example.test/v1")

    with patch("orville_core.endpoint_health.probe_endpoint") as mock_probe:
        # Mock returns unreachable which triggers unhealthy status
        mock_probe.return_value = type("Response", (), {"status": None, "reachable": False, "detail": "Connection refused"})()
        monitor.run_probes()

    alerts = monitor.get_alerts(hours=24)
    assert len(alerts) >= 1
    assert alerts[0]["endpoint_url"] == "https://example.test/v1"
    assert alerts[0]["status"] == "unhealthy"

    # Clean up
    cleanup_monitor(monitor, config.database_path)


def test_endpoint_monitor_export_report():
    """Test exporting health report to JSON."""
    config = EndpointMonitorConfig(
        database_path=Path(".orville/test_monitor_export.db"),
    )
    monitor = EndpointMonitor(config)
    monitor.initialize()

    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
    )
    monitor.add_endpoint("https://example.test/v1")

    with patch("orville_core.endpoint_health.probe_endpoint") as mock_probe:
        mock_probe.return_value = type("Response", (), {"status": 200, "reachable": True})()
        monitor.run_probes()

    output_path = Path(".orville/test_report.json")
    monitor.export_report(output_path)
    assert output_path.exists()

    # Verify content
    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["total_endpoints"] == 1
    assert data["healthy_count"] == 1

    # Clean up
    output_path.unlink(missing_ok=True)
    cleanup_monitor(monitor, config.database_path)


def test_endpoint_monitor_import_config():
    """Test importing monitoring configuration."""
    config = EndpointMonitorConfig(
        database_path=Path(".orville/test_monitor_import.db"),
    )
    monitor = EndpointMonitor(config)
    monitor.initialize()

    # Create a config file
    config_data = {
        "database_path": ".orville/test_monitor_import.db",
        "check_interval_seconds": 180,
        "failure_threshold": 5,
        "success_threshold": 3,
        "probe_timeout_seconds": 10.0,
        "alert_on_failure": True,
        "alert_on_degraded": True,
        "alert_on_recovery": True,
        "max_history_entries": 500,
    }
    config_path = Path(".orville/test_config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f)

    # Import config
    monitor.import_config(config_path)
    assert monitor.config.check_interval_seconds == 180
    assert monitor.config.failure_threshold == 5

    # Clean up
    config_path.unlink(missing_ok=True)
    cleanup_monitor(monitor, config.database_path)


def test_endpoint_monitor_multiple_endpoints():
    """Test monitoring multiple endpoints."""
    config = EndpointMonitorConfig(
        database_path=Path(".orville/test_monitor_multi.db"),
    )
    monitor = EndpointMonitor(config)
    monitor.initialize()

    urls = [
        "https://example1.test/v1",
        "https://example2.test/v1",
        "https://example3.test/v1",
    ]

    for url in urls:
        monitor.add_endpoint(url)

    assert len(monitor.get_all_health()) == 3

    with patch("orville_core.endpoint_health.probe_endpoint") as mock_probe:
        mock_probe.return_value = type("Response", (), {"status": 200, "reachable": True})()
        report = monitor.run_probes()

        assert report.total_endpoints == 3
        assert report.healthy_count == 3

    # Clean up
    cleanup_monitor(monitor, config.database_path)


def test_endpoint_monitor_persistence_after_multiple_probes():
    """Test that persistence works correctly after multiple probes."""
    config = EndpointMonitorConfig(
        database_path=Path(".orville/test_monitor_multi_probe.db"),
    )
    monitor = EndpointMonitor(config)
    monitor.initialize()

    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
    )
    monitor.add_endpoint("https://example.test/v1")

    with patch("orville_core.endpoint_health.probe_endpoint") as mock_probe:
        # First probe
        mock_probe.return_value = type("Response", (), {"status": 200, "reachable": True})()
        report = monitor.run_probes()
        assert report.healthy_count == 1

        # Second probe
        mock_probe.return_value = type("Response", (), {"status": 200, "reachable": True})()
        report = monitor.run_probes()
        assert report.healthy_count == 1

    # Verify persistence
    health = monitor.get_endpoint_health("https://example.test/v1")
    assert health.probe_count == 2
    assert health.consecutive_successes == 2

    # Clean up
    cleanup_monitor(monitor, config.database_path)


def test_endpoint_monitor_history_trimming():
    """Test that history is trimmed to max entries."""
    config = EndpointMonitorConfig(
        database_path=Path(".orville/test_monitor_trim.db"),
        max_history_entries=10,
    )
    monitor = EndpointMonitor(config)
    monitor.initialize()

    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
    )
    monitor.add_endpoint("https://example.test/v1")

    with patch("orville_core.endpoint_health.probe_endpoint") as mock_probe:
        # Run multiple probes
        for _ in range(20):
            mock_probe.return_value = type("Response", (), {"status": 200, "reachable": True})()
            monitor.run_probes()

    history = monitor.get_history("https://example.test/v1", limit=100)
    assert len(history) <= 10  # Should be trimmed

    # Clean up
    cleanup_monitor(monitor, config.database_path)


def test_endpoint_monitor_config_persistence():
    """Test that configuration is persisted correctly."""
    config = EndpointMonitorConfig(
        database_path=Path(".orville/test_monitor_config.db"),
        check_interval_seconds=180,
        failure_threshold=5,
    )
    monitor = EndpointMonitor(config)
    monitor.initialize()

    # Verify config is persisted
    conn = sqlite3.connect(config.database_path)
    try:
        cursor = conn.execute("SELECT value FROM endpoint_monitor_config WHERE key = 'check_interval_seconds'")
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == "180"
    finally:
        conn.close()

    # Clean up
    cleanup_monitor(monitor, config.database_path)
