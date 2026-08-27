from __future__ import annotations

from pathlib import Path
import re
import unittest

from tests.repository_references import resolve_repository_reference


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ORCHESTRATION_TEST_MATRIX.md"
REQUIRED_CAPABILITIES = (
    "Orchestration",
    "Delegation",
    "Graph dependencies",
    "Retries",
    "Failures",
    "Approvals",
    "Integration",
)


class OrchestrationTestMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = DOC.read_text(encoding="utf-8")

    def test_required_capabilities_are_present(self) -> None:
        for capability in REQUIRED_CAPABILITIES:
            self.assertIn(f"| {capability} |", self.text)

    def test_each_matrix_row_references_existing_test_modules(self) -> None:
        rows = [line for line in self.text.splitlines() if line.startswith("|") and "tests/" in line]
        self.assertGreaterEqual(len(rows), len(REQUIRED_CAPABILITIES))
        for row in rows:
            references = re.findall(r"`(tests/[^`]+\.py)`", row)
            self.assertTrue(references, row)
            for reference in references:
                self.assertTrue(resolve_repository_reference(ROOT, reference).is_file(), reference)

    def test_matrix_has_deterministic_execution_and_safety_gates(self) -> None:
        for phrase in (
            "Focused matrix",
            "Behavioral subset",
            "Security subset",
            "Full configured suite",
            "synthetic identifiers",
            "local loopback endpoints",
            "must not load credentials",
            "every failure is triaged",
        ):
            self.assertIn(phrase, self.text)

    def test_matrix_does_not_claim_live_external_validation(self) -> None:
        self.assertIn("does not claim live provider authorization", self.text)
        self.assertIn("deployment-owned extension", self.text)


if __name__ == "__main__":
    unittest.main()
