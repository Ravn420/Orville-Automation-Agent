"""Focused validation for the GUI information-architecture contract."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURE_PATH = ROOT / "docs" / "GUI_INFORMATION_ARCHITECTURE.md"


class GuiInformationArchitectureTests(unittest.TestCase):
    """Verify that the GUI contract covers users, workflows, and safe navigation."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.architecture = ARCHITECTURE_PATH.read_text(encoding="utf-8")

    def test_target_users_and_needs_are_defined(self) -> None:
        for user in ("Builder", "Operator", "Reviewer", "Project owner"):
            self.assertIn(user, self.architecture)
        for need in ("Objective intake", "Provider/model inventory", "Evidence", "Project settings"):
            self.assertIn(need, self.architecture)
        self.assertIn("Cannot publish, deploy, or alter external systems without approval", self.architecture)

    def test_primary_workflows_cover_lifecycle_and_recovery(self) -> None:
        for workflow in (
            "Configure and check readiness",
            "Create and execute an objective",
            "Review and verify an output",
            "Preview and deliver an artifact",
            "Recover a failed or interrupted run",
        ):
            self.assertIn(workflow, self.architecture)
        for term in ("assumptions", "task graph", "verification", "local preview", "resume", "rollback"):
            self.assertIn(term, self.architecture)

    def test_navigation_and_information_architecture_are_explicit(self) -> None:
        for item in ("Home", "Projects", "New objective", "Activity", "Providers", "Settings", "Help"):
            self.assertIn(f"**{item}**", self.architecture)
        for object_name in ("Workspace", "Project", "Objective", "Run", "Task graph and events", "Artifacts and checkpoints"):
            self.assertIn(object_name, self.architecture)
        for region in ("summary", "evidence", "controls"):
            self.assertIn(region, self.architecture)

    def test_journeys_and_safety_boundaries_are_testable(self) -> None:
        for journey in ("First objective", "Active execution", "Verification", "Artifact preview", "Provider issue", "Interrupted run"):
            self.assertIn(journey, self.architecture)
        for phrase in (
            "stable URLs",
            "Loading, blocked, failed, stale, and unavailable states",
            "idempotent action state",
            "safe operation identifier",
            "Privacy mode",
            "external side effects",
        ):
            self.assertIn(phrase, self.architecture)
        self.assertNotRegex(
            self.architecture,
            re.compile(r"(?i)(bearer\s+[a-z0-9._-]{12,}|sk-[a-z0-9]{12,})"),
        )


if __name__ == "__main__":
    unittest.main()
