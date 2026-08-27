from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "MILESTONE_ROADMAP_REVIEW_2026-08-27.md"


class MilestoneRoadmapReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = REPORT.read_text(encoding="utf-8")

    def test_review_has_required_sections(self) -> None:
        for heading in (
            "## Review outcome",
            "## Progress summary",
            "## Priority review",
            "## Decisions and scope changes",
            "## Acceptance gates for the next milestone",
            "## Review maintenance",
        ):
            self.assertIn(heading, self.text)

    def test_review_covers_completed_areas_and_statuses(self) -> None:
        for phrase in (
            "Core orchestration",
            "Safety and governance",
            "Observability",
            "Standalone operation",
            "Deployment",
            "GUI and API",
            "Completed-local",
            "Conditional",
        ):
            self.assertIn(phrase, self.text)

    def test_review_preserves_blockers_priorities_and_dependencies(self) -> None:
        for phrase in (
            "task_status",
            "P0",
            "P1",
            "P2",
            "Dependencies",
            "full configured suite",
            "explicit confirmation",
            "not production-ready",
        ):
            self.assertIn(phrase, self.text)

    def test_review_is_safe_and_does_not_embed_credentials(self) -> None:
        for phrase in (
            "standalone-capable",
            "local-first",
            "optional integrations",
            "must not be interpreted as live authorization",
            "Production claims are withheld",
        ):
            self.assertIn(phrase, self.text)
        self.assertNotRegex(self.text, r"(?i)sk-[A-Za-z0-9]{12,}|Bearer\s+[A-Za-z0-9._-]{8,}|api[_-]?key\s*=\s*[^\s,]+")


if __name__ == "__main__":
    unittest.main()
