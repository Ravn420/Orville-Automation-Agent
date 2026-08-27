"""Focused tests for plain-language primary workflows."""

from __future__ import annotations

import unittest
from pathlib import Path


class PlainLanguageWorkflowTests(unittest.TestCase):
    """Verify first-run copy does not require framework knowledge."""

    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).resolve().parents[1]
        cls.source = (root / "windows_gui.py").read_text(encoding="utf-8")
        cls.document = (root / "docs" / "PLAIN_LANGUAGE_WORKFLOWS.md").read_text(encoding="utf-8")

    def test_gui_leads_with_plain_language_and_help(self) -> None:
        for phrase in ("What would you like Orville to do?", "Describe a goal in your own words", "Tell Orville what you need", "How Orville works"):
            self.assertIn(phrase, self.source)

    def test_workflow_guide_maps_technical_terms_without_requiring_them(self) -> None:
        for phrase in ("Describe", "Prepare", "Work", "Review", "Task graph", "Provider/model", "not prerequisites"):
            self.assertIn(phrase, self.document)

    def test_workflow_guide_preserves_safety_and_accessibility_boundaries(self) -> None:
        for phrase in ("sensitive actions", "credentials", "Keyboard access", "responsive layout", "safe error feedback", "approval"):
            self.assertIn(phrase, self.document)


if __name__ == "__main__":
    unittest.main()
