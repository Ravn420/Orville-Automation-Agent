from __future__ import annotations

from pathlib import Path, PurePosixPath
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "READINESS_REPORT.md"


class ReadinessReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = REPORT.read_text(encoding="utf-8")

    def test_report_has_current_status_and_required_readiness_domains(self) -> None:
        for phrase in (
            "## Executive status",
            "## Current readiness checks",
            "## Readiness by target",
            "## Recent architecture and operations changes reflected",
            "## Blocking findings and actions",
            "## Report maintenance",
        ):
            self.assertIn(phrase, self.text)

    def test_report_covers_all_supported_targets_and_key_gates(self) -> None:
        for phrase in (
            "Sandbox",
            "Attached desktop",
            "Web hosting",
            "Persistent computing",
            "Source compilation",
            "Full regression suite",
            "API readiness contract",
            "Adapter readiness",
            "Deployment preflight",
            "Deployment smoke",
            "Security controls",
            "Operational evidence",
        ):
            self.assertIn(phrase, self.text)

    def test_report_preserves_known_blockers_and_safe_boundaries(self) -> None:
        for phrase in (
            "task_status",
            "explicit confirmation",
            "named-path deletion list",
            "does not claim production readiness",
            "protected runtime configuration",
            "redact evidence",
        ):
            self.assertIn(phrase, self.text)
        self.assertNotRegex(self.text, r"(?i)sk-[A-Za-z0-9]{12,}|Bearer\s+[A-Za-z0-9._-]{8,}|api[_-]?key\s*=\s*[^\s,]+")

    def test_reproduction_commands_reference_existing_tools_and_tests(self) -> None:
        for relative_path in (
            "tools/project_checks.py",
            "tools/deployment_validation.py",
            "tests/test_readiness.py",
        ):
            self.assertTrue(ROOT.joinpath(*PurePosixPath(relative_path).parts).is_file(), relative_path)
        for command in (
            "python tools\\project_checks.py test",
            "python tools\\project_checks.py preview",
            "python tools\\deployment_validation.py preflight --target sandbox",
            "python -m unittest tests.test_readiness -v",
        ):
            self.assertIn(command, self.text)


if __name__ == "__main__":
    unittest.main()
