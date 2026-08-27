"""Focused tests for the native Orville GUI accessibility contract."""

from __future__ import annotations

import unittest
from pathlib import Path


class GuiAccessibilityTests(unittest.TestCase):
    """Verify accessible interaction and feedback markers remain present."""

    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).resolve().parents[1]
        cls.source = (root / "windows_gui.py").read_text(encoding="utf-8")
        cls.document = (root / "docs" / "GUI_ACCESSIBILITY.md").read_text(encoding="utf-8")

    def test_keyboard_entry_points_and_focusable_controls(self) -> None:
        for phrase in ('<Alt-Key-1>', '<Alt-Key-2>', '<Escape>', 'takefocus=True', 'Use Tab to move through controls'):
            self.assertIn(phrase, self.source)

    def test_focus_visibility_semantics_and_contrast_markers(self) -> None:
        for phrase in ('highlightthickness=2', 'highlightcolor=self.ACCENT', 'bordercolor=[("focus", self.ACCENT)]', 'Objective workspace'):
            self.assertIn(phrase, self.source)
        for phrase in ('Visible focus', 'Semantic controls and labels', 'Color contrast'):
            self.assertIn(phrase, self.document)

    def test_reduced_motion_and_secret_safe_error_feedback(self) -> None:
        for phrase in ('uses no animated transitions', 'Accessible errors', 'Raw exception text', 'recovery instruction'):
            self.assertIn(phrase, self.document)
        self.assertIn('The objective request could not be completed.', self.source)
        self.assertNotIn('f"Connection error: {exc}"', self.source)
        self.assertNotIn('f"HTTP {exc.code}: {detail}"', self.source)


if __name__ == "__main__":
    unittest.main()
