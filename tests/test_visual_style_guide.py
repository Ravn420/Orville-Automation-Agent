"""Focused checks for the polished visual-style contract."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class VisualStyleGuideTests(unittest.TestCase):
    """Verify style-profile safeguards and review-gate coverage."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = json.loads((ROOT / "config" / "visual-style.example.json").read_text(encoding="utf-8"))
        cls.document = (ROOT / "docs" / "VISUAL_STYLE_GUIDE.md").read_text(encoding="utf-8")

    def test_profile_has_polished_style_and_performance_safeguards(self) -> None:
        self.assertEqual(self.profile["voice"]["qualities"], ["professional", "modern", "clear", "calm", "operational"])
        self.assertEqual(self.profile["composition"]["primary_action_per_surface"], 1)
        self.assertLessEqual(self.profile["performance"]["max_decorative_asset_kb"], 100)
        self.assertLessEqual(self.profile["performance"]["max_initial_font_families"], 2)
        self.assertGreaterEqual(self.profile["usability"]["minimum_touch_target_px"], 44)

    def test_guide_covers_required_style_and_usability_domains(self) -> None:
        for phrase in ("Composition and hierarchy", "Visual language", "Performance posture", "Usability and accessibility posture", "Review gates", "Light/dark parity", "Visual regression"):
            self.assertIn(phrase, self.document)

    def test_security_and_performance_boundaries_are_explicit(self) -> None:
        for phrase in ("bearer token", "production data", "reduced motion", "Loading preserves layout dimensions", "320 px", "100 KB"):
            self.assertIn(phrase, self.document)


if __name__ == "__main__":
    unittest.main()
