"""Focused validation for GUI wireframe and mockup artifacts."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WIREFRAME_PATH = ROOT / "docs" / "GUI_WIREFRAMES.md"
MOCKUP_PATH = ROOT / "docs" / "mockups" / "orville-control-center.html"


class GuiWireframesMockupTests(unittest.TestCase):
    """Verify that pre-implementation visual artifacts cover the core GUI contract."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.wireframes = WIREFRAME_PATH.read_text(encoding="utf-8")
        cls.mockup = MOCKUP_PATH.read_text(encoding="utf-8")

    def test_wireframes_cover_primary_surfaces_and_states(self) -> None:
        for surface in ("Global shell", "Home and readiness", "New objective", "Run and verification", "Artifact and provider surfaces"):
            self.assertIn(surface, self.wireframes)
        for state in ("Empty", "loading", "offline", "blocked", "failed"):
            self.assertIn(state, self.wireframes)
        for region in ("navigation", "Main content", "Context rail", "Task graph", "Evidence"):
            self.assertIn(region, self.wireframes)

    def test_mockup_is_standalone_and_has_semantic_structure(self) -> None:
        for marker in ('<!doctype html>', '<html lang="en">', '<meta name="viewport"', '<nav aria-label="Primary navigation">', '<main id="home">', '<aside aria-label="Context rail">'):
            self.assertIn(marker, self.mockup)
        for label in ("Home", "Projects", "New objective", "Activity", "Providers", "Settings", "Help"):
            self.assertIn(label, self.mockup)

    def test_mockup_uses_responsive_and_design_system_behaviors(self) -> None:
        for marker in ("--canvas", "--surface", "--accent", "--focus", "prefers-reduced-motion", "max-width:980px", "max-width:790px", "44px"):
            self.assertIn(marker, self.mockup if marker != "44px" else self.wireframes + self.mockup)
        self.assertIn("focus-visible", self.mockup)
        self.assertIn("aria-label=\"Verification progress\"", self.mockup)

    def test_visual_review_gate_and_secret_safety_are_explicit(self) -> None:
        for phrase in ("reviewed before high-fidelity implementation begins", "one primary action", "approval boundary", "never expose credentials", "Local-only"):
            self.assertIn(phrase, self.wireframes + self.mockup)
        self.assertNotRegex(
            self.wireframes + self.mockup,
            re.compile(r"(?i)(bearer\s+[a-z0-9._-]{12,}|sk-[a-z0-9]{12,})"),
        )


if __name__ == "__main__":
    unittest.main()
