"""Tests for endpoint health check scheduling and environment validation."""
import asyncio
import gc
import json
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from orville_core import (
    EndpointEnvironmentValidator,
    EndpointHealthScheduler,
    EndpointHealthSchedulerManager,
    EndpointScheduleConfig,
    EndpointSchedulingError,
    EndpointValidationError,
    ScheduledEndpointCheck,
    EnvironmentConfig,
    ProviderEndpointSpec,
    LocalModelSpec,
    EndpointHealthStatus,
    ScheduleInterval,
)


def cleanup_scheduler(scheduler: EndpointHealthScheduler):
    """Helper to properly cleanup scheduler and database files on Windows."""
    scheduler.close()
    gc.collect()
    time.sleep(0.1)
    if scheduler.database_path.exists():
        scheduler.database_path.unlink(missing_ok=True)


# =============================================================================
# EndpointScheduleConfig Tests
# =============================================================================

def test_endpoint_schedule_config_creation():
    """Test creating EndpointScheduleConfig."""
    config = EndpointScheduleConfig(
        check_interval_seconds=120,
        failure_threshold=5,
        success_threshold=3,
        environment="production",
    )
    assert config.check_interval_seconds == 120
    assert config.failure_threshold == 5
    assert config.success_threshold == 3
    assert config.environment == "production"


def test_endpoint_schedule_config_to_dict():
    """Test EndpointScheduleConfig serialization."""
    config = EndpointScheduleConfig(
        check_interval_seconds=120,
        failure_threshold=5,
        environment="staging",
    )
    data = config.to_dict()
    assert data["check_interval_seconds"] == 120
    assert data["failure_threshold"] == 5
    assert data["environment"] == "staging"
    assert data["schedule_interval"] == "minutes"


def test_endpoint_schedule_config_from_dict():
    """Test EndpointScheduleConfig deserialization."""
    data = {
        "check_interval_seconds": 180,
        "failure_threshold": 5,
        "success_threshold": 3,
        "probe_timeout_seconds": 10.0,
        "alert_on_failure": True,
        "alert_on_degraded": False,
        "alert_on_recovery": True,
        "max_history_entries": 500,
        "enable_scheduling": True,
        "schedule_interval": "hourly",
        "environment": "production",
    }
    config = EndpointScheduleConfig.from_dict(data)
    assert config.check_interval_seconds == 180
    assert config.failure_threshold == 5
    assert config.schedule_interval == ScheduleInterval.HOURLY
    assert config.environment == "production"


# =============================================================================
# ScheduledEndpointCheck Tests
# =============================================================================

def test_scheduled_endpoint_check_creation():
    """Test creating ScheduledEndpointCheck."""
    config = EndpointScheduleConfig()
    check = ScheduledEndpointCheck(
        endpoint_url="https://example.test/v1",
        schedule_config=config,
        enabled=True,
    )
    assert check.endpoint_url == "https://example.test/v1"
    assert check.enabled is True
    assert check.consecutive_failures == 0
    assert check.consecutive_successes == 0


def test_scheduled_endpoint_check_to_dict():
    """Test ScheduledEndpointCheck serialization."""
    config = EndpointScheduleConfig()
    env_config = EnvironmentConfig.get_local()
    check = ScheduledEndpointCheck(
        endpoint_url="https://example.test/v1",
        schedule_config=config,
        environment_config=env_config,
        enabled=True,
        metadata={"provider": "test"},
    )
    data = check.to_dict()
    assert data["endpoint_url"] == "https://example.test/v1"
    assert data["enabled"] is True
    assert data["metadata"] == {"provider": "test"}
    assert data["environment_config"] is not None


# =============================================================================
# EndpointEnvironmentValidator Tests
# =============================================================================

def test_validator_validate_endpoint_url_valid():
    """Test validating a valid endpoint URL."""
    env_config = EnvironmentConfig.get_default()
    validator = EndpointEnvironmentValidator(env_config)

    is_valid, error = validator.validate_endpoint_url("https://example.test/v1")
    assert is_valid is True
    assert error == ""


def test_validator_validate_endpoint_url_invalid_scheme():
    """Test validating URL with invalid scheme."""
    env_config = EnvironmentConfig.get_default()
    validator = EndpointEnvironmentValidator(env_config)

    is_valid, error = validator.validate_endpoint_url("ftp://example.test/v1")
    assert is_valid is False
    assert "scheme" in error.lower()


