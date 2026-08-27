from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs" / "HELP_AND_RECOVERY_GUIDANCE.md"
MOCKUP_PATH = ROOT / "docs" / "mockups" / "help-recovery.html"


class HelpAndRecoveryTests(unittest.TestCase):
    """Verify user guidance is actionable, accessible, and secret-safe."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = CONTRACT_PATH.read_text(encoding="utf-8")
        cls.mockup = MOCKUP_PATH.read_text(encoding="utf-8")

    def test_contract_covers_help_onboarding_errors_and_recovery(self) -> None:
        for phrase in (
            "Onboarding",
            "Contextual help",
            "Error message",
            "Confirmation",
            "Recovery action",
            "What is this? What is required? What can I do next?",
            "Operation:",
            "Resume",
            "retry",
            "cancel",
            "reconcile",
            "escalate",
        ):
            self.assertIn(phrase, self.contract)

    def test_all_required_states_and_safe_error_boundary_are_documented(self) -> None:
        for phrase in (
            "Loading",
            "Empty",
            "Offline/unavailable",
            "Blocked/approval required",
            "Failed",
            "Partial",
            "Long-running",
            "raw exceptions",
            "response bodies",
            "absolute local paths",
            "secret-bearing URLs",
            "without stealing focus",
            "future localization",
        ):
            self.assertIn(phrase, self.contract)
        self.assertNotRegex(
            self.contract,
            re.compile(r"(?i)(bearer\s+[a-z0-9._-]{12,}|sk-[a-z0-9]{12,})"),
        )

    def test_mockup_has_accessible_help_errors_confirmation_and_recovery_controls(self) -> None:
        for phrase in (
            'lang="en"',
            'aria-label="Explain privacy mode"',
            'role="alert"',
            'aria-live="polite"',
            "Confirm resume",
            "Not now",
            "Resume checkpoint",
            "Retry failed task",
            "Cancel and preserve evidence",
            "prefers-reduced-motion",
            "Operation: CFG-ENDPOINT-LOCAL",
        ):
            self.assertIn(phrase, self.mockup)
        self.assertNotRegex(
            self.mockup,
            re.compile(r"(?i)(bearer\s+[a-z0-9._-]{12,}|sk-[a-z0-9]{12,})"),
        )

    def test_confirmation_does_not_execute_external_actions(self) -> None:
        for phrase in (
            "no external action was taken",
            "no task was executed",
            "no retry was started",
            "evidence remain preserved",
        ):
            self.assertIn(phrase, self.mockup)
        self.assertNotIn("fetch(", self.mockup)
        self.assertNotIn("XMLHttpRequest", self.mockup)


if __name__ == "__main__":
    unittest.main()
