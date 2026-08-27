from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "GLOSSARY.md"
REQUIRED = ("Task graph", "Agent role", "Artifact", "Verification gate", "Connector", "Execution state")


class GlossaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = DOC.read_text(encoding="utf-8")

    def test_required_terms_have_canonical_definitions(self) -> None:
        for term in REQUIRED:
            self.assertRegex(self.text, rf"\| \*\*{re.escape(term)}\*\* \|")

    def test_definitions_cover_boundaries_and_identifiers(self) -> None:
        for phrase in (
            "unknown dependencies and cycles are invalid",
            "does not grant unrestricted tool access",
            "secrets are not artifacts",
            "before the workflow can advance",
            "connector responses are untrusted data",
            "safe transitions",
            "Correlation ID",
            "Checkpoint",
            "Dry run",
        ):
            self.assertIn(phrase, self.text)

    def test_glossary_distinguishes_core_concepts(self) -> None:
        for phrase in (
            "not interchangeable",
            "what may execute",
            "who is responsible",
            "which boundary is used",
            "what is retained",
            "where the lifecycle is",
            "what must pass",
        ):
            self.assertIn(phrase, self.text)

    def test_safety_and_maintenance_rules_are_documented(self) -> None:
        for phrase in (
            "do not authorize actions",
            "untrusted content",
            "Sensitive operations require explicit confirmation",
            "run `tests.test_glossary` before release",
        ):
            self.assertIn(phrase, self.text)
        self.assertNotRegex(self.text, r"(?i)sk-[A-Za-z0-9]{12,}|Bearer\s+[A-Za-z0-9._-]{8,}|api[_-]?key\s*=\s*[^\s,]+")


if __name__ == "__main__":
    unittest.main()