def test_validator_validate_endpoint_url_private_network_not_allowed():
    """Test validating private network URL when not allowed."""
    env_config = EnvironmentConfig.get_default()  # allow_private_network=False
    validator = EndpointEnvironmentValidator(env_config)

    is_valid, error = validator.validate_endpoint_url("http://localhost:8080/v1")
    assert is_valid is False
    assert "private" in error.lower()


def test_validator_validate_endpoint_url_private_network_allowed():
    """Test validating private network URL when allowed."""
    env_config = EnvironmentConfig.get_local()  # allow_private_network=True
    validator = EndpointEnvironmentValidator(env_config)

    is_valid, error = validator.validate_endpoint_url("http://localhost:8080/v1")
    assert is_valid is True
    assert error == ""


def test_validator_validate_endpoint_url_allowed_hosts():
    """Test validating URL against allowed hosts."""
    env_config = EnvironmentConfig(
        name="test",
        allowed_hosts=("example.com", "api.example.com"),
    )
    validator = EndpointEnvironmentValidator(env_config)

    is_valid, error = validator.validate_endpoint_url("https://example.com/v1")
    assert is_valid is True

    is_valid, error = validator.validate_endpoint_url("https://notallowed.com/v1")
    assert is_valid is False
    assert "not in allowed hosts" in error


def test_validator_validate_endpoint_url_allowed_ports():
    """Test validating URL against allowed ports."""
    env_config = EnvironmentConfig(
        name="test",
        allowed_ports=(443, 8443),
    )
    validator = EndpointEnvironmentValidator(env_config)

    is_valid, error = validator.validate_endpoint_url("https://example.com/v1")
    assert is_valid is True  # 443 is allowed

    is_valid, error = validator.validate_endpoint_url("http://example.com:8080/v1")
    assert is_valid is False
    assert "port" in error.lower()


def test_validator_validate_provider_endpoint():
    """Test validating a provider endpoint spec."""
    env_config = EnvironmentConfig.get_default()
    validator = EndpointEnvironmentValidator(env_config)

    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
        environment="default",
    )

    is_valid, error = validator.validate_provider_endpoint(spec)
    assert is_valid is True
    assert error == ""


def test_validator_validate_provider_endpoint_environment_mismatch():
    """Test validating provider endpoint with environment mismatch."""
    env_config = EnvironmentConfig.get_default()
    validator = EndpointEnvironmentValidator(env_config)

    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
        environment="production",  # Mismatch with validator
    )

    is_valid, error = validator.validate_provider_endpoint(spec)
    assert is_valid is False
    assert "does not match" in error


def test_validator_validate_local_model():
    """Test validating a local model spec."""
    env_config = EnvironmentConfig.get_local()  # allow_private_network=True
    validator = EndpointEnvironmentValidator(env_config)

    # Create a temporary file to test with
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test model data")
        temp_path = Path(f.name)

    try:
        spec = LocalModelSpec(
            model_id="test-model",
            source_path=temp_path,
            checksum_sha256="a" * 64,
            file_format="gguf",
            environment="local",
        )

        is_valid, error = validator.validate_local_model(spec)
        assert is_valid is True
        assert error == ""
    finally:
        temp_path.unlink(missing_ok=True)


def test_validator_validate_local_model_not_allowed():
    """Test validating local model when not allowed."""
    env_config = EnvironmentConfig.get_production()  # allow_private_network=False
    validator = EndpointEnvironmentValidator(env_config)

    spec = LocalModelSpec(
        model_id="test-model",
        source_path=Path("/models/test.gguf"),
        checksum_sha256="a" * 64,
        file_format="gguf",
        environment="production",
    )

    is_valid, error = validator.validate_local_model(spec)
    assert is_valid is False
    assert "not allowed" in error.lower()


def test_validator_get_validation_summary():
    """Test getting validation summary."""
    env_config = EnvironmentConfig(
        name="test",
        allowed_hosts=("example.com",),
        allowed_ports=(443,),
        allow_private_network=True,
    )
    validator = EndpointEnvironmentValidator(env_config)

    summary = validator.get_validation_summary()
    assert summary["environment"] == "test"
    assert summary["allow_private_network"] is True
    assert "example.com" in summary["allowed_hosts"]
    assert 443 in summary["allowed_ports"]


