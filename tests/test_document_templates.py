"""Focused validation for the document template contract."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "docs" / "DOCUMENT_TEMPLATES.md"


class DocumentTemplateTests(unittest.TestCase):
    """Verify that each required document type has a complete safe template."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.templates = TEMPLATE_PATH.read_text(encoding="utf-8")

    def test_shared_header_defines_required_metadata(self) -> None:
        for field in (
            "title",
            "document_type",
            "status",
            "owner",
            "created",
            "last_updated",
            "version",
            "audience",
            "project_id",
        ):
            self.assertIn(f"{field}:", self.templates)
        for status in ("draft", "in_review", "approved", "superseded"):
            self.assertIn(status, self.templates)

    def test_all_required_document_types_have_template_sections(self) -> None:
        for document_type, heading in (
            ("report", "## Report template"),
            ("specification", "## Specification template"),
            ("runbook", "## Runbook template"),
            ("research", "## Research output template"),
        ):
            self.assertIn(document_type, self.templates)
            self.assertIn(heading, self.templates)
        for heading in (
            "## Executive summary",
            "## Requirements",
            "## Procedure",
            "## Methodology and source hierarchy",
            "## References",
        ):
            self.assertIn(heading, self.templates)

    def test_templates_require_validation_and_operational_boundaries(self) -> None:
        for phrase in (
            "acceptance test",
            "Security and privacy",
            "Validation plan",
            "Rollback and recovery",
            "Evidence and handoff",
            "independent reviewer",
            "explicit approval gate",
            "unresolved risks",
        ):
            self.assertIn(phrase, self.templates)

    def test_templates_are_secret_safe_and_use_deterministic_names(self) -> None:
        for phrase in (
            "Do not place credentials",
            "safe identifiers",
            "lowercase kebab-case",
            "Do not use `final-final`",
            "source templates under `docs/`",
        ):
            self.assertIn(phrase, self.templates)
        self.assertNotRegex(
            self.templates,
            re.compile(r"(?i)(bearer\s+[a-z0-9._-]{12,}|sk-[a-z0-9]{12,})"),
        )


if __name__ == "__main__":
    unittest.main()
