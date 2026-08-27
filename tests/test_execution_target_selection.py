from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "EXECUTION_TARGET_SELECTION.md"


class ExecutionTargetSelectionTests(unittest.TestCase):
    """Verify the documented execution-target decision contract."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.document = DOC.read_text(encoding="utf-8")

    def test_all_targets_and_selection_signals_are_defined(self) -> None:
        for phrase in (
            "`sandbox`",
            "`web_hosting`",
            "`attached_desktop`",
            "`persistent_computing`",
            "one-shot",
            "recurring",
            "event-triggered",
            "webhook-driven",
            "persistent service",
            "Docker",
            "fixed network identity",
            "native Windows GUI",
        ):
            self.assertIn(phrase, self.document)

    def test_decision_procedure_and_matrix_cover_boundaries(self) -> None:
        for phrase in (
            "Decision procedure",
            "Decision matrix",
            "smallest execution target",
            "managed web hosting",
            "must remain online",
            "resource requirements beyond managed hosting",
            "data-residency constraints",
            "approval gates",
            "idempotency",
            "rollback",
        ):
            self.assertIn(phrase, self.document)

    def test_security_and_escalation_rules_are_explicit(self) -> None:
        for phrase in (
            "never place them in the GUI",
            "Do not purchase infrastructure",
            "leave the task blocked",
            "safe alternatives",
            "credential-free local checks",
            "environment-specific release checks",
            "target mismatch is a planning blocker",
        ):
            self.assertIn(phrase, self.document)
        self.assertNotIn("sk-", self.document)
        self.assertNotIn("Bearer ey", self.document)


if __name__ == "__main__":
    unittest.main()
