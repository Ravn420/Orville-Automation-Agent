"""Focused validation for the project initialization rules contract."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = ROOT / "docs" / "PROJECT_INITIALIZATION_RULES.md"


class ProjectInitializationRulesTests(unittest.TestCase):
    """Verify that each supported project profile has deterministic rules."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.rules = RULES_PATH.read_text(encoding="utf-8")

    def test_document_defines_all_supported_profiles(self) -> None:
        for profile, heading in (
            ("static_site", "### Static site"),
            ("full_stack_web", "### Full-stack web application"),
            ("mobile_application", "### Mobile application"),
        ):
            self.assertIn(f"`{profile}`", self.rules)
            self.assertIn(heading, self.rules)

    def test_contract_requires_common_initialization_inputs(self) -> None:
        for field in (
            "project_name",
            "project_type",
            "objective",
            "target_platforms",
            "runtime",
            "package_manager",
            "data_and_auth",
            "preview_method",
            "acceptance_criteria",
            "assumptions",
        ):
            self.assertRegex(self.rules, rf"`{re.escape(field)}`")
        self.assertIn("must fail closed", self.rules)
        self.assertIn("exactly one supported project profile", self.rules)

    def test_security_and_external_side_effect_boundaries_are_explicit(self) -> None:
        for phrase in (
            "must never be generated into a scaffold",
            "outside source control",
            "must be isolated from production data",
            "No device enrollment or store submission is performed automatically",
            "explicitly selects a target and approves external side effects",
        ):
            self.assertIn(phrase, self.rules)
        self.assertNotRegex(
            self.rules,
            re.compile(r"(?i)(bearer\s+[a-z0-9._-]{12,}|sk-[a-z0-9]{12,})"),
        )

    def test_profiles_define_quality_and_preview_requirements(self) -> None:
        for phrase in (
            "build successfully",
            "backend unit tests",
            "compile or bundle",
            "local static preview command",
            "local server command",
            "device/emulator preview procedure",
            "build, test, and preview results",
        ):
            self.assertIn(phrase, self.rules)


if __name__ == "__main__":
    unittest.main()
