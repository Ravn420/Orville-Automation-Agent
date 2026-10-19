"""Persistent endpoint monitoring with scheduling and alerting."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .endpoint_config import ProviderEndpointSpec
from .endpoint_health import (
    EndpointHealth,
    EndpointHealthMonitor,
    EndpointHealthReport,
)


class EndpointMonitorError(Exception):
    """Base exception for endpoint monitor errors."""


class EndpointMonitorPersistenceError(EndpointMonitorError):
    """Error related to endpoint monitor persistence."""


@dataclass(frozen=True)
class EndpointMonitorConfig:
    """Configuration for endpoint monitoring."""
    database_path: Path
    check_interval_seconds: int = 60
    failure_threshold: int = 3
    success_threshold: int = 2
    probe_timeout_seconds: float = 5.0
    alert_on_failure: bool = True
    alert_on_degraded: bool = True
    alert_on_recovery: bool = True
    max_history_entries: int = 1000


class EndpointMonitor:
    """Persistent endpoint monitoring with scheduling and alerting."""

    def __init__(self, config: EndpointMonitorConfig):
        """
        Initialize endpoint monitor.

        Args:
            config: EndpointMonitorConfig with monitoring settings
        """
        self.config = config
        self._monitor = EndpointHealthMonitor(
            environment="persistent",
            check_interval_seconds=config.check_interval_seconds,
            failure_threshold=config.failure_threshold,
            success_threshold=config.success_threshold,
            probe_timeout_seconds=config.probe_timeout_seconds,
        )
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the monitoring database."""
        if self._initialized:
            return

        # Create database if it doesn't exist
        self.config.database_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.config.database_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS endpoint_health (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint_url TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL,
                    last_probed TEXT NOT NULL,
                    consecutive_failures INTEGER DEFAULT 0,
                    consecutive_successes INTEGER DEFAULT 0,
                    average_response_time_ms REAL DEFAULT 0.0,
                    probe_count INTEGER DEFAULT 0,
                    last_error TEXT,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS endpoint_health_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint_url TEXT NOT NULL,
                    status TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    consecutive_failures INTEGER,
                    consecutive_successes INTEGER,
                    average_response_time_ms REAL,
                    probe_count INTEGER,
                    last_error TEXT,
                    metadata TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS endpoint_monitor_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

            # Initialize config
            conn.execute("""
                INSERT OR IGNORE INTO endpoint_monitor_config (key, value)
                VALUES ('check_interval_seconds', ?)
            """, (str(self.config.check_interval_seconds),))
            conn.execute("""
                INSERT OR IGNORE INTO endpoint_monitor_config (key, value)
                VALUES ('failure_threshold', ?)
            """, (str(self.config.failure_threshold),))
            conn.execute("""
                INSERT OR IGNORE INTO endpoint_monitor_config (key, value)
                VALUES ('success_threshold', ?)
            """, (str(self.config.success_threshold),))
            conn.execute("""
                INSERT OR IGNORE INTO endpoint_monitor_config (key, value)
                VALUES ('probe_timeout_seconds', ?)
            """, (str(self.config.probe_timeout_seconds),))
            conn.execute("""
                INSERT OR IGNORE INTO endpoint_monitor_config (key, value)
                VALUES ('alert_on_failure', ?)
            """, (str(self.config.alert_on_failure),))
            conn.execute("""
                INSERT OR IGNORE INTO endpoint_monitor_config (key, value)
                VALUES ('alert_on_degraded', ?)
            """, (str(self.config.alert_on_degraded),))
            conn.execute("""
                INSERT OR IGNORE INTO endpoint_monitor_config (key, value)
                VALUES ('alert_on_recovery', ?)
            """, (str(self.config.alert_on_recovery),))
            conn.execute("""
                INSERT OR IGNORE INTO endpoint_monitor_config (key, value)
                VALUES ('max_history_entries', ?)
            """, (str(self.config.max_history_entries),))

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        self._initialized = True

    def add_endpoint(self, url: str) -> None:
        """
        Add an endpoint to monitor.

        Args:
            url: Endpoint URL to monitor
        """
        self.initialize()
        # Create a temporary spec object for the endpoint
        spec = ProviderEndpointSpec(
            provider_id="monitor",
            display_name="Monitored Endpoint",
            provider_type="cloud",
            endpoint_url=url,
            model_identifier="model",
            protocol="openai",
        )
        self._monitor.add_endpoint(spec)

    def remove_endpoint(self, url: str) -> bool:
        """
        Remove an endpoint from monitoring.

        Args:
            url: Endpoint URL to remove

        Returns:
            True if endpoint was removed, False if not found
        """
        self.initialize()
        return self._monitor.remove_endpoint(url)

    def get_endpoint_health(self, url: str) -> EndpointHealth | None:
        """
        Get health status for a specific endpoint.

        Args:
            url: Endpoint URL

        Returns:
            EndpointHealth if found, None otherwise
        """
        self.initialize()
        return self._monitor.get_endpoint_health(url)

    def get_all_health(self) -> dict[str, EndpointHealth]:
        """
        Get health status for all monitored endpoints.

        Returns:
            Dictionary mapping URLs to EndpointHealth
        """
        self.initialize()
        return self._monitor.get_all_health()

    def run_probes(self) -> EndpointHealthReport:
        """
        Run health probes for all monitored endpoints.

        Returns:
            EndpointHealthReport with results
        """
        if not self._initialized:
            self.initialize()
        report = self._monitor.run_probes()
        self._persist_report(report)
        return report

    def _persist_report(self, report: EndpointHealthReport) -> None:
        """Persist health report to database."""
        try:
            # Use a fresh connection for each persistence operation to avoid
            # keeping the database locked on Windows
            with sqlite3.connect(self.config.database_path) as conn:
                # Update current health
                for url, health in report.endpoints.items():
                    conn.execute("""
                        INSERT OR REPLACE INTO endpoint_health
                        (endpoint_url, status, last_probed, consecutive_failures,
                         consecutive_successes, average_response_time_ms, probe_count,
                         last_error, metadata, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        url,
                        health.status.value,
                        health.last_probed.isoformat(),
                        health.consecutive_failures,
                        health.consecutive_successes,
                        health.average_response_time_ms,
                        health.probe_count,
                        health.last_error,
                        json.dumps(health.metadata) if health.metadata else None,
                        health.last_probed.isoformat(),
                        health.last_probed.isoformat(),
                    ))

                    # Add to history
                    conn.execute("""
                        INSERT INTO endpoint_health_history
                        (endpoint_url, status, timestamp, consecutive_failures,
                         consecutive_successes, average_response_time_ms, probe_count,
                         last_error, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        url,
                        health.status.value,
                        health.last_probed.isoformat(),
                        health.consecutive_failures,
                        health.consecutive_successes,
                        health.average_response_time_ms,
                        health.probe_count,
                        health.last_error,
                        json.dumps(health.metadata) if health.metadata else None,
                    ))

                    # Trim history
                    conn.execute("""
                        DELETE FROM endpoint_health_history
                        WHERE id NOT IN (
                            SELECT id FROM endpoint_health_history
                            WHERE endpoint_url = ?
                            ORDER BY id DESC
                            LIMIT ?
                        )
                    """, (url, self.config.max_history_entries))

                # Update config
                conn.execute("""
                    UPDATE endpoint_monitor_config
                    SET value = ?
                    WHERE key = 'check_interval_seconds'
                """, (str(self.config.check_interval_seconds),))
                conn.execute("""
                    UPDATE endpoint_monitor_config
                    SET value = ?
                    WHERE key = 'failure_threshold'
                """, (str(self.config.failure_threshold),))
                conn.execute("""
                    UPDATE endpoint_monitor_config
                    SET value = ?
                    WHERE key = 'success_threshold'
                """, (str(self.config.success_threshold),))
                conn.execute("""
                    UPDATE endpoint_monitor_config
                    SET value = ?
                    WHERE key = 'probe_timeout_seconds'
                """, (str(self.config.probe_timeout_seconds),))
                conn.execute("""
                    UPDATE endpoint_monitor_config
                    SET value = ?
                    WHERE key = 'alert_on_failure'
                """, (str(self.config.alert_on_failure),))
                conn.execute("""
                    UPDATE endpoint_monitor_config
                    SET value = ?
                    WHERE key = 'alert_on_degraded'
                """, (str(self.config.alert_on_degraded),))
                conn.execute("""
                    UPDATE endpoint_monitor_config
                    SET value = ?
                    WHERE key = 'alert_on_recovery'
                """, (str(self.config.alert_on_recovery),))
                conn.execute("""
                    UPDATE endpoint_monitor_config
                    SET value = ?
                    WHERE key = 'max_history_entries'
                """, (str(self.config.max_history_entries),))

                conn.commit()

        except sqlite3.Error as exc:
            raise EndpointMonitorPersistenceError(f"Failed to persist health report: {exc}")

    def get_history(self, url: str, limit: int = 100) -> list[dict[str, Any]]:
        """
        Get health history for a specific endpoint.

        Args:
            url: Endpoint URL
            limit: Maximum number of history entries to return

        Returns:
            List of health history entries
        """
        self.initialize()

        try:
            with sqlite3.connect(self.config.database_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM endpoint_health_history
                    WHERE endpoint_url = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (url, limit))

                return [dict(row) for row in cursor.fetchall()]

        except sqlite3.Error as exc:
            raise EndpointMonitorPersistenceError(f"Failed to get health history: {exc}")

    def get_summary(self) -> dict[str, Any]:
        """
        Get monitoring summary.

        Returns:
            Dictionary with monitoring summary
        """
        self.initialize()

        try:
            with sqlite3.connect(self.config.database_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT
                        COUNT(*) as total_endpoints,
                        SUM(CASE WHEN status = 'healthy' THEN 1 ELSE 0 END) as healthy_count,
                        SUM(CASE WHEN status = 'degraded' THEN 1 ELSE 0 END) as degraded_count,
                        SUM(CASE WHEN status = 'unhealthy' THEN 1 ELSE 0 END) as unhealthy_count,
                        SUM(CASE WHEN status = 'unknown' THEN 1 ELSE 0 END) as unknown_count
                    FROM endpoint_health
                """)
                row = cursor.fetchone()
                return dict(row) if row else {}

        except sqlite3.Error as exc:
            raise EndpointMonitorPersistenceError(f"Failed to get summary: {exc}")

    def get_alerts(self, hours: int = 24) -> list[dict[str, Any]]:
        """
        Get recent alerts.

        Args:
            hours: Number of hours to look back

        Returns:
            List of recent alerts
        """
        self.initialize()

        try:
            with sqlite3.connect(self.config.database_path) as conn:
                conn.row_factory = sqlite3.Row
                cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
                cursor = conn.execute("""
                    SELECT * FROM endpoint_health_history
                    WHERE timestamp >= ?
                    AND (status = 'unhealthy' OR status = 'degraded')
                    ORDER BY timestamp DESC
                """, (cutoff,))

                return [dict(row) for row in cursor.fetchall()]

        except sqlite3.Error as exc:
            raise EndpointMonitorPersistenceError(f"Failed to get alerts: {exc}")

    def get_report(self) -> EndpointHealthReport:
        """
        Get current health report without running new probes.

        Returns:
            Current EndpointHealthReport
        """
        self.initialize()
        return self._monitor.get_report()

    def export_report(self, output_path: Path) -> None:
        """
        Export health report to JSON file.

        Args:
            output_path: Path to output JSON file
        """
        self.initialize()
        report = self.get_report()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2, default=str)

    def import_config(self, config_path: Path) -> None:
        """
        Import monitoring configuration from JSON file.

        Args:
            config_path: Path to JSON configuration file
        """
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        self.config = EndpointMonitorConfig(
            database_path=Path(config_data.get("database_path", self.config.database_path)),
            check_interval_seconds=config_data.get("check_interval_seconds", self.config.check_interval_seconds),
            failure_threshold=config_data.get("failure_threshold", self.config.failure_threshold),
            success_threshold=config_data.get("success_threshold", self.config.success_threshold),
            probe_timeout_seconds=config_data.get("probe_timeout_seconds", self.config.probe_timeout_seconds),
            alert_on_failure=config_data.get("alert_on_failure", self.config.alert_on_failure),
            alert_on_degraded=config_data.get("alert_on_degraded", self.config.alert_on_degraded),
            alert_on_recovery=config_data.get("alert_on_recovery", self.config.alert_on_recovery),
            max_history_entries=config_data.get("max_history_entries", self.config.max_history_entries),
        )

        self.initialize()

    def close(self) -> None:
        """Close the monitor and release resources."""
        self._initialized = False

    def __repr__(self) -> str:
        """Return string representation of the monitor."""
        return f"EndpointMonitor(config={self.config!r}, initialized={self._initialized})"""
