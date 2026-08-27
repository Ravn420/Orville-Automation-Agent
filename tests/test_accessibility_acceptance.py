"""Focused validation for accessibility acceptance criteria."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs" / "ACCESSIBILITY_ACCEPTANCE_CRITERIA.md"


class AccessibilityAcceptanceTests(unittest.TestCase):
    """Verify keyboard, semantics, contrast, motion, and error criteria."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = CONTRACT_PATH.read_text(encoding="utf-8")

    def test_required_accessibility_criteria_are_present(self) -> None:
        for phrase in (
            "A11Y-01",
            "A11Y-02",
            "A11Y-03",
            "A11Y-04",
            "A11Y-05",
            "A11Y-06",
            "A11Y-07",
            "A11Y-08",
            "A11Y-09",
            "A11Y-10",
            "keyboard",
            "Focus is visible",
            "accessible name",
            "4.5:1",
            "reduced-motion",
            "44 pixel",
        ):
            self.assertIn(phrase, self.contract)

    def test_critical_workflow_matrix_and_failure_policy_are_present(self) -> None:
        for phrase in (
            "Objective intake",
            "Task plan",
            "Execution monitor",
            "Approval",
            "Model setup",
            "Artifact access",
            "Settings",
            "preserved-input error",
            "partial failure",
            "focus restoration",
            "permission denial",
            "retest date",
        ):
            self.assertIn(phrase, self.contract)

    def test_security_and_error_feedback_boundaries_are_secret_safe(self) -> None:
        for phrase in (
            "failed operation",
            "recovery action",
            "raw exceptions",
            "provider response bodies",
            "credentials",
            "bearer tokens",
            "secret-bearing URLs",
            "Automated audits are screening evidence",
        ):
            self.assertIn(phrase, self.contract)
        self.assertNotRegex(
            self.contract,
            re.compile(r"(?i)(bearer\s+[a-z0-9._-]{12,}|sk-[a-z0-9]{12,})"),
        )


if __name__ == "__main__":
    unittest.main()
