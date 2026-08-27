"""Focused validation for the task-plan view contract."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs" / "TASK_PLAN_VIEW.md"


class TaskPlanViewTests(unittest.TestCase):
    """Verify the task-plan view exposes deterministic planning state safely."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = CONTRACT_PATH.read_text(encoding="utf-8")

    def test_graph_model_covers_required_plan_fields(self) -> None:
        for phrase in (
            "Plan header",
            "Task node",
            "Dependency edge",
            "Agent assignment",
            "Blocker",
            "Retry state",
            "Verification gate",
            "Plan summary",
            "next eligible tasks",
        ):
            self.assertIn(phrase, self.contract)

    def test_statuses_and_interactions_are_explicit(self) -> None:
        for phrase in (
            "Draft",
            "Ready",
            "Waiting",
            "Running",
            "Blocked",
            "Failed",
            "Verifying",
            "Completed",
            "Cancelled",
            "Select node",
            "Filter and search",
            "Expand dependency path",
            "Inspect blocker",
            "Inspect retry",
            "Verification review",
            "Narrow layout",
        ):
            self.assertIn(phrase, self.contract)

    def test_safety_accessibility_and_acceptance_boundaries_are_present(self) -> None:
        for phrase in (
            "accessible tree or tabular dependency representation",
            "keyboard navigation",
            "reduced motion",
            "bounded rendering",
            "provider credentials",
            "Authorization is enforced server-side",
            "root-bound and size-limited",
            "fixture graph",
            "large-graph performance bound",
            "implementation and live visual regression remain subsequent work",
        ):
            self.assertIn(phrase, self.contract)
        self.assertNotRegex(
            self.contract,
            re.compile(r"(?i)(bearer\s+[a-z0-9._-]{12,}|sk-[a-z0-9]{12,})"),
        )


if __name__ == "__main__":
    unittest.main()
