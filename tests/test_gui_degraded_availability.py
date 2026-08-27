"""Focused validation for GUI degraded-availability behavior."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from windows_gui import (
    DEPENDENCY_STATE_COPY,
    classify_dependency_state,
    dependency_state_message,
)


class GuiDegradedAvailabilityTests(unittest.TestCase):
    """Verify unavailable dependencies preserve safe user workflows."""

    def test_all_dependency_types_map_to_stable_states(self) -> None:
        cases = (
            ({"dependency": "cloud"}, "cloud_unavailable"),
            ({"dependency": "local_endpoint"}, "local_endpoint_unavailable"),
            ({"dependency": "connector"}, "connector_unavailable"),
            ({"dependency": "runtime"}, "runtime_unavailable"),
            ({"status": "disconnected"}, "connector_unavailable"),
            ({"status": "endpoint_unavailable"}, "local_endpoint_unavailable"),
        )
        for result, expected in cases:
            self.assertEqual(classify_dependency_state(result), expected)
        self.assertEqual(classify_dependency_state(None), "runtime_unavailable")

    def test_each_state_has_plain_language_recovery_actions(self) -> None:
        for state, (title, explanation, actions) in DEPENDENCY_STATE_COPY.items():
            message = dependency_state_message(state)
            self.assertIn(title, message)
            self.assertIn(explanation, message)
            self.assertGreaterEqual(len(actions), 2)
            for action in actions:
                self.assertIn(action, message)

    def test_contract_and_gui_copy_preserve_work_and_privacy(self) -> None:
        root = Path(__file__).resolve().parents[1]
        contract = (root / "docs" / "GUI_DEGRADED_AVAILABILITY.md").read_text(encoding="utf-8")
        for phrase in (
            "objective draft",
            "task plan",
            "saved artifacts",
            "diagnostics",
            "Cloud failure never silently routes data",
            "Retry is bounded",
            "idempotency key",
            "does not discard the task",
            "does not delete an imported model",
        ):
            self.assertIn(phrase, contract)
        self.assertNotRegex(
            contract,
            re.compile(r"(?i)(bearer\s+[a-z0-9._-]{12,}|sk-[a-z0-9]{12,})"),
        )


if __name__ == "__main__":
    unittest.main()
