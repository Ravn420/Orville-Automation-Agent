#!/usr/bin/env python3
"""Rewrite the _persist_report method with correct indentation"""

with open('orville_core/endpoint_monitor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the _persist_report method and replace it
old_method = '''    def _persist_report(self, report: EndpointHealthReport) -> None:
        """Persist health report to database."""
        try:
            if self._conn is None:
                raise EndpointMonitorPersistenceError("Database connection not initialized")
            conn = self._conn

            # Update current health
            for url, health in report.endpoints.items():
                            self._conn.execute("""
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
                            self._conn.execute("""
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
                            self._conn.execute("""
                        DELETE FROM endpoint_health_history
                        WHERE id NOT IN (
                            SELECT id FROM endpoint_health_history
                            WHERE endpoint_url = ?
                            ORDER BY id DESC
                            LIMIT ?
                        )
                    """, (url, self.config.max_history_entries))

            # Update config
                        self._conn.execute("""
                    UPDATE endpoint_monitor_config
                    SET value = ?
                    WHERE key = 'check_interval_seconds'
                """, (str(self.config.check_interval_seconds),))
                        self._conn.execute("""
                    UPDATE endpoint_monitor_config
                    SET value = ?
                    WHERE key = 'failure_threshold'
                """, (str(self.config.failure_threshold),))
                        self._conn.execute("""
                    UPDATE endpoint_monitor_config
                    SET value = ?
                    WHERE key = 'success_threshold'
                """, (str(self.config.success_threshold),))
                        self._conn.execute("""
                    UPDATE endpoint_monitor_config
                    SET value = ?
                    WHERE key = 'probe_timeout_seconds'
                """, (str(self.config.probe_timeout_seconds),))
                        self._conn.execute("""
                    UPDATE endpoint_monitor_config
                    SET value = ?
                    WHERE key = 'alert_on_failure'
                """, (str(self.config.alert_on_failure),))
                        self._conn.execute("""
                    UPDATE endpoint_monitor_config
                    SET value = ?
                    WHERE key = 'alert_on_degraded'
                """, (str(self.config.alert_on_degraded),))
                        self._conn.execute("""
                    UPDATE endpoint_monitor_config
                    SET value = ?
                    WHERE key = 'alert_on_recovery'
                """, (str(self.config.alert_on_recovery),))
                        self._conn.execute("""
                    UPDATE endpoint_monitor_config
                    SET value = ?
                    WHERE key = 'max_history_entries'
                """, (str(self.config.max_history_entries),))

        except sqlite3.Error as exc:
            raise EndpointMonitorPersistenceError(f"Failed to persist health report: {exc}")'''

new_method = '''    def _persist_report(self, report: EndpointHealthReport) -> None:
        """Persist health report to database."""
        try:
            if self._conn is None:
                raise EndpointMonitorPersistenceError("Database connection not initialized")
            conn = self._conn

            # Update current health
            for url, health in report.endpoints.items():
                self._conn.execute("""
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
                self._conn.execute("""
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
                self._conn.execute("""
                    DELETE FROM endpoint_health_history
                    WHERE id NOT IN (
                        SELECT id FROM endpoint_health_history
                        WHERE endpoint_url = ?
                        ORDER BY id DESC
                        LIMIT ?
                    )
                """, (url, self.config.max_history_entries))

            # Update config
            self._conn.execute("""
                UPDATE endpoint_monitor_config
                SET value = ?
                WHERE key = 'check_interval_seconds'
            """, (str(self.config.check_interval_seconds),))
            self._conn.execute("""
                UPDATE endpoint_monitor_config
                SET value = ?
                WHERE key = 'failure_threshold'
            """, (str(self.config.failure_threshold),))
            self._conn.execute("""
                UPDATE endpoint_monitor_config
                SET value = ?
                WHERE key = 'success_threshold'
            """, (str(self.config.success_threshold),))
            self._conn.execute("""
                UPDATE endpoint_monitor_config
                SET value = ?
                WHERE key = 'probe_timeout_seconds'
            """, (str(self.config.probe_timeout_seconds),))
            self._conn.execute("""
                UPDATE endpoint_monitor_config
                SET value = ?
                WHERE key = 'alert_on_failure'
            """, (str(self.config.alert_on_failure),))
            self._conn.execute("""
                UPDATE endpoint_monitor_config
                SET value = ?
                WHERE key = 'alert_on_degraded'
            """, (str(self.config.alert_on_degraded),))
            self._conn.execute("""
                UPDATE endpoint_monitor_config
                SET value = ?
                WHERE key = 'alert_on_recovery'
            """, (str(self.config.alert_on_recovery),))
            self._conn.execute("""
                UPDATE endpoint_monitor_config
                SET value = ?
                WHERE key = 'max_history_entries'
            """, (str(self.config.max_history_entries),))

        except sqlite3.Error as exc:
            raise EndpointMonitorPersistenceError(f"Failed to persist health report: {exc}")'''

content = content.replace(old_method, new_method)

with open('orville_core/endpoint_monitor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Rewrote _persist_report method with correct indentation')
