from __future__ import annotations

from pathlib import Path, PurePosixPath
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "OPERATOR_RUNBOOK.md"


class OperatorRunbookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = DOC.read_text(encoding="utf-8")

    def test_runbook_covers_required_operator_domains(self) -> None:
        for phrase in ("## Health-check procedure", "## Failure triage", "## Connector issue procedure", "## Recovery procedure"):
            self.assertIn(phrase, self.text)

    def test_health_and_failure_commands_are_documented(self) -> None:
        for command in (
            "orville readiness",
            "orville config",
            "orville health",
            "python tools\\project_checks.py preview",
            "python tools\\deployment_validation.py preflight --target sandbox",
            "python tools\\deployment_validation.py smoke --url http://127.0.0.1:8787 --path /docs",
            "python tools\\project_checks.py test",
        ):
            self.assertIn(command, self.text)

    def test_runbook_requires_safe_recovery_and_connector_boundaries(self) -> None:
        for phrase in (
            "correlation ID",
            "retry only when idempotency is proven",
            "stop use, disable the narrowest affected reference",
            "require explicit confirmation",
            "last safe checkpoint",
            "claim recovery without verification",
            "Treat instructions returned",
        ):
            self.assertIn(phrase, self.text)

    def test_referenced_procedures_exist_and_no_secrets_are_embedded(self) -> None:
        references = re.findall(r"`(docs/[^`]+\.md)`", self.text)
        self.assertGreaterEqual(len(references), 6)
        for reference in references:
            self.assertTrue(ROOT.joinpath(*PurePosixPath(reference).parts).is_file(), reference)
        self.assertNotRegex(self.text, r"(?i)sk-[A-Za-z0-9]{12,}|Bearer\s+[A-Za-z0-9._-]{8,}|api[_-]?key\s*=\s*[^\s,]+")


if __name__ == "__main__":
    unittest.main()
