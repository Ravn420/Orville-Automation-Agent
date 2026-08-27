"""Focused tests for the desktop operational dashboard."""

from __future__ import annotations

import unittest
from pathlib import Path

from windows_gui import OrvilleWindow


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
        dashboard = object.__new__(OrvilleWindow)
        dashboard.dashboard_vars = {key: _Value() for key in ("active", "runs", "models", "health", "failures", "artifacts")}
        OrvilleWindow._update_dashboard(dashboard, {
            "health": {"status": "ok"},
            "state": {"active_tasks": [{"id": "task-1"}], "recent_runs": [{"id": "run-1"}], "failures": [{"id": "failure-1"}]},
            "providers": {"providers": [{"provider_id": "local"}, {"provider_id": "cloud"}]},
            "artifacts": {"artifacts": [{"name": "report.md"}]},
        })
        self.assertEqual({key: value.value for key, value in dashboard.dashboard_vars.items()}, {"active": "1", "runs": "1", "models": "2", "health": "ONLINE", "failures": "1", "artifacts": "1"})

    def test_dashboard_degrades_to_safe_bounded_values(self) -> None:
        dashboard = object.__new__(OrvilleWindow)
        dashboard.dashboard_vars = {key: _Value() for key in ("active", "runs", "models", "health", "failures", "artifacts")}
        OrvilleWindow._update_dashboard(dashboard, {"health": None, "state": None, "providers": None, "artifacts": None})
        self.assertEqual(dashboard.dashboard_vars["health"].value, "CHECK")
        self.assertEqual(dashboard.dashboard_vars["active"].value, "0")
        self.assertEqual(dashboard.dashboard_vars["artifacts"].value, "0")


if __name__ == "__main__":
    unittest.main()
