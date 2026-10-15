"""Tests for health check alerting system."""
import json
import os
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from orville_core.health_alerting import (
    HealthAlerting,
    Alert,
    AlertChannel,
    AlertLevel,
)


def test_alert_creation():
    """Test creating an alert."""
    alert = Alert(
        level=AlertLevel.ERROR,
        check_name="test-check",
        message="Test alert message",
        details={"error": "Connection failed"},
        channels=[AlertChannel.CONSOLE],
    )
    
    assert alert.level == AlertLevel.ERROR
    assert alert.check_name == "test-check"
    assert alert.message == "Test alert message"
    assert len(alert.channels) == 1


def test_alert_to_dict():
    """Test converting an alert to dictionary."""
    alert = Alert(
        level=AlertLevel.ERROR,
        check_name="test-check",
        message="Test alert message",
    )
    
    data = alert.to_dict()
    
    assert data["level"] == "error"
    assert data["check_name"] == "test-check"
    assert data["message"] == "Test alert message"
    assert "timestamp" in data


def test_alert_with_all_channels():
    """Test creating an alert with all channels."""
    alert = Alert(
        level=AlertLevel.ERROR,
        check_name="test-check",
        message="Test alert",
        channels=[AlertChannel.CONSOLE, AlertChannel.EMAIL, AlertChannel.WEBHOOK],
    )
    
    assert len(alert.channels) == 3


def test_health_alerting_initialization(tmp_path):
    """Test initializing the health alerting system."""
    db_path = tmp_path / "test_health.db"
    alert_config_path = tmp_path / "test_alert_config.json"
    
    alerting = HealthAlerting(
        db_path=db_path,
        alert_config_path=alert_config_path,
        default_channels=[AlertChannel.CONSOLE],
    )
    
    assert str(alerting.db_path) == str(db_path)
    assert str(alerting.alert_config_path) == str(alert_config_path)
    assert len(alerting.alerts) == 0


def test_health_alerting_add_alert_handler(tmp_path):
    """Test adding a custom alert handler."""
    db_path = tmp_path / "test_health.db"
    alert_config_path = tmp_path / "test_alert_config.json"
    
    alerting = HealthAlerting(db_path=db_path, alert_config_path=alert_config_path)
    
    handler_called = []
    
    def test_handler(alert: Alert) -> None:
        handler_called.append(alert)
    
    alerting.add_alert_handler(test_handler)
    
    alert = Alert(
        level=AlertLevel.INFO,
        check_name="test-check",
        message="Test message",
    )
    
    alerting._send_alert(alert)
    
    assert len(handler_called) == 1
    assert handler_called[0].check_name == "test-check"


def test_health_alerting_remove_alert_handler(tmp_path):
    """Test removing a custom alert handler."""
    db_path = tmp_path / "test_health.db"
    alert_config_path = tmp_path / "test_alert_config.json"
    
    alerting = HealthAlerting(db_path=db_path, alert_config_path=alert_config_path)
    
    handler_called = []
    
    def test_handler(alert: Alert) -> None:
        handler_called.append(alert)
    
    alerting.add_alert_handler(test_handler)
    alerting.remove_alert_handler(test_handler)
    
    alert = Alert(
        level=AlertLevel.INFO,
        check_name="test-check",
        message="Test message",
    )
    
    alerting._send_alert(alert)
    
    assert len(handler_called) == 0


def test_health_alerting_alert_on_failure(tmp_path):
    """Test sending an alert for a failure."""
    db_path = tmp_path / "test_health.db"
    alert_config_path = tmp_path / "test_alert_config.json"
    
    alerting = HealthAlerting(db_path=db_path, alert_config_path=alert_config_path)
    
    alerting.alert_on_failure(
        check_name="test-check",
        message="Health check failed",
        level=AlertLevel.ERROR,
        details={"error": "Connection timeout"},
    )
    
    assert len(alerting.alerts) == 1
    assert alerting.alerts[0].check_name == "test-check"
    assert alerting.alerts[0].level == AlertLevel.ERROR
    assert "failed" in alerting.alerts[0].message.lower()


def test_health_alerting_alert_on_degraded(tmp_path):
    """Test sending an alert for degraded status."""
    db_path = tmp_path / "test_health.db"
    alert_config_path = tmp_path / "test_alert_config.json"
    
    alerting = HealthAlerting(db_path=db_path, alert_config_path=alert_config_path)
    
    alerting.alert_on_degraded(
        check_name="test-check",
        message="Health check degraded",
        level=AlertLevel.WARNING,
    )
    
    assert len(alerting.alerts) == 1
    assert alerting.alerts[0].level == AlertLevel.WARNING


def test_health_alerting_alert_on_recovery(tmp_path):
    """Test sending an alert for recovery."""
    db_path = tmp_path / "test_health.db"
    alert_config_path = tmp_path / "test_alert_config.json"
    
    alerting = HealthAlerting(db_path=db_path, alert_config_path=alert_config_path)
    
    alerting.alert_on_recovery(
        check_name="test-check",
        message="Health check recovered",
        level=AlertLevel.INFO,
    )
    
    assert len(alerting.alerts) == 1
    assert alerting.alerts[0].level == AlertLevel.INFO


def test_health_alerting_get_alerts(tmp_path):
    """Test getting recent alerts."""
    db_path = tmp_path / "test_health.db"
    alert_config_path = tmp_path / "test_alert_config.json"
    
    alerting = HealthAlerting(db_path=db_path, alert_config_path=alert_config_path)
    
    # Add some alerts
    for i in range(5):
        alerting.alert_on_failure(
            check_name="test-check",
            message=f"Alert {i}",
        )
    
    # Get all alerts
    all_alerts = alerting.get_alerts()
    assert len(all_alerts) == 5
    
    # Get filtered alerts
    error_alerts = alerting.get_alerts(level=AlertLevel.ERROR)
    assert len(error_alerts) == 5
    
    # Get limited alerts
    limited_alerts = alerting.get_alerts(limit=3)
    assert len(limited_alerts) == 3


