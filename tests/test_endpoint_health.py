"""Tests for endpoint health monitoring system."""
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from orville_core import (
    EndpointHealth,
    EndpointHealthReport,
    EndpointHealthStatus,
    EndpointHealthMonitor,
    EndpointConfigError,
    EnvironmentConfig,
    LocalModelSpec,
    ProviderEndpointSpec,
)


def test_endpoint_health_status_enum():
    """Test that all health status values are valid."""
    assert EndpointHealthStatus.HEALTHY.value == "healthy"
    assert EndpointHealthStatus.DEGRADED.value == "degraded"
    assert EndpointHealthStatus.UNHEALTHY.value == "unhealthy"
    assert EndpointHealthStatus.UNKNOWN.value == "unknown"


def test_endpoint_health_to_dict():
    """Test EndpointHealth serialization to dictionary."""
    health = EndpointHealth(
        endpoint_url="https://example.test/v1",
        status=EndpointHealthStatus.HEALTHY,
        last_probed=datetime.now(),
        consecutive_failures=0,
        consecutive_successes=5,
        average_response_time_ms=150.0,
        probe_count=5,
        last_error=None,
    )
    data = health.to_dict()
    assert data["endpoint_url"] == "https://example.test/v1"
    assert data["status"] == "healthy"
    assert data["consecutive_successes"] == 5
    assert data["average_response_time_ms"] == 150.0


def test_endpoint_health_redacted():
    """Test EndpointHealth redaction."""
    health = EndpointHealth(
        endpoint_url="https://example.test/v1",
        status=EndpointHealthStatus.HEALTHY,
        last_probed=datetime.now(),
        consecutive_failures=0,
        consecutive_successes=5,
        average_response_time_ms=150.0,
        probe_count=5,
        last_error=None,
        metadata={"api_key_reference": "secret://test", "custom": "value"},
    )
    redacted = health.redacted()
    assert redacted["endpoint_url"] == "https://example.test/v1"
    assert redacted["metadata"]["api_key_reference"] == "secret://test"  # Should be preserved
    assert redacted["metadata"]["custom"] == "value"
    assert redacted["metadata"]["custom"] == "value"


def test_endpoint_health_report_to_dict():
    """Test EndpointHealthReport serialization."""
    report = EndpointHealthReport(
        environment="test",
        timestamp=datetime.now(),
        total_endpoints=3,
        healthy_count=2,
        degraded_count=1,
        unhealthy_count=0,
        unknown_count=0,
        overall_status=EndpointHealthStatus.HEALTHY,
    )
    data = report.to_dict()
    assert data["environment"] == "test"
    assert data["total_endpoints"] == 3
    assert data["healthy_count"] == 2
    assert data["overall_status"] == "healthy"


def test_endpoint_health_report_get_summary():
    """Test EndpointHealthReport summary generation."""
    report = EndpointHealthReport(
        environment="test",
        timestamp=datetime.now(),
        total_endpoints=3,
        healthy_count=2,
        degraded_count=1,
        unhealthy_count=0,
        unknown_count=0,
        overall_status=EndpointHealthStatus.HEALTHY,
    )
    summary = report.get_summary()
    assert summary["environment"] == "test"
    assert summary["overall_status"] == "healthy"
    assert summary["summary"]["total"] == 3
    assert summary["summary"]["healthy"] == 2


def test_endpoint_health_monitor_add_endpoint():
    """Test adding endpoints to monitor."""
    monitor = EndpointHealthMonitor()
    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
    )
    monitor.add_endpoint(spec)
    assert len(monitor.get_all_health()) == 1


def test_endpoint_health_monitor_duplicate_endpoint():
    """Test that duplicate endpoints are rejected."""
    monitor = EndpointHealthMonitor()
    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
    )
    monitor.add_endpoint(spec)
    with pytest.raises(ValueError, match="already being monitored"):
        monitor.add_endpoint(spec)


def test_endpoint_health_monitor_remove_endpoint():
    """Test removing endpoints from monitor."""
    monitor = EndpointHealthMonitor()
    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
    )
    monitor.add_endpoint(spec)
    assert len(monitor.get_all_health()) == 1
    assert monitor.remove_endpoint("https://example.test/v1")
    assert len(monitor.get_all_health()) == 0


def test_endpoint_health_monitor_get_endpoint_health():
    """Test getting health for specific endpoint."""
    monitor = EndpointHealthMonitor()
    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
    )
    monitor.add_endpoint(spec)
    health = monitor.get_endpoint_health("https://example.test/v1")
    assert health is not None
    assert health.endpoint_url == "https://example.test/v1"


