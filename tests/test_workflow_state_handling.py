"""Focused tests for consistent workflow-state handling."""

from __future__ import annotations

import unittest
from pathlib import Path

from orville_core.gui_state import WORKFLOW_STATE_COPY, classify_workflow_state, state_message


class WorkflowStateHandlingTests(unittest.TestCase):
    """Verify stable state classification and safe user-facing guidance."""

    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).resolve().parents[1]
        cls.source = (root / "windows_gui.py").read_text(encoding="utf-8")
        cls.document = (root / "docs" / "WORKFLOW_STATE_HANDLING.md").read_text(encoding="utf-8")

    def test_all_required_states_have_copy_and_recovery(self) -> None:
        labels = {"loading": "Loading", "empty": "Empty", "offline": "Offline", "blocked": "Blocked", "failed": "Failed", "partial": "Partial", "long_running": "Long-running"}
        for state, label in labels.items():
            self.assertIn(state, WORKFLOW_STATE_COPY)
            self.assertIn("Next:", state_message(state))
            self.assertIn(label, self.document)

    def test_classifier_distinguishes_empty_blocked_active_partial_and_failed(self) -> None:
        self.assertEqual(classify_workflow_state({"graph": {"tasks": []}}), "empty")
        self.assertEqual(classify_workflow_state({"run_status": "waiting_approval", "graph": {"tasks": [{}]}}), "blocked")
        self.assertEqual(classify_workflow_state({"run_status": "running", "graph": {"tasks": [{}]}}), "long_running")
        self.assertEqual(classify_workflow_state({"graph": {"tasks": [{"status": "complete"}, {"status": "failed"}]}}), "partial")
        self.assertEqual(classify_workflow_state({"graph": {"tasks": [{"status": "failed"}]}}), "failed")

    def test_views_expose_loading_empty_offline_and_safe_recovery(self) -> None:
        for phrase in ('summary.set(state_message("loading"))', 'summary.set(state_message("empty"))', 'if state == "offline":', 'Review the reason before continuing.'):
            self.assertIn(phrase, self.source if phrase != 'Review the reason before continuing.' else self.document)
        for phrase in ("without exposing raw exceptions", "credentials", "recovery guidance"):
            self.assertIn(phrase, self.document)


if __name__ == "__main__":
    unittest.main()