def test_health_alerting_get_alert_summary(tmp_path):
    """Test getting alert summary."""
    db_path = tmp_path / "test_health.db"
    alert_config_path = tmp_path / "test_alert_config.json"
    
    alerting = HealthAlerting(db_path=db_path, alert_config_path=alert_config_path)
    
    # Add some alerts
    for i in range(3):
        alerting.alert_on_failure(
            check_name="check-1",
            message=f"Alert {i}",
        )
    
    for i in range(2):
        alerting.alert_on_degraded(
            check_name="check-2",
            message=f"Alert {i}",
        )
    
    summary = alerting.get_alert_summary()
    
    assert summary["total_alerts"] == 5
    assert summary["by_level"]["error"] == 3
    assert summary["by_level"]["warning"] == 2
    assert summary["by_check"]["check-1"] == 3
    assert summary["by_check"]["check-2"] == 2


def test_health_alerting_clear_alerts(tmp_path):
    """Test clearing all alerts."""
    db_path = tmp_path / "test_health.db"
    alert_config_path = tmp_path / "test_alert_config.json"
    
    alerting = HealthAlerting(db_path=db_path, alert_config_path=alert_config_path)
    
    # Add some alerts
    for i in range(3):
        alerting.alert_on_failure(
            check_name="test-check",
            message=f"Alert {i}",
        )
    
    assert len(alerting.alerts) == 3
    
    alerting.clear_alerts()
    
    assert len(alerting.alerts) == 0


def test_health_alerting_export_alerts(tmp_path):
    """Test exporting alerts to JSON."""
    db_path = tmp_path / "test_health.db"
    alert_config_path = tmp_path / "test_alert_config.json"
    
    alerting = HealthAlerting(db_path=db_path, alert_config_path=alert_config_path)
    
    # Add some alerts
    for i in range(2):
        alerting.alert_on_failure(
            check_name="test-check",
            message=f"Alert {i}",
        )
    
    output_path = tmp_path / "alerts_export.json"
    alerting.export_alerts(output_path)
    
    assert output_path.exists()
    
    with open(output_path) as f:
        data = json.load(f)
    
    assert len(data) == 2
    assert data[0]["check_name"] == "test-check"


def test_health_alerting_console_alert(tmp_path, capsys):
    """Test sending a console alert."""
    db_path = tmp_path / "test_health.db"
    alert_config_path = tmp_path / "test_alert_config.json"
    
    alerting = HealthAlerting(db_path=db_path, alert_config_path=alert_config_path)
    
    alerting.alert_on_failure(
        check_name="test-check",
        message="Test console alert",
    )
    
    captured = capsys.readouterr()
    assert "Test console alert" in captured.err


def test_health_alerting_email_alert_not_configured(tmp_path, capsys):
    """Test that email alert is not sent when not configured."""
    db_path = tmp_path / "test_health.db"
    alert_config_path = tmp_path / "test_alert_config.json"
    
    alerting = HealthAlerting(db_path=db_path, alert_config_path=alert_config_path)
    
    # Don't set email environment variables
    alerting.alert_on_failure(
        check_name="test-check",
        message="Test email alert",
    )
    
    # Should not fail, just print warning
    captured = capsys.readouterr()
    # Console alert should still be sent
    assert "Test email alert" in captured.err
    # But no email warning should be printed
    assert "Failed to send email alert" not in captured.err


def test_health_alerting_webhook_alert_not_configured(tmp_path, capsys):
    """Test that webhook alert is not sent when not configured."""
    db_path = tmp_path / "test_health.db"
    alert_config_path = tmp_path / "test_alert_config.json"
    
    alerting = HealthAlerting(db_path=db_path, alert_config_path=alert_config_path)
    
    # Don't set webhook environment variable
    alerting.alert_on_failure(
        check_name="test-check",
        message="Test webhook alert",
    )
    
    # Should not fail, just print warning
    captured = capsys.readouterr()
    # Console alert should still be sent
    assert "Test webhook alert" in captured.err
    # But no webhook warning should be printed
    assert "Failed to send webhook alert" not in captured.err


def test_health_alerting_custom_channels(tmp_path):
    """Test using custom alert channels."""
    db_path = tmp_path / "test_health.db"
    alert_config_path = tmp_path / "test_alert_config.json"
    
    alerting = HealthAlerting(db_path=db_path, alert_config_path=alert_config_path)
    
    alerting.alert_on_failure(
        check_name="test-check",
        message="Test custom channels",
        channels=[AlertChannel.EMAIL],
    )
    
    assert len(alerting.alerts) == 1
    assert alerting.alerts[0].channels == [AlertChannel.EMAIL]


def test_alert_level_enum():
    """Test AlertLevel enum values."""
    assert AlertLevel.INFO.value == "info"
    assert AlertLevel.WARNING.value == "warning"
    assert AlertLevel.ERROR.value == "error"
    assert AlertLevel.CRITICAL.value == "critical"


def test_alert_channel_enum():
    """Test AlertChannel enum values."""
    assert AlertChannel.CONSOLE.value == "console"
    assert AlertChannel.EMAIL.value == "email"
    assert AlertChannel.WEBHOOK.value == "webhook"
    assert AlertChannel.ALL.value == "all"
