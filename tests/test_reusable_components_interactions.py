"""Focused validation for the reusable component interaction contract."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs" / "REUSABLE_COMPONENTS_INTERACTIONS.md"


class ReusableComponentsInteractionTests(unittest.TestCase):
    """Verify reusable component families and deterministic interaction rules."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = CONTRACT_PATH.read_text(encoding="utf-8")

    def test_component_families_and_domain_components_are_defined(self) -> None:
        for phrase in (
            "Actions",
            "Data entry",
            "Data display",
            "Feedback",
            "Navigation",
            "Overlays",
            "Orville domain",
            "Task row",
            "approval panel",
            "artifact viewer",
        ):
            self.assertIn(phrase, self.contract)

    def test_states_and_interaction_patterns_are_deterministic(self) -> None:
        for phrase in (
            "default",
            "focus-visible",
            "disabled",
            "loading",
            "error",
            "empty",
            "success",
            "Submit and mutate",
            "Destructive or external action",
            "Async loading",
            "Long-running task",
            "bounded recovery action",
        ):
            self.assertIn(phrase, self.contract)

    def test_accessibility_security_and_review_boundaries_are_present(self) -> None:
        for phrase in (
            "accessible name",
            "Keyboard focus",
            "reduced-motion",
            "44 px",
            "raw exceptions",
            "credentials",
            "visual regression evidence",
            "one primary action",
            "Unmigrated screens remain follow-up work",
        ):
            self.assertIn(phrase, self.contract)
        self.assertNotRegex(
            self.contract,
            re.compile(r"(?i)(bearer\s+[a-z0-9._-]{12,}|sk-[a-z0-9]{12,})"),
        )


if __name__ == "__main__":
    unittest.main()
