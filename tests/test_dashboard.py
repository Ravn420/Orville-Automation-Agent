"""Focused tests for the desktop operational dashboard."""

from __future__ import annotations

import unittest
from pathlib import Path

from orville_core.gui_state import dashboard_values


class _Value:
    def __init__(self) -> None:
        self.value = None

    def set(self, value: str) -> None:
        self.value = value


class DashboardTests(unittest.TestCase):
    """Verify dashboard coverage without opening a desktop window."""

    def test_dashboard_source_declares_required_cards_and_routes(self) -> None:
        source = (Path(__file__).resolve().parents[1] / "windows_gui.py").read_text(encoding="utf-8")
        for label in ("ACTIVE TASKS", "RECENT RUNS", "MODEL AVAILABILITY", "SYSTEM HEALTH", "FAILURES", "GENERATED ARTIFACTS"):
            self.assertIn(label, source)
        for route in ("/api/v1/health", "/api/v1/state", "/api/v1/providers", "/api/v1/artifacts"):
            self.assertIn(route, source)
        self.assertIn("never display raw errors or payloads", source)

    def test_dashboard_aggregates_existing_payload_shapes(self) -> None:
        values = dashboard_values({
            "health": {"status": "ok"},
            "state": {"active_tasks": [{"id": "task-1"}], "recent_runs": [{"id": "run-1"}], "failures": [{"id": "failure-1"}]},
            "providers": {"providers": [{"provider_id": "local"}, {"provider_id": "cloud"}]},
            "artifacts": {"artifacts": [{"name": "report.md"}]},
        })
        self.assertEqual(values, {"active": "1", "runs": "1", "models": "2", "health": "ONLINE", "failures": "1", "artifacts": "1"})

    def test_dashboard_degrades_to_safe_bounded_values(self) -> None:
        values = dashboard_values({"health": None, "state": None, "providers": None, "artifacts": None})
        self.assertEqual(values["health"], "CHECK")
        self.assertEqual(values["active"], "0")
        self.assertEqual(values["artifacts"], "0")


if __name__ == "__main__":
    unittest.main()
