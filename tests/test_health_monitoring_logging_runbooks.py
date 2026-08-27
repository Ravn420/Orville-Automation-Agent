"""Focused tests for health monitoring, structured logs, and runbook contract."""

from __future__ import annotations

import unittest
from pathlib import Path


class HealthMonitoringLoggingRunbookTests(unittest.TestCase):
    """Verify the operational contract is complete and safe by construction."""

    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).resolve().parents[1]
        cls.document = (root / "docs" / "HEALTH_MONITORING_LOGGING_RUNBOOKS.md").read_text(encoding="utf-8")

    def test_health_model_and_signal_thresholds_are_defined(self) -> None:
        for phrase in ("healthy", "degraded", "blocked", "offline", "unknown", "Availability", "Error rate", "Latency", "Saturation", "Freshness"):
            self.assertIn(phrase, self.document)

    def test_structured_event_schema_and_redaction_are_defined(self) -> None:
        for phrase in ("event_id", "event_type", "event_version", "occurred_at", "severity", "component", "correlation_id", "reason_code", "SecretScanner", "single JSON object", "unbounded payloads"):
            self.assertIn(phrase, self.document)

    def test_runbooks_ownership_and_limits_are_defined(self) -> None:
        for phrase in ("Service unavailable", "Elevated workflow", "storage saturation", "Security or integrity", "Release or canary", "approval-gated rollback", "GUI presents bounded summaries", "standalone commands", "Live alert delivery"):
            self.assertIn(phrase, self.document)


if __name__ == "__main__":
    unittest.main()
