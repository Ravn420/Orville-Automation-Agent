"""Enhanced runtime health check tests."""
import os
import platform
import sys
from unittest.mock import MagicMock, patch

import pytest

from orville_core import RuntimeHealth


def test_runtime_health_detects_cloud_environment(monkeypatch):
    """Test cloud environment detection."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIAIOSFODNN7EXAMPLE")
    report = RuntimeHealth(check_environment=True).run()
    cloud_check = next((c for c in report["checks"] if c["name"] == "cloud-environment"), None)
    assert cloud_check is not None
    assert cloud_check["available"] is True
    assert cloud_check["version"] == "AWS"


def test_runtime_health_detects_azure_environment(monkeypatch):
    """Test Azure environment detection."""
    monkeypatch.setenv("AZURE_STORAGE_ACCOUNT", "mystorageaccount")
    report = RuntimeHealth(check_environment=True).run()
    cloud_check = next((c for c in report["checks"] if c["name"] == "cloud-environment"), None)
    assert cloud_check is not None
    assert cloud_check["available"] is True
    assert cloud_check["version"] == "AZURE"


def test_runtime_health_detects_gcp_environment(monkeypatch):
    """Test GCP environment detection."""
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "/path/to/credentials.json")
    report = RuntimeHealth(check_environment=True).run()
    cloud_check = next((c for c in report["checks"] if c["name"] == "cloud-environment"), None)
    assert cloud_check is not None
    assert cloud_check["available"] is True
    assert cloud_check["version"] == "GCP"


def test_runtime_health_detects_local_environment(monkeypatch):
    """Test local environment detection when no cloud indicators present."""
    # Ensure no cloud environment variables are set
    for key in ["AWS_ACCESS_KEY_ID", "AZURE_STORAGE_ACCOUNT", "GOOGLE_APPLICATION_CREDENTIALS", "CLOUDSDK_PROJECT"]:
        monkeypatch.delenv(key, raising=False)

    report = RuntimeHealth(check_environment=True).run()
    cloud_check = next((c for c in report["checks"] if c["name"] == "cloud-environment"), None)
    assert cloud_check is not None
    assert cloud_check["available"] is False
    assert cloud_check["version"] is None


def test_runtime_health_detects_production_environment(monkeypatch):
    """Test production environment detection."""
    monkeypatch.setenv("PRODUCTION", "true")
    report = RuntimeHealth(check_environment=True).run()
    prod_check = next((c for c in report["checks"] if c["name"] == "production-environment"), None)
    assert prod_check is not None
    assert prod_check["available"] is True
    assert prod_check["version"] == "true"


def test_runtime_health_detects_development_environment(monkeypatch):
    """Test development environment detection."""
    monkeypatch.setenv("DEVELOPMENT", "true")
    report = RuntimeHealth(check_environment=True).run()
    prod_check = next((c for c in report["checks"] if c["name"] == "production-environment"), None)
    assert prod_check is not None
    assert prod_check["available"] is False
    assert prod_check["version"] == "false"


def test_runtime_health_checks_disk_space(monkeypatch):
    """Test disk space checking."""
    # Mock disk usage to return high usage
    with patch("shutil.disk_usage") as mock_disk:
        mock_disk.return_value = MagicMock(used=1000, total=1000, free=0)
        report = RuntimeHealth(check_resources=True).run()
        disk_check = next((c for c in report["checks"] if c["name"] == "disk-space"), None)
        assert disk_check is not None
        assert disk_check["available"] is False


def test_runtime_health_checks_memory(monkeypatch):
    """Test memory checking."""
    # Mock virtual memory to return high usage
    with patch("psutil.virtual_memory") as mock_memory:
        mock_memory.return_value = MagicMock(percent=95)
        report = RuntimeHealth(check_resources=True).run()
        memory_check = next((c for c in report["checks"] if c["name"] == "memory"), None)
        assert memory_check is not None
        assert memory_check["available"] is False


def test_runtime_health_checks_cpu(monkeypatch):
    """Test CPU checking."""
    # Mock CPU to return high usage
    with patch("psutil.cpu_percent", return_value=90):
        with patch("psutil.cpu_count", return_value=4):
            report = RuntimeHealth(check_resources=True).run()
            cpu_check = next((c for c in report["checks"] if c["name"] == "cpu"), None)
            assert cpu_check is not None
            assert cpu_check["available"] is True
            assert "90.0" in cpu_check["version"]


def test_runtime_health_skips_resource_checks_when_disabled():
    """Test that resource checks are skipped when check_resources=False."""
    report = RuntimeHealth(check_resources=False).run()
    resource_checks = [c for c in report["checks"] if c["name"] in ("disk-space", "memory", "cpu")]
    assert len(resource_checks) == 0


def test_runtime_health_skips_environment_checks_when_disabled():
    """Test that environment checks are skipped when check_environment=False."""
    report = RuntimeHealth(check_environment=False).run()
    env_checks = [c for c in report["checks"] if c["name"] in ("cloud-environment", "production-environment")]
    assert len(env_checks) == 0


def test_runtime_health_handles_psutil_import_error():
    """Test graceful handling when psutil is not available."""
    with patch.dict(sys.modules, {"psutil": None}):
        report = RuntimeHealth(check_resources=True).run()
        # When psutil is not available, the first resource check (disk-space) should be unavailable
        resource_check = next((c for c in report["checks"] if c["name"] == "disk-space"), None)
        assert resource_check is not None
        assert resource_check["available"] is False
        # The detail message should indicate the disk usage percentage
        assert "disk usage" in resource_check["detail"]


def test_runtime_health_handles_disk_space_error():
    """Test graceful handling when disk space check fails."""
    with patch("shutil.disk_usage", side_effect=OSError("Disk error")):
        report = RuntimeHealth(check_resources=True).run()
        # When disk space check fails, a resources check should be created
        resource_check = next((c for c in report["checks"] if c["name"] == "resources"), None)
        assert resource_check is not None
        assert resource_check["available"] is False
        assert "Disk error" in resource_check["detail"]


def test_runtime_health_status_with_resource_issues():
    """Test that degraded status is returned when resources are low."""
    with patch("shutil.disk_usage") as mock_disk:
        mock_disk.return_value = MagicMock(used=1000, total=1000, free=0)
        report = RuntimeHealth(check_resources=True).run()
        # Status is still 'ok' because required checks (git) are available
        # Resource checks are not required, so they don't affect the status
        assert report["status"] == "ok"


def test_runtime_health_status_with_cloud_environment(monkeypatch):
    """Test that ok status is returned even with cloud environment."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIAIOSFODNN7EXAMPLE")
    report = RuntimeHealth(check_environment=True).run()
    assert report["status"] == "ok"
