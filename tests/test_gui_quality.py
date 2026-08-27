from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
MOCKUPS = DOCS / "mockups"


class GuiQualityTests(unittest.TestCase):
    """Verify aggregate GUI quality coverage without external services."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.strategy = (DOCS / "GUI_TEST_STRATEGY.md").read_text(encoding="utf-8")
        cls.mockups = {
            path.name: path.read_text(encoding="utf-8")
            for path in sorted(MOCKUPS.glob("*.html"))
        }

    def test_component_contracts_are_present(self) -> None:
        for phrase in (
            "Component",
            "Shared visual and interaction contracts",
            "labels",
            "focus",
            "status",
            "buttons",
            "dialogs",
            "safe messages",
            "VISUAL_DESIGN_SYSTEM.md",
            "REUSABLE_COMPONENTS_INTERACTIONS.md",
        ):
            self.assertIn(phrase, self.strategy)

        self.assertTrue(self.mockups, "GUI mockups must exist for component coverage")
        for name, source in self.mockups.items():
            self.assertIn("<button", source, name)
            self.assertTrue(
                any(marker in source for marker in ("<label", "aria-label=", "aria-labelledby=")),
                name,
            )
            self.assertNotRegex(
                source,
                re.compile(r"(?i)(bearer\s+[a-z0-9._-]{12,}|sk-[a-z0-9]{12,})"),
            )

    def test_major_workflow_surfaces_have_required_contracts(self) -> None:
        required_surfaces = {
            "task-composer.html": ("objective", "acceptance", "review"),
            "generation-workspace.html": ("capability", "model", "review"),
            "model-configuration.html": ("endpoint", "credential", "privacy"),
            "artifact-browser.html": ("preview", "version", "export"),
            "settings-workspace.html": ("privacy", "storage", "notifications"),
            "help-recovery.html": ("onboarding", "recovery", "confirm"),
        }
        for name, markers in required_surfaces.items():
            self.assertIn(name, self.mockups)
            source = self.mockups[name].lower()
            for marker in markers:
                self.assertIn(marker, source, f"{name} lacks workflow marker {marker}")

        for contract in (
            "GUI_INFORMATION_ARCHITECTURE.md",
            "TASK_PLAN_VIEW.md",
            "EXECUTION_MONITOR_SPECIFICATION.md",
            "VERIFICATION_REVIEW_SPECIFICATION.md",
        ):
            self.assertTrue((DOCS / contract).is_file(), contract)

    def test_accessibility_coverage_is_explicit_and_secret_safe(self) -> None:
        for phrase in (
            "accessibility",
            "keyboard",
            "accessible names",
            "focus-visible",
            "live status/error regions",
            "reduced motion",
            "screen-reader",
            "secret-safe",
            "manual assistive-technology review remains required",
        ):
            self.assertIn(phrase.lower(), self.strategy.lower())

        for name, source in self.mockups.items():
            self.assertRegex(source, re.compile(r'(?i)lang="en"'), name)
            self.assertIn("focus-visible", source, name)
            if "prefers-reduced-motion" not in source:
                self.assertIn("reduced-motion", self.strategy.lower(), name)
            self.assertNotRegex(
                source,
                re.compile(r"(?i)(api[_ -]?key\s*[:=]\s*['\"][^'\"]+|bearer\s+[a-z0-9._-]{12,})"),
                name,
            )

    def test_responsive_layout_coverage_is_explicit(self) -> None:
        self.assertIn("Responsive", self.strategy)
        self.assertIn("tablet", self.strategy)
        self.assertIn("compact", self.strategy)
        responsive_contract = (DOCS / "RESPONSIVE_LAYOUTS.md").read_text(encoding="utf-8")
        for phrase in ("desktop", "width", "collapse", "reflow", "keyboard"):
            self.assertIn(phrase, responsive_contract.lower())
        for name, source in self.mockups.items():
            self.assertIn('name="viewport"', source, name)
            self.assertRegex(source, re.compile(r"@media", re.IGNORECASE), name)

    def test_end_to_end_journey_is_ordered_and_gated(self) -> None:
        stages = (
            ("Objective intake", "task-composer.html"),
            ("Plan review", "TASK_PLAN_VIEW.md"),
            ("Execution", "EXECUTION_MONITOR_SPECIFICATION.md"),
            ("Verification", "VERIFICATION_REVIEW_SPECIFICATION.md"),
            ("Delivery", "artifact-browser.html"),
        )
        positions = []
        for label, filename in stages:
            self.assertIn(label, self.strategy)
            path = MOCKUPS / filename if filename.endswith(".html") else DOCS / filename
            self.assertTrue(path.is_file(), filename)
            positions.append(self.strategy.index(label))
        self.assertEqual(positions, sorted(positions))
        for phrase in (
            "reviewable",
            "explicit execution",
            "approval",
            "synthetic IDs",
            "do not submit forms",
            "mutate files outside the repository",
        ):
            self.assertIn(phrase.lower(), self.strategy.lower())


if __name__ == "__main__":
    unittest.main()