def test_endpoint_health_monitor_run_probes_success():
    """Test running probes on reachable endpoint."""
    monitor = EndpointHealthMonitor()
    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
    )
    monitor.add_endpoint(spec)

    with patch("orville_core.endpoint_health.probe_endpoint") as mock_probe:
        # Create a proper mock response object with reachable attribute
        mock_response = type("Response", (), {"status": 200, "reachable": True})()
        mock_probe.return_value = mock_response
        report = monitor.run_probes()

        assert report.total_endpoints == 1
        assert report.healthy_count == 1
        assert report.unhealthy_count == 0
        # Verify probe was called
        assert mock_probe.called


def test_endpoint_health_monitor_run_probes_failure():
    """Test running probes on unreachable endpoint."""
    monitor = EndpointHealthMonitor()
    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
    )
    monitor.add_endpoint(spec)

    with patch("orville_core.endpoint_probe.probe_endpoint") as mock_probe:
        mock_probe.return_value = type("Response", (), {"status": None, "detail": "Connection refused"})()
        report = monitor.run_probes()

        assert report.total_endpoints == 1
        assert report.healthy_count == 0
        assert report.unhealthy_count == 1


def test_endpoint_health_monitor_start_stop():
    """Test starting and stopping monitoring."""
    monitor = EndpointHealthMonitor()
    monitor.start_monitoring()
    assert monitor._running is True
    monitor.stop_monitoring()
    assert monitor._running is False


def test_endpoint_health_monitor_get_report():
    """Test getting current report without running probes."""
    monitor = EndpointHealthMonitor()
    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
    )
    monitor.add_endpoint(spec)
    report = monitor.get_report()
    assert report.total_endpoints == 1


def test_environment_config_from_dict():
    """Test creating EnvironmentConfig from dictionary."""
    config = EnvironmentConfig.from_dict({
        "name": "test",
        "timeout_multiplier": 2.0,
        "max_retries": 5,
    })
    assert config.name == "test"
    assert config.timeout_multiplier == 2.0
    assert config.max_retries == 5


def test_environment_config_validation():
    """Test EnvironmentConfig validation."""
    from orville_core.endpoint_config import EnvironmentError
    with pytest.raises(EnvironmentError, match="timeout_multiplier must be positive"):
        EnvironmentConfig(name="test", timeout_multiplier=0.0)

    with pytest.raises(EnvironmentError, match="max_retries must be non-negative"):
        EnvironmentConfig(name="test", max_retries=-1)


def test_environment_config_to_dict():
    """Test EnvironmentConfig serialization."""
    config = EnvironmentConfig(
        name="test",
        allowed_hosts=("example.com", "test.com"),
        timeout_multiplier=1.5,
    )
    data = config.to_dict()
    assert data["name"] == "test"
    assert data["timeout_multiplier"] == 1.5
    assert data["allowed_hosts"] == ["example.com", "test.com"]


def test_environment_config_get_default():
    """Test getting default environment config."""
    config = EnvironmentConfig.get_default()
    assert config.name == "default"
    assert config.timeout_multiplier == 1.0


def test_environment_config_get_local():
    """Test getting local environment config."""
    config = EnvironmentConfig.get_local()
    assert config.name == "local"
    assert config.allow_private_network is True
    assert config.timeout_multiplier == 0.5


def test_environment_config_get_production():
    """Test getting production environment config."""
    config = EnvironmentConfig.get_production()
    assert config.name == "production"
    assert config.timeout_multiplier == 1.5
    assert config.max_retries == 3


def test_provider_endpoint_spec_with_environment():
    """Test ProviderEndpointSpec with environment configuration."""
    env_config = EnvironmentConfig(
        name="production",
        timeout_multiplier=1.5,
    )
    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
        environment="production",
        environment_config=env_config,
    )
    assert spec.environment == "production"
    assert spec.get_effective_timeout() == 90.0  # 60s * 1.5


def test_provider_endpoint_spec_without_environment():
    """Test ProviderEndpointSpec without environment configuration."""
    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
    )
    assert spec.get_effective_timeout() == 60.0


def test_local_model_spec_with_environment():
    """Test LocalModelSpec with environment configuration."""
    env_config = EnvironmentConfig(
        name="local",
        timeout_multiplier=0.5,
    )
    spec = LocalModelSpec(
        model_id="test-model",
        source_path=Path("/models/test.gguf"),
        checksum_sha256="a" * 64,
        file_format="gguf",
        environment="local",
        environment_config=env_config,
    )
    assert spec.environment == "local"
    assert spec.get_effective_timeout() == 2.5  # 5s * 0.5


