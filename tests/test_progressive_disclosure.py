"""Focused tests for progressive disclosure of advanced workflow options."""

from __future__ import annotations

import unittest
from pathlib import Path


class ProgressiveDisclosureTests(unittest.TestCase):
    """Verify advanced options are explicit, bounded, and reversible."""

    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).resolve().parents[1]
        cls.source = (root / "windows_gui.py").read_text(encoding="utf-8")
        cls.document = (root / "docs" / "PROGRESSIVE_DISCLOSURE.md").read_text(encoding="utf-8")

    def test_provider_setup_defaults_to_collapsed_advanced_options(self) -> None:
        self.assertIn('advanced_visible = tk.BooleanVar(value=False)', self.source)
        self.assertIn('text="Show advanced options"', self.source)
        self.assertIn('toggle_advanced()', self.source)

    def test_disclosure_is_reversible_and_preserves_values(self) -> None:
        self.assertIn('widget.grid_remove()', self.source)
        self.assertIn('widget.grid()', self.source)
        self.assertIn('advanced_widgets.extend', self.source)
        self.assertIn('Advanced options stay hidden until requested.', self.source)

    def test_contract_preserves_safety_and_accessibility_boundaries(self) -> None:
        for phrase in ("MUST be hidden", "MUST be reversible", "Credentials remain masked", "approval", "keyboard-addressable", "safe error feedback"):
            self.assertIn(phrase, self.document)


if __name__ == "__main__":
    unittest.main()
