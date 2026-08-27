"""Focused checks for the web and mobile acceptance-criteria document."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


DOCUMENT = Path(__file__).resolve().parents[1] / "docs" / "WEB_MOBILE_ACCEPTANCE_CRITERIA.md"


class WebMobileAcceptanceCriteriaTests(unittest.TestCase):
    """Ensure the release criteria remain measurable and security-aware."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.text = DOCUMENT.read_text(encoding="utf-8")

    def test_required_quality_domains_and_target_matrix_are_present(self) -> None:
        for heading in (
            "## Supported target matrix",
            "## Responsive design criteria",
            "## Accessibility criteria",
            "## Security criteria",
            "## Performance criteria",
            "## Release evidence and validation sequence",
        ):
            self.assertIn(heading, self.text)
        for viewport in ("320 CSS px", "390 CSS px", "768 CSS px", "1024 CSS px", "1280 CSS px"):
            self.assertIn(viewport, self.text)

    def test_criteria_include_measurable_accessibility_security_and_performance_gates(self) -> None:
        for phrase in (
            "WCAG 2.2 Level AA",
            "4.5:1",
            "44 by 44 CSS px",
            "Content Security Policy",
            "localStorage",
            "provider credentials",
            "LCP",
            "2.5 seconds",
            "INP",
            "200 ms",
            "CLS",
            "0.1",
            "250 KB compressed JavaScript",
        ):
            self.assertIn(phrase, self.text)

    def test_acceptance_ids_are_unique_and_secrets_are_explicitly_excluded(self) -> None:
        ids = re.findall(r"\| ([RASP]-\d{2}) \|", self.text)
        self.assertGreaterEqual(len(ids), 20)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("must not contain provider credentials", self.text)
        self.assertIn("never credentials", self.text)
        self.assertIn("A failed criterion blocks completion", self.text)


if __name__ == "__main__":
    unittest.main()