def test_validator_is_private_ip():
    """Test private IP detection."""
    env_config = EnvironmentConfig.get_default()
    validator = EndpointEnvironmentValidator(env_config)

    assert validator._is_private_ip("localhost") is True
    assert validator._is_private_ip("127.0.0.1") is True
    assert validator._is_private_ip("192.168.1.1") is True
    assert validator._is_private_ip("10.0.0.1") is True
    assert validator._is_private_ip("172.16.0.1") is True
    assert validator._is_private_ip("172.31.255.255") is True
    assert validator._is_private_ip("example.com") is False
    assert validator._is_private_ip("8.8.8.8") is False


# =============================================================================
# EndpointHealthScheduler Tests
# =============================================================================

def test_endpoint_health_scheduler_creation():
    """Test creating EndpointHealthScheduler."""
    config = EndpointScheduleConfig()
    scheduler = EndpointHealthScheduler(
        config=config,
        database_path=Path(".orville/test_scheduler.db"),
    )
    assert scheduler.config == config
    assert scheduler._initialized is False


def test_endpoint_health_scheduler_initialize():
    """Test initializing the scheduler."""
    config = EndpointScheduleConfig()
    scheduler = EndpointHealthScheduler(
        config=config,
        database_path=Path(".orville/test_scheduler_init.db"),
    )
    scheduler.initialize()
    assert scheduler._initialized is True
    assert scheduler._monitor is not None

    cleanup_scheduler(scheduler)


def test_endpoint_health_scheduler_add_endpoint():
    """Test adding an endpoint to the scheduler."""
    config = EndpointScheduleConfig()
    scheduler = EndpointHealthScheduler(
        config=config,
        database_path=Path(".orville/test_scheduler_add.db"),
    )

    scheduler.add_endpoint("https://example.test/v1")
    assert len(scheduler.get_scheduled_checks()) == 1
    assert "https://example.test/v1" in scheduler.get_scheduled_checks()

    cleanup_scheduler(scheduler)


def test_endpoint_health_scheduler_add_endpoint_duplicate():
    """Test adding duplicate endpoint raises error."""
    config = EndpointScheduleConfig()
    scheduler = EndpointHealthScheduler(
        config=config,
        database_path=Path(".orville/test_scheduler_dup.db"),
    )

    scheduler.add_endpoint("https://example.test/v1")

    with pytest.raises(EndpointSchedulingError, match="already scheduled"):
        scheduler.add_endpoint("https://example.test/v1")

    cleanup_scheduler(scheduler)


def test_endpoint_health_scheduler_add_endpoint_validation_failure():
    """Test adding invalid endpoint raises validation error."""
    config = EndpointScheduleConfig()
    env_config = EnvironmentConfig.get_default()  # Private not allowed
    scheduler = EndpointHealthScheduler(
        config=config,
        database_path=Path(".orville/test_scheduler_val.db"),
        environment_config=env_config,
    )

    with pytest.raises(EndpointValidationError, match="Private network"):
        scheduler.add_endpoint("http://localhost:8080/v1")

    cleanup_scheduler(scheduler)


def test_endpoint_health_scheduler_remove_endpoint():
    """Test removing an endpoint from the scheduler."""
    config = EndpointScheduleConfig()
    scheduler = EndpointHealthScheduler(
        config=config,
        database_path=Path(".orville/test_scheduler_remove.db"),
    )

    scheduler.add_endpoint("https://example.test/v1")
    assert len(scheduler.get_scheduled_checks()) == 1

    result = scheduler.remove_endpoint("https://example.test/v1")
    assert result is True
    assert len(scheduler.get_scheduled_checks()) == 0

    # Removing non-existent endpoint returns False
    result = scheduler.remove_endpoint("https://notexist.test/v1")
    assert result is False

    cleanup_scheduler(scheduler)


def test_endpoint_health_scheduler_run_health_check():
    """Test running health check for an endpoint."""
    config = EndpointScheduleConfig()
    scheduler = EndpointHealthScheduler(
        config=config,
        database_path=Path(".orville/test_scheduler_run.db"),
    )

    scheduler.add_endpoint("https://example.test/v1")

    with patch("orville_core.endpoint_health.probe_endpoint") as mock_probe:
        mock_probe.return_value = type("Response", (), {"status": 200, "reachable": True})()
        health = scheduler.run_health_check("https://example.test/v1")

        assert health.endpoint_url == "https://example.test/v1"
        assert health.status == EndpointHealthStatus.HEALTHY

    cleanup_scheduler(scheduler)


