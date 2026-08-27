"""Focused validation for GUI theme and status behavior."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MOCKUP_PATH = ROOT / "docs" / "mockups" / "orville-control-center.html"
CONTRACT_PATH = ROOT / "docs" / "THEME_AND_STATUS_BEHAVIOR.md"


class ThemeAndStatusBehaviorTests(unittest.TestCase):
    """Verify theme persistence and status semantics are explicit and safe."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.mockup = MOCKUP_PATH.read_text(encoding="utf-8")
        cls.contract = CONTRACT_PATH.read_text(encoding="utf-8")

    def test_mockup_implements_two_themes_and_persisted_preference(self) -> None:
        for marker in (
            '[data-theme="dark"]',
            "orville-theme",
            'saved === "dark" || saved === "light"',
            "localStorage.setItem",
            'aria-pressed="false"',
            "Use dark theme",
            "Use light theme",
        ):
            self.assertIn(marker, self.mockup)
        self.assertIn("Invalid, missing, or inaccessible preference values fall back to light", self.contract)

    def test_semantic_tokens_and_reduced_motion_are_defined(self) -> None:
        for token in ("--canvas", "--surface", "--text", "--muted", "--border", "--accent", "--focus", "--success", "--warning", "--danger"):
            self.assertIn(token, self.mockup + self.contract)
        for phrase in ("same semantic token roles", "sufficient contrast", "reduced motion", "non-secret client setting"):
            self.assertIn(phrase, self.contract)

    def test_status_states_have_labels_and_bounded_actions(self) -> None:
        for state in ("ready", "running", "needs_review", "blocked", "failed", "stale", "unavailable", "approval_required"):
            self.assertIn(f"`{state}`", self.contract)
        for phrase in ("text label", "must not be communicated only through hue", "bounded remediation", "do not execute implicitly"):
            self.assertIn(phrase, self.contract)
        self.assertRegex(self.mockup, re.compile(r"class=\"status\"[^>]*>[^<]+<"))

    def test_theme_preference_and_status_output_are_secret_safe(self) -> None:
        combined = self.mockup + self.contract
        self.assertIn("credentials", combined)
        self.assertIn("raw exceptions", combined)
        self.assertNotRegex(combined, re.compile(r"(?i)(bearer\s+[a-z0-9._-]{12,}|sk-[a-z0-9]{12,})"))


if __name__ == "__main__":
    unittest.main()