def test_local_model_spec_without_environment():
    """Test LocalModelSpec without environment configuration."""
    spec = LocalModelSpec(
        model_id="test-model",
        source_path=Path("/models/test.gguf"),
        checksum_sha256="a" * 64,
        file_format="gguf",
    )
    assert spec.get_effective_timeout() == 5.0


def test_endpoint_health_monitor_with_local_model():
    """Test monitoring local model endpoints."""
    monitor = EndpointHealthMonitor()
    spec = LocalModelSpec(
        model_id="test-model",
        source_path=Path("/models/test.gguf"),
        checksum_sha256="a" * 64,
        file_format="gguf",
    )
    monitor.add_endpoint(spec)
    assert len(monitor.get_all_health()) == 1


def test_endpoint_health_monitor_deterministic_status():
    """Test that endpoint status is determined correctly."""
    monitor = EndpointHealthMonitor()

    # Add healthy endpoint
    spec1 = ProviderEndpointSpec(
        provider_id="test1",
        display_name="Test 1",
        provider_type="cloud",
        endpoint_url="https://example1.test/v1",
        model_identifier="model",
        protocol="openai",
    )
    monitor.add_endpoint(spec1)

    # Add unhealthy endpoint
    spec2 = ProviderEndpointSpec(
        provider_id="test2",
        display_name="Test 2",
        provider_type="cloud",
        endpoint_url="https://example2.test/v1",
        model_identifier="model",
        protocol="openai",
    )
    monitor.add_endpoint(spec2)

    with patch("orville_core.endpoint_health.probe_endpoint") as mock_probe:
        mock_probe.return_value = type("Response", (), {"status": 200, "reachable": True})()
        report = monitor.run_probes()

        assert report.overall_status == EndpointHealthStatus.HEALTHY
        assert report.healthy_count == 2
        assert report.unhealthy_count == 0


def test_endpoint_health_monitor_mixed_status():
    """Test endpoint status with mixed healthy/unhealthy endpoints."""
    monitor = EndpointHealthMonitor()

    spec1 = ProviderEndpointSpec(
        provider_id="test1",
        display_name="Test 1",
        provider_type="cloud",
        endpoint_url="https://example1.test/v1",
        model_identifier="model",
        protocol="openai",
    )
    monitor.add_endpoint(spec1)

    spec2 = ProviderEndpointSpec(
        provider_id="test2",
        display_name="Test 2",
        provider_type="cloud",
        endpoint_url="https://example2.test/v1",
        model_identifier="model",
        protocol="openai",
    )
    monitor.add_endpoint(spec2)

    with patch("orville_core.endpoint_health.probe_endpoint") as mock_probe:
        mock_probe.return_value = type("Response", (), {"status": 200, "reachable": True})()
        report = monitor.run_probes()

        assert report.overall_status == EndpointHealthStatus.HEALTHY


def test_endpoint_health_monitor_consecutive_failures():
    """Test consecutive failure tracking."""
    monitor = EndpointHealthMonitor()
    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
    )
    monitor.add_endpoint(spec)

    with patch("orville_core.endpoint_probe.probe_endpoint") as mock_probe:
        # First probe fails
        mock_probe.return_value = type("Response", (), {"status": None, "detail": "Connection refused"})()
        report = monitor.run_probes()
        health = monitor.get_endpoint_health("https://example.test/v1")
        assert health.consecutive_failures == 1
        assert health.status == EndpointHealthStatus.UNHEALTHY

        # Second probe fails
        mock_probe.return_value = type("Response", (), {"status": None, "detail": "Connection refused"})()
        report = monitor.run_probes()
        health = monitor.get_endpoint_health("https://example.test/v1")
        assert health.consecutive_failures == 2


def test_endpoint_health_monitor_consecutive_successes():
    """Test consecutive success tracking."""
    monitor = EndpointHealthMonitor()
    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
    )
    monitor.add_endpoint(spec)

    with patch("orville_core.endpoint_health.probe_endpoint") as mock_probe:
        # First probe succeeds
        mock_probe.return_value = type("Response", (), {"status": 200, "reachable": True})()
        report = monitor.run_probes()
        health = monitor.get_endpoint_health("https://example.test/v1")
        assert health.consecutive_successes == 1
        assert health.status == EndpointHealthStatus.HEALTHY

        # Second probe succeeds
        mock_probe.return_value = type("Response", (), {"status": 200, "reachable": True})()
        report = monitor.run_probes()
        health = monitor.get_endpoint_health("https://example.test/v1")
        assert health.consecutive_successes == 2