def test_endpoint_health_scheduler_run_health_check_not_scheduled():
    """Test running health check for non-scheduled endpoint raises error."""
    config = EndpointScheduleConfig()
    scheduler = EndpointHealthScheduler(
        config=config,
        database_path=Path(".orville/test_scheduler_not_sched.db"),
    )

    with pytest.raises(EndpointSchedulingError, match="not scheduled"):
        scheduler.run_health_check("https://notexist.test/v1")

    cleanup_scheduler(scheduler)


def test_endpoint_health_scheduler_run_all_health_checks():
    """Test running health checks for all endpoints."""
    config = EndpointScheduleConfig()
    scheduler = EndpointHealthScheduler(
        config=config,
        database_path=Path(".orville/test_scheduler_run_all.db"),
    )

    scheduler.add_endpoint("https://example1.test/v1")
    scheduler.add_endpoint("https://example2.test/v1")

    with patch("orville_core.endpoint_health.probe_endpoint") as mock_probe:
        mock_probe.return_value = type("Response", (), {"status": 200, "reachable": True})()
        report = scheduler.run_all_health_checks()

        assert report.total_endpoints == 2
        assert report.healthy_count == 2

    cleanup_scheduler(scheduler)


def test_endpoint_health_scheduler_get_endpoint_health():
    """Test getting health for a specific endpoint."""
    config = EndpointScheduleConfig()
    scheduler = EndpointHealthScheduler(
        config=config,
        database_path=Path(".orville/test_scheduler_get_health.db"),
    )

    scheduler.add_endpoint("https://example.test/v1")

    with patch("orville_core.endpoint_health.probe_endpoint") as mock_probe:
        mock_probe.return_value = type("Response", (), {"status": 200, "reachable": True})()
        scheduler.run_all_health_checks()

        health = scheduler.get_endpoint_health("https://example.test/v1")
        assert health is not None
        assert health.endpoint_url == "https://example.test/v1"

    cleanup_scheduler(scheduler)


def test_endpoint_health_scheduler_get_all_health():
    """Test getting health for all endpoints."""
    config = EndpointScheduleConfig()
    scheduler = EndpointHealthScheduler(
        config=config,
        database_path=Path(".orville/test_scheduler_get_all.db"),
    )

    scheduler.add_endpoint("https://example1.test/v1")
    scheduler.add_endpoint("https://example2.test/v1")

    health = scheduler.get_all_health()
    assert len(health) == 2

    cleanup_scheduler(scheduler)


def test_endpoint_health_scheduler_get_health_report():
    """Test getting health report."""
    config = EndpointScheduleConfig()
    scheduler = EndpointHealthScheduler(
        config=config,
        database_path=Path(".orville/test_scheduler_report.db"),
    )

    scheduler.add_endpoint("https://example.test/v1")

    report = scheduler.get_health_report()
    assert report.total_endpoints == 1

    cleanup_scheduler(scheduler)


def test_endpoint_health_scheduler_get_endpoint_history():
    """Test getting endpoint health history."""
    config = EndpointScheduleConfig()
    scheduler = EndpointHealthScheduler(
        config=config,
        database_path=Path(".orville/test_scheduler_history.db"),
    )

    scheduler.add_endpoint("https://example.test/v1")

    with patch("orville_core.endpoint_health.probe_endpoint") as mock_probe:
        mock_probe.return_value = type("Response", (), {"status": 200, "reachable": True})()
        scheduler.run_all_health_checks()
        scheduler.run_all_health_checks()

        history = scheduler.get_endpoint_history("https://example.test/v1", limit=10)
        assert len(history) >= 1

    cleanup_scheduler(scheduler)


def test_endpoint_health_scheduler_export_health_report(tmp_path):
    """Test exporting health report to JSON."""
    config = EndpointScheduleConfig()
    scheduler = EndpointHealthScheduler(
        config=config,
        database_path=Path(".orville/test_scheduler_export.db"),
    )

    scheduler.add_endpoint("https://example.test/v1")

    output_path = tmp_path / "health_report.json"
    scheduler.export_health_report(output_path)

    assert output_path.exists()
    with open(output_path, "r") as f:
        data = json.load(f)
    assert data["total_endpoints"] == 1

    cleanup_scheduler(scheduler)


def test_endpoint_health_scheduler_get_status():
    """Test getting scheduler status."""
    config = EndpointScheduleConfig(environment="test")
    scheduler = EndpointHealthScheduler(
        config=config,
        database_path=Path(".orville/test_scheduler_status.db"),
    )

    scheduler.add_endpoint("https://example.test/v1")

    status = scheduler.get_status()
    assert status["initialized"] is True
    assert status["scheduled_endpoints"] == 1
    assert len(status["endpoints"]) == 1
    assert status["config"]["environment"] == "test"

    cleanup_scheduler(scheduler)


