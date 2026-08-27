"""Focused tests for responsive native desktop layouts."""

from __future__ import annotations

import unittest
from pathlib import Path


class ResponsiveLayoutTests(unittest.TestCase):
    """Verify width-aware reflow keeps the primary workflow available."""

    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).resolve().parents[1]
        cls.source = (root / "windows_gui.py").read_text(encoding="utf-8")
        cls.document = (root / "docs" / "RESPONSIVE_LAYOUTS.md").read_text(encoding="utf-8")

    def test_dashboard_has_content_driven_reflow_thresholds(self) -> None:
        for phrase in ('columns = 3 if width >= 1080 else 2 if width >= 790 else 1', 'card.grid(row=index // columns', 'columnspan=columns'):
            self.assertIn(phrase, self.source)
        for phrase in ('1080 px', '980–1079 px', '790–979 px', 'Below 790 px'):
            self.assertIn(phrase, self.document)

    def test_shell_collapses_secondary_regions_at_existing_thresholds(self) -> None:
        self.assertIn('if width < 980 and self.context_visible:', self.source)
        self.assertIn('if width < 790 and self.sidebar_visible:', self.source)
        self.assertIn('the primary objective workspace remains visible.', self.document)

    def test_cards_wrap_and_refresh_follows_final_row(self) -> None:
        self.assertIn('wraplength=180', self.source)
        self.assertIn('refresh_row = (len(self.dashboard_cards) + columns - 1) // columns', self.source)
        for phrase in ('wrap rather than clip', 'without network requests', 'No destructive action is introduced by resizing'):
            self.assertIn(phrase, self.document)


if __name__ == "__main__":
    unittest.main()
