"""Focused validation for the media visual-verification contract."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs" / "MEDIA_VISUAL_VERIFICATION.md"


class MediaVisualVerificationTests(unittest.TestCase):
    """Verify deterministic, artifact-specific media acceptance rules."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = CONTRACT_PATH.read_text(encoding="utf-8")

    def test_record_and_review_workflow_are_explicit(self) -> None:
        for field in (
            "asset_id",
            "artifact_type",
            "technical result",
            "quality result",
            "accessibility result",
            "rights/provenance result",
            "security/privacy result",
            "sanitized evidence",
            "ACCEPTED",
            "NEEDS_REVIEW",
            "REJECTED",
        ):
            self.assertIn(field, self.contract)
        for phrase in ("second reviewer", "complete artifact", "source and output checksums"):
            self.assertIn(phrase, self.contract)

    def test_each_artifact_has_quality_and_accessibility_checks(self) -> None:
        for artifact in ("| image |", "| audio |", "| video |", "| document |", "| animation |", "| mixed |"):
            self.assertIn(artifact, self.contract)
        for phrase in ("waveform/spectrograms", "Captions/subtitles", "Heading structure", "Static frame", "strictest alternative"):
            self.assertIn(phrase, self.contract)

    def test_defects_fail_closed_and_secret_safe(self) -> None:
        for phrase in ("| CRITICAL |", "| MAJOR |", "| MINOR |", "Reject", "exposed secret/private data", "full-artifact human inspection"):
            self.assertIn(phrase, self.contract)
        self.assertNotRegex(self.contract, re.compile(r"(?i)(bearer\s+[a-z0-9._-]{12,}|sk-[a-z0-9]{12,})"))


if __name__ == "__main__":
    unittest.main()
