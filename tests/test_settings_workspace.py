"""Focused validation for the settings workspace prototype."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MOCKUP_PATH = ROOT / "docs" / "mockups" / "settings-workspace.html"
CONTRACT_PATH = ROOT / "docs" / "SETTINGS_WORKSPACE.md"


class SettingsWorkspaceTests(unittest.TestCase):
    """Verify settings coverage and safe persistence boundaries."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.mockup = MOCKUP_PATH.read_text(encoding="utf-8")
        cls.contract = CONTRACT_PATH.read_text(encoding="utf-8")

    def test_all_settings_sections_and_controls_are_present(self) -> None:
        for section in ("providers", "privacy", "storage", "limits", "schedules", "notifications", "preferences"):
            self.assertIn(f'data-section="{section}"', self.mockup)
            self.assertIn(section.lower(), self.contract.lower())
        for control in ("provider", "model", "credential-ref", "routing", "artifact-path", "temp-path", "max-concurrency", "timeout", "schedule", "notify", "theme", "motion"):
            self.assertIn(f'id="{control}"', self.mockup)

    def test_settings_have_bounded_and_labeled_controls(self) -> None:
        for marker in ('type="number" min="1" max="32"', 'type="number" min="1" max="86400"', 'aria-label="Settings sections"', 'role="status"', 'aria-live="polite"'):
            self.assertIn(marker, self.mockup)
        for phrase in ("typed", "schema validation", "path containment", "bounded"):
            self.assertIn(phrase, self.contract)

    def test_local_persistence_is_allowlisted_and_reset_is_non_destructive(self) -> None:
        for marker in ("orville-settings", "localStorage.setItem", "localStorage.removeItem", "Settings saved locally", "Settings reset locally"):
            self.assertIn(marker, self.mockup)
        for phrase in ("allowlisted non-secret settings", "does not delete artifacts", "does not by itself authorize external execution"):
            self.assertIn(phrase, self.contract)

    def test_secrets_and_consequential_changes_are_protected(self) -> None:
        for phrase in ("protected controls or references", "never renders API keys", "separate confirmation or approval", "make no external requests"):
            self.assertIn(phrase, self.contract)
        self.assertNotRegex(
            self.mockup + self.contract,
            re.compile(r"(?i)(bearer\s+[a-z0-9._-]{12,}|sk-[a-z0-9]{12,})"),
        )


if __name__ == "__main__":
    unittest.main()
