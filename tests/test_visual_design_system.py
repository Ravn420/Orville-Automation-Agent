"""Focused checks for the Orville visual design system."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class VisualDesignSystemTests(unittest.TestCase):
    """Verify shared tokens and component-state coverage."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tokens = json.loads((ROOT / "config" / "design-system.example.json").read_text(encoding="utf-8"))
        cls.document = (ROOT / "docs" / "VISUAL_DESIGN_SYSTEM.md").read_text(encoding="utf-8")

    def test_tokens_cover_foundation_and_theme_requirements(self) -> None:
        for section in ("font", "color", "spacing_px", "elevation", "icon", "control", "motion", "breakpoints_px"):
            self.assertIn(section, self.tokens)
        for theme in ("light", "dark"):
            for role in ("canvas", "surface", "text", "muted", "border", "accent", "focus", "success", "warning", "danger"):
                self.assertIn(role, self.tokens["color"][theme])
        self.assertGreaterEqual(self.tokens["control"]["min_touch_target_px"], 44)

    def test_document_covers_required_components_and_states(self) -> None:
        for component in ("Button", "Text input", "Form", "Table", "Card", "Notification", "Dialog", "Empty state", "Status badge", "Navigation"):
            self.assertIn(component, self.document)
        for state in ("hover", "focus-visible", "disabled", "loading", "invalid", "error", "empty", "reduced motion"):
            self.assertIn(state, self.document)

    def test_document_preserves_security_and_responsive_boundaries(self) -> None:
        for phrase in ("44 px", "320 px", "bearer tokens", "Do not introduce one-off colors", "raw exceptions", "Light and dark themes"):
            self.assertIn(phrase, self.document)


if __name__ == "__main__":
    unittest.main()
