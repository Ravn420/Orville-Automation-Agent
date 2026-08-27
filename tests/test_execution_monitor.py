"""Focused tests for the desktop execution monitor contract."""

from __future__ import annotations

import unittest
from pathlib import Path

from orville_core.gui_state import state_message


class ExecutionMonitorTests(unittest.TestCase):
    """Verify monitor controls and safe persisted-run coverage."""

    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).resolve().parents[1]
        cls.source = (root / "windows_gui.py").read_text(encoding="utf-8")
        cls.document = (root / "docs" / "EXECUTION_MONITOR_SPECIFICATION.md").read_text(encoding="utf-8")

    def test_monitor_covers_progress_events_controls_and_elapsed_time(self) -> None:
        for phrase in ("Execution monitor", "/api/v1/runs/", "/events", "Elapsed:", "_manager_request", "events[-80:]"):
            self.assertIn(phrase, self.source)
        for control in ("Pause monitor", "Resume waiting task", "Retry run", "Cancel run"):
            self.assertIn(control, self.source)

    def test_monitor_document_defines_required_operational_surfaces(self) -> None:
        for phrase in ("Live progress", "Logs and events", "Agent activity", "Tool calls", "Elapsed time", "Pause monitor", "Resume waiting task", "Retry run", "Cancel run"):
            self.assertIn(phrase, self.document)

    def test_monitor_uses_safe_bounded_output(self) -> None:
        self.assertIn("never display raw errors or payloads", self.source)
        self.assertIn("events[-80:]", self.source)
        self.assertIn('if state == "offline":', self.source)
        self.assertIn("write_safe(state_message(state))", self.source)
        self.assertIn("Offline", state_message("offline"))
        self.assertIn("Next:", state_message("offline"))


if __name__ == "__main__":
    unittest.main()