@pytest.mark.asyncio
async def test_endpoint_health_scheduler_start_stop_scheduling():
    """Test starting and stopping the scheduling loop."""
    config = EndpointScheduleConfig(enable_scheduling=True)
    scheduler = EndpointHealthScheduler(
        config=config,
        database_path=Path(".orville/test_scheduler_start_stop.db"),
    )

    await scheduler.start_scheduling()
    assert scheduler._running is True

    await scheduler.stop_scheduling()
    assert scheduler._running is False

    cleanup_scheduler(scheduler)


def test_endpoint_health_scheduler_close():
    """Test closing the scheduler."""
    config = EndpointScheduleConfig()
    scheduler = EndpointHealthScheduler(
        config=config,
        database_path=Path(".orville/test_scheduler_close.db"),
    )

    scheduler.initialize()
    assert scheduler._initialized is True

    scheduler.close()
    assert scheduler._initialized is False

    if scheduler.database_path.exists():
        scheduler.database_path.unlink(missing_ok=True)


# =============================================================================
# EndpointHealthSchedulerManager Tests
# =============================================================================

def test_scheduler_manager_creation():
    """Test creating EndpointHealthSchedulerManager."""
    manager = EndpointHealthSchedulerManager(base_path=Path(".orville/schedulers"))
    assert manager.base_path == Path(".orville/schedulers")
    assert len(manager._schedulers) == 0


def test_scheduler_manager_get_or_create_scheduler():
    """Test getting or creating a scheduler."""
    manager = EndpointHealthSchedulerManager(base_path=Path(".orville/test_manager"))

    scheduler = manager.get_or_create_scheduler("production")
    assert scheduler is not None
    assert scheduler.environment_config.name == "production"
    assert "production" in manager._schedulers

    # Get existing scheduler
    scheduler2 = manager.get_or_create_scheduler("production")
    assert scheduler2 is scheduler

    scheduler.close()
    if scheduler.database_path.exists():
        scheduler.database_path.unlink(missing_ok=True)


def test_scheduler_manager_get_scheduler():
    """Test getting a scheduler."""
    manager = EndpointHealthSchedulerManager(base_path=Path(".orville/test_manager_get"))

    # Get non-existent scheduler returns None
    scheduler = manager.get_scheduler("staging")
    assert scheduler is None

    # Create and get scheduler
    manager.get_or_create_scheduler("staging")
    scheduler = manager.get_scheduler("staging")
    assert scheduler is not None

    scheduler.close()
    if scheduler.database_path.exists():
        scheduler.database_path.unlink(missing_ok=True)


def test_scheduler_manager_remove_scheduler():
    """Test removing a scheduler."""
    manager = EndpointHealthSchedulerManager(base_path=Path(".orville/test_manager_remove"))

    manager.get_or_create_scheduler("test")
    assert "test" in manager._schedulers

    result = manager.remove_scheduler("test")
    assert result is True
    assert "test" not in manager._schedulers

    # Removing non-existent returns False
    result = manager.remove_scheduler("nonexistent")
    assert result is False


def test_scheduler_manager_get_all_schedulers():
    """Test getting all schedulers."""
    manager = EndpointHealthSchedulerManager(base_path=Path(".orville/test_manager_all"))

    manager.get_or_create_scheduler("env1")
    manager.get_or_create_scheduler("env2")

    schedulers = manager.get_all_schedulers()
    assert len(schedulers) == 2
    assert "env1" in schedulers
    assert "env2" in schedulers

    manager.close_all()
    for scheduler in schedulers.values():
        if scheduler.database_path.exists():
            scheduler.database_path.unlink(missing_ok=True)


def test_scheduler_manager_get_all_status():
    """Test getting status for all schedulers."""
    manager = EndpointHealthSchedulerManager(base_path=Path(".orville/test_manager_status"))

    scheduler1 = manager.get_or_create_scheduler("env1")
    scheduler2 = manager.get_or_create_scheduler("env2")

    scheduler1.add_endpoint("https://example1.test/v1")
    scheduler2.add_endpoint("https://example2.test/v1")

    all_status = manager.get_all_status()
    assert len(all_status) == 2
    assert all_status["env1"]["scheduled_endpoints"] == 1
    assert all_status["env2"]["scheduled_endpoints"] == 1

    manager.close_all()
    for scheduler in [scheduler1, scheduler2]:
        if scheduler.database_path.exists():
            scheduler.database_path.unlink(missing_ok=True)


