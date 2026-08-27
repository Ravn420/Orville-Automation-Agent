"""Focused validation for the artifact browser prototype."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MOCKUP_PATH = ROOT / "docs" / "mockups" / "artifact-browser.html"
CONTRACT_PATH = ROOT / "docs" / "ARTIFACT_BROWSER.md"


class ArtifactBrowserTests(unittest.TestCase):
    """Verify that artifact actions remain versioned, local, and reviewable."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.mockup = MOCKUP_PATH.read_text(encoding="utf-8")
        cls.contract = CONTRACT_PATH.read_text(encoding="utf-8")

    def test_supported_artifact_types_and_library_filters_are_present(self) -> None:
        for artifact_type in ("code", "document", "media", "log", "report"):
            self.assertIn(f'value="{artifact_type}"', self.mockup) if f'value="{artifact_type}"' in self.mockup else self.assertIn(f"`{artifact_type}`", self.contract)
        for marker in ("Search artifacts", "type-filter", "status-filter", "artifact-list", "versioned artifact"):
            self.assertIn(marker, self.mockup + self.contract)

    def test_preview_and_source_export_metadata_are_visible(self) -> None:
        for marker in ("Safe local preview", "Source", "Checksum", "Format", "Rights", "Editable source", "Manifest"):
            self.assertIn(marker, self.mockup + self.contract)
        for phrase in ("does not execute code", "source/export relationship", "missing source", "checksum mismatch"):
            self.assertIn(phrase, self.contract)

    def test_download_export_compare_and_revision_actions_are_non_destructive(self) -> None:
        for marker in ("Download", "Export selected", "Compare version", "Create revision", "download", "compare", "version"):
            self.assertIn(marker, self.mockup)
        for phrase in ("must not overwrite", "Accepted versions remain immutable", "no external publication", "was not overwritten"):
            self.assertIn(phrase, self.mockup + self.contract)

    def test_states_approvals_and_secret_safety_are_explicit(self) -> None:
        for state in ("draft", "needs_review", "accepted", "failed", "unavailable"):
            self.assertIn(f"`{state}`", self.contract)
        for phrase in ("External sharing", "separate approval", "path containment", "safe operation IDs"):
            self.assertIn(phrase, self.mockup + self.contract)
        self.assertNotRegex(
            self.mockup + self.contract,
            re.compile(r"(?i)(bearer\s+[a-z0-9._-]{12,}|sk-[a-z0-9]{12,})"),
        )


if __name__ == "__main__":
    unittest.main()
