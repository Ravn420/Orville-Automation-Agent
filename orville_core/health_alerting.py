"""Health check alerting and monitoring for Orville deployments.

This module provides alerting capabilities for health check failures and degraded status,
with support for multiple alert channels (email, webhook, console).
"""

from __future__ import annotations

import json
import os
import smtplib
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from pathlib import Path
from typing import Any


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Supported alert channels."""
    CONSOLE = "console"
    EMAIL = "email"
    WEBHOOK = "webhook"
    ALL = "all"


@dataclass
class Alert:
    """An alert notification."""
    level: AlertLevel
    check_name: str
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: dict[str, Any] = field(default_factory=dict)
    channels: list[AlertChannel] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "level": self.level.value,
            "check_name": self.check_name,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
            "channels": [c.value for c in self.channels],
        }


class HealthAlerting:
    """Alerting system for health check events."""
    
    def __init__(
        self,
        *,
        db_path: str | Path = ".orville/health.db",
        alert_config_path: str | Path = ".orville/alert_config.json",
        default_channels: list[AlertChannel] | None = None,
    ) -> None:
        """Initialize the health alerting system.
        
        Args:
            db_path: Path to the health check database
            alert_config_path: Path to the alert configuration file
            default_channels: Default alert channels
        """
        if default_channels is None:
            default_channels = [AlertChannel.CONSOLE]
        self.db_path = Path(db_path)
        self.alert_config_path = Path(alert_config_path)
        self.default_channels = default_channels
        self.alerts: list[Alert] = []
        self._alert_handlers: list[Callable[[Alert], None]] = []
        
        # Load alert configuration
        if self.alert_config_path.exists():
            self._load_config()
    
    def _load_config(self) -> None:
        """Load alert configuration from file."""
        try:
            with open(self.alert_config_path, "r") as f:
                data = json.load(f)
            
            self.default_channels = [
                AlertChannel(c) for c in data.get("default_channels", ["console"])
            ]
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            print(f"Warning: Failed to load alert config: {exc}", file=sys.stderr)
    
    def _save_config(self) -> None:
        """Save alert configuration to file."""
        try:
            data = {
                "default_channels": [c.value for c in self.default_channels],
            }
            
            self.alert_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.alert_config_path, "w") as f:
                json.dump(data, f, indent=2)
        except OSError as exc:
            print(f"Warning: Failed to save alert config: {exc}", file=sys.stderr)
    
    def add_alert_handler(self, handler: Callable[[Alert], None]) -> None:
        """Add a custom alert handler.
        
        Args:
            handler: Function that receives Alert objects
        """
        self._alert_handlers.append(handler)
    
    def remove_alert_handler(self, handler: Callable[[Alert], None]) -> None:
        """Remove a custom alert handler.
        
        Args:
            handler: Function to remove
        """
        if handler in self._alert_handlers:
            self._alert_handlers.remove(handler)
    
    def _send_alert(self, alert: Alert) -> None:
        """Send an alert through configured channels.
        
        Args:
            alert: The alert to send
        """
        # Call custom handlers
        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as exc:
                print(f"Error in alert handler: {exc}", file=sys.stderr)
        
        # Send through configured channels
        channels = alert.channels if alert.channels else self.default_channels
        
        if AlertChannel.CONSOLE in channels:
            self._send_console_alert(alert)
        
        if AlertChannel.EMAIL in channels:
            self._send_email_alert(alert)
        
        if AlertChannel.WEBHOOK in channels:
            self._send_webhook_alert(alert)
        
        # Store the alert
        self.alerts.append(alert)
        
        # Keep only the last 1000 alerts
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]
    
    def _send_console_alert(self, alert: Alert) -> None:
        """Send an alert to console.
        
        Args:
            alert: The alert to send
        """
        level_color = {
            AlertLevel.INFO: "\033[94m",  # Blue
            AlertLevel.WARNING: "\033[93m",  # Yellow
            AlertLevel.ERROR: "\033[91m",  # Red
            AlertLevel.CRITICAL: "\033[95m",  # Magenta
        }.get(alert.level, "")
        
        reset_color = "\033[0m"
        
        print(f"{level_color}[{alert.level.value.upper()}]{reset_color} Health Check Alert: {alert.message}", file=sys.stderr)
        
        if alert.details:
            print(f"  Details: {json.dumps(alert.details, indent=2)}", file=sys.stderr)
    
    def _send_email_alert(self, alert: Alert) -> None:
        """Send an alert via email.
        
        Args:
            alert: The alert to send
        """
        # Check for email configuration
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        alert_email = os.getenv("ALERT_EMAIL")
        
        if not smtp_server or not smtp_username or not smtp_password or not alert_email:
            return
        
        # Create the email
        msg = MIMEMultipart()
        msg["From"] = smtp_username
        msg["To"] = alert_email
        msg["Subject"] = f"[{alert.level.value.upper()}] Health Check Alert: {alert.check_name}"
        
        body = f"""
