"""Focused validation for the presentation procedure contract."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCEDURES_PATH = ROOT / "docs" / "PRESENTATION_PROCEDURES.md"


class PresentationProcedureTests(unittest.TestCase):
    """Verify that presentation workflows have deterministic review gates."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.procedures = PROCEDURES_PATH.read_text(encoding="utf-8")

    def test_brief_and_planning_fields_are_defined(self) -> None:
        for field in (
            "deck_id",
            "objective",
            "audience",
            "duration",
            "slide_budget",
            "content_sources",
            "narrative",
            "visual_direction",
            "output_formats",
            "acceptance_criteria",
            "approval_gates",
        ):
            self.assertIn(f"`{field}`", self.procedures)
        for phrase in ("Build the outline", "Map evidence", "Set the design system", "Plan accessibility"):
            self.assertIn(phrase, self.procedures)

    def test_content_validation_covers_evidence_and_claim_integrity(self) -> None:
        for phrase in (
            "each slide advances the objective",
            "Every material number has units",
            "Charts identify axes",
            "Quotations preserve meaning",
            "Placeholder text",
            "blocks export approval",
        ):
            self.assertIn(phrase, self.procedures)

    def test_design_and_accessibility_checks_are_explicit(self) -> None:
        for phrase in (
            "grid alignment",
            "typography hierarchy",
            "reading order",
            "alternative text",
            "sufficient contrast",
            "non-color-only distinctions",
            "reduced-motion behavior",
        ):
            self.assertIn(phrase, self.procedures)

    def test_export_checks_cover_formats_assets_and_delivery_evidence(self) -> None:
        for check in (
            "Editable source",
            "PDF or print export",
            "Web export",
            "Fonts and assets",
            "Charts and images",
            "References and links",
            "Visual sample",
            "Delivery manifest",
        ):
            self.assertIn(check, self.procedures)
        self.assertIn("source version", self.procedures)
        self.assertIn("checksum", self.procedures)
        self.assertIn("explicit approval", self.procedures)
        self.assertNotRegex(
            self.procedures,
            re.compile(r"(?i)(bearer\s+[a-z0-9._-]{12,}|sk-[a-z0-9]{12,})"),
        )


if __name__ == "__main__":
    unittest.main()