def test_scheduler_manager_close_all():
    """Test closing all schedulers."""
    manager = EndpointHealthSchedulerManager(base_path=Path(".orville/test_manager_close"))

    manager.get_or_create_scheduler("env1")
    manager.get_or_create_scheduler("env2")

    assert len(manager._schedulers) == 2

    manager.close_all()

    assert len(manager._schedulers) == 0


# =============================================================================
# Integration Tests
# =============================================================================

def test_scheduler_integration_with_monitor():
    """Test integration between scheduler and monitor."""
    config = EndpointScheduleConfig()
    scheduler = EndpointHealthScheduler(
        config=config,
        database_path=Path(".orville/test_integration.db"),
    )

    # Add endpoint
    scheduler.add_endpoint("https://example.test/v1")

    # Run health check
    with patch("orville_core.endpoint_health.probe_endpoint") as mock_probe:
        mock_probe.return_value = type("Response", (), {"status": 200, "reachable": True})()
        health = scheduler.run_health_check("https://example.test/v1")

    # Verify health is persisted
    health2 = scheduler.get_endpoint_health("https://example.test/v1")
    assert health2 is not None
    assert health2.endpoint_url == health.endpoint_url

    # Get history
    history = scheduler.get_endpoint_history("https://example.test/v1")
    assert len(history) >= 1

    cleanup_scheduler(scheduler)


def test_scheduler_with_different_environments():
    """Test scheduler with different environment configurations."""
    manager = EndpointHealthSchedulerManager(base_path=Path(".orville/test_envs"))

    # Create schedulers for different environments
    local_scheduler = manager.get_or_create_scheduler("local")
    prod_scheduler = manager.get_or_create_scheduler("production")

    # Verify environment configs
    assert local_scheduler.environment_config.allow_private_network is True
    assert prod_scheduler.environment_config.allow_private_network is False

    # Local scheduler should allow localhost
    local_scheduler.add_endpoint("http://localhost:8080/v1")
    assert len(local_scheduler.get_scheduled_checks()) == 1

    # Production scheduler should reject localhost
    with pytest.raises(EndpointValidationError):
        prod_scheduler.add_endpoint("http://localhost:8080/v1")

    manager.close_all()
    for scheduler in [local_scheduler, prod_scheduler]:
        if scheduler.database_path.exists():
            scheduler.database_path.unlink(missing_ok=True)


def test_scheduler_consecutive_failures_tracking():
    """Test tracking of consecutive failures."""
    config = EndpointScheduleConfig()
    scheduler = EndpointHealthScheduler(
        config=config,
        database_path=Path(".orville/test_failures.db"),
    )

    scheduler.add_endpoint("https://example.test/v1")

    # Simulate failures
    with patch("orville_core.endpoint_health.probe_endpoint") as mock_probe:
        mock_probe.return_value = type("Response", (), {"status": None, "reachable": False, "detail": "Connection refused"})()
        
        scheduler.run_health_check("https://example.test/v1")
        scheduler.run_health_check("https://example.test/v1")

    # Check scheduled check tracking
    scheduled = scheduler.get_scheduled_checks()["https://example.test/v1"]
    assert scheduled.consecutive_failures == 2
    assert scheduled.consecutive_successes == 0

    # Simulate success
    with patch("orville_core.endpoint_health.probe_endpoint") as mock_probe:
        mock_probe.return_value = type("Response", (), {"status": 200, "reachable": True})()
        scheduler.run_health_check("https://example.test/v1")

    scheduled = scheduler.get_scheduled_checks()["https://example.test/v1"]
    assert scheduled.consecutive_failures == 0
    assert scheduled.consecutive_successes == 1

    cleanup_scheduler(scheduler)


def test_scheduler_metadata_tracking():
    """Test metadata tracking for scheduled endpoints."""
    config = EndpointScheduleConfig()
    scheduler = EndpointHealthScheduler(
        config=config,
        database_path=Path(".orville/test_metadata.db"),
    )

    metadata = {"provider": "openai", "region": "us-east-1", "priority": "high"}
    scheduler.add_endpoint(
        "https://api.openai.test/v1",
        metadata=metadata,
    )

    scheduled = scheduler.get_scheduled_checks()["https://api.openai.test/v1"]
    assert scheduled.metadata == metadata

    cleanup_scheduler(scheduler)
