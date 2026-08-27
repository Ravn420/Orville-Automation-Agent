"""Focused validation for the task composer prototype."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPOSER_PATH = ROOT / "docs" / "mockups" / "task-composer.html"


class TaskComposerTests(unittest.TestCase):
    """Verify that the composer captures a safe, reviewable task draft."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.composer = COMPOSER_PATH.read_text(encoding="utf-8")

    def test_required_composer_inputs_are_present(self) -> None:
        for marker in (
            'id="objective"',
            'id="deliverables"',
            'id="context"',
            'id="files" type="file" multiple',
            'id="environment"',
            'id="model"',
            'id="constraints"',
            'id="criterion"',
            'id="acceptance-title"',
            'id="review"',
        ):
            self.assertIn(marker, self.composer)

    def test_composer_supports_local_file_references_and_criteria(self) -> None:
        for marker in ("Files are referenced locally", "file-list", "add-criterion", "criteria-list", "acceptance_criteria"):
            self.assertIn(marker, self.composer)
        self.assertIn("One criterion per line", self.composer) if "One criterion per line" in self.composer else self.assertIn("Add criterion", self.composer)

    def test_review_is_gated_and_draft_persistence_is_local(self) -> None:
        for marker in (
            "Complete the objective and at least one acceptance criterion",
            "Add an objective and at least one acceptance criterion before review",
            "Ready for task-graph review",
            'localStorage.setItem(key, JSON.stringify(draft()))',
            "No external request was made",
        ):
            self.assertIn(marker, self.composer)

    def test_constraints_and_credentials_are_safe(self) -> None:
        for phrase in (
            "Privacy",
            "External execution, publication, and deployment require separate approval",
            "Provider credentials remain outside this draft",
            "No task has executed",
        ):
            self.assertIn(phrase, self.composer)
        self.assertNotRegex(
            self.composer,
            re.compile(r"(?i)(bearer\s+[a-z0-9._-]{12,}|sk-[a-z0-9]{12,})"),
        )


if __name__ == "__main__":
    unittest.main()