Health Check Alert

Check Name: {alert.check_name}
Level: {alert.level.value}
Timestamp: {alert.timestamp.isoformat()}
Message: {alert.message}

Details:
{json.dumps(alert.details, indent=2)}
"""
        msg.attach(MIMEText(body, "plain"))
        
        # Send the email
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
        except Exception as exc:
            print(f"Warning: Failed to send email alert: {exc}", file=sys.stderr)
    
    def _send_webhook_alert(self, alert: Alert) -> None:
        """Send an alert via webhook.
        
        Args:
            alert: The alert to send
        """
        webhook_url = os.getenv("ALERT_WEBHOOK_URL")
        
        if not webhook_url:
            return
        
        try:
            import urllib.error
            import urllib.request
            
            data = alert.to_dict()
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps(data).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Orville-HealthAlerting/1.0",
                },
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                response.read()
        except (urllib.error.URLError, urllib.error.HTTPError, Exception) as exc:
            print(f"Warning: Failed to send webhook alert: {exc}", file=sys.stderr)
    
    def alert_on_failure(
        self,
        check_name: str,
        message: str,
        *,
        level: AlertLevel = AlertLevel.ERROR,
        details: dict[str, Any] | None = None,
        channels: list[AlertChannel] | None = None,
    ) -> None:
        """Send an alert for a health check failure.
        
        Args:
            check_name: Name of the health check
            message: Alert message
            level: Alert severity level
            details: Additional details
            channels: Alert channels to use
        """
        alert = Alert(
            level=level,
            check_name=check_name,
            message=message,
            details=details or {},
            channels=channels or self.default_channels,
        )
        self._send_alert(alert)
    
    def alert_on_degraded(
        self,
        check_name: str,
        message: str,
        *,
        level: AlertLevel = AlertLevel.WARNING,
        details: dict[str, Any] | None = None,
        channels: list[AlertChannel] | None = None,
    ) -> None:
        """Send an alert for a health check degradation.
        
        Args:
            check_name: Name of the health check
            message: Alert message
            level: Alert severity level
            details: Additional details
            channels: Alert channels to use
        """
        alert = Alert(
            level=level,
            check_name=check_name,
            message=message,
            details=details or {},
            channels=channels or self.default_channels,
        )
        self._send_alert(alert)
    
    def alert_on_recovery(
        self,
        check_name: str,
        message: str,
        *,
        level: AlertLevel = AlertLevel.INFO,
        details: dict[str, Any] | None = None,
        channels: list[AlertChannel] | None = None,
    ) -> None:
        """Send an alert for a health check recovery.
        
        Args:
            check_name: Name of the health check
            message: Alert message
            level: Alert severity level
            details: Additional details
            channels: Alert channels to use
        """
        alert = Alert(
            level=level,
            check_name=check_name,
            message=message,
            details=details or {},
            channels=channels or self.default_channels,
        )
        self._send_alert(alert)
    
    def get_alerts(
        self,
        *,
        check_name: str | None = None,
        level: AlertLevel | None = None,
        limit: int = 100,
    ) -> list[Alert]:
        """Get recent alerts.
        
        Args:
            check_name: Filter by check name
            level: Filter by alert level
            limit: Maximum number of alerts to return
            
        Returns:
            List of alerts
        """
        alerts = self.alerts
        
        if check_name:
            alerts = [a for a in alerts if a.check_name == check_name]
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        return alerts[-limit:]
    
    def get_alert_summary(self) -> dict[str, Any]:
        """Get a summary of recent alerts.
        
        Returns:
            Dictionary with alert statistics
        """
        if not self.alerts:
            return {
                "total_alerts": 0,
                "by_level": {},
                "by_check": {},
            }
        
        by_level = {}
        by_check = {}
        
        for alert in self.alerts:
            # Count by level
            by_level[alert.level.value] = by_level.get(alert.level.value, 0) + 1
            
            # Count by check
            by_check[alert.check_name] = by_check.get(alert.check_name, 0) + 1
        
        return {
            "total_alerts": len(self.alerts),
            "by_level": by_level,
            "by_check": by_check,
        }
    
    def clear_alerts(self) -> None:
        """Clear all stored alerts."""
        self.alerts.clear()
    
    def export_alerts(self, output_path: str | Path) -> None:
        """Export alerts to a JSON file.
        
        Args:
            output_path: Path to the output JSON file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump([alert.to_dict() for alert in self.alerts], f, indent=2)
