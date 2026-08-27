"""Focused tests for the desktop verification and review view."""

from __future__ import annotations

import unittest
from pathlib import Path


class VerificationReviewTests(unittest.TestCase):
    """Verify review coverage without opening a desktop window."""

    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).resolve().parents[1]
        cls.source = (root / "windows_gui.py").read_text(encoding="utf-8")
        cls.document = (root / "docs" / "VERIFICATION_REVIEW_SPECIFICATION.md").read_text(encoding="utf-8")

    def test_review_view_covers_required_evidence_sections(self) -> None:
        for phrase in ("Verification & review", "Acceptance criteria", "Test results", "Source evidence", "Visual checks", "Defects", "Residual risks", "Approval state"):
            self.assertIn(phrase, self.source)
        self.assertIn("Verification", self.source)
        self.assertIn("Refresh review", self.source)

    def test_review_view_reads_persisted_run_evidence(self) -> None:
        for phrase in ("/api/v1/runs/", "context.get(\"verifications\")", "context.get(\"citations\")", "context.get(\"visual_checks\")", "context.get(\"residual_risks\")", "result.get(\"run_status\")"):
            self.assertIn(phrase, self.source)

    def test_review_document_defines_safe_bounded_review_rules(self) -> None:
        for phrase in ("acceptance criteria", "test results", "source evidence", "visual checks", "defects", "residual risks", "approval state", "raw provider configuration", "4,000"):
            self.assertIn(phrase, self.document)


if __name__ == "__main__":
    unittest.main()
