"""Focused validation for editable-source preservation rules."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = ROOT / "docs" / "EDITABLE_SOURCE_PRESERVATION.md"


class EditableSourcePreservationTests(unittest.TestCase):
    """Verify that editable sources remain linked to validated exports."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.rules = RULES_PATH.read_text(encoding="utf-8")

    def test_manifest_captures_source_and_export_relationships(self) -> None:
        for field in (
            "artifact_id",
            "source_path",
            "source_format",
            "source_checksum",
            "exports",
            "source_version",
            "relationships",
            "retention_class",
            "validation",
            "approval_reference",
        ):
            self.assertIn(f"`{field}`", self.rules)
        for phrase in (
            "An export is a delivery derivative",
            "Never overwrite the editable source",
            "source checksum",
            "each export checksum",
        ):
            self.assertIn(phrase, self.rules)

    def test_versions_and_fallback_are_explicit(self) -> None:
        for phrase in (
            "immutable source version",
            "source_path: null",
            "source_format: unavailable",
            "highest-fidelity non-editable origin",
            "lossy export",
            "limitation is disclosed",
        ):
            self.assertIn(phrase, self.rules)

    def test_storage_paths_and_safety_boundaries_are_defined(self) -> None:
        for path in (
            "artifacts/<artifact-id>/source/",
            "artifacts/<artifact-id>/exports/",
            "artifacts/<artifact-id>/manifest.json",
            "tmp/",
        ):
            self.assertIn(path, self.rules)
        for phrase in (
            "lowercase kebab-case",
            "path-containment checks",
            "not retained in source control",
            "External sharing, publication",
        ):
            self.assertIn(phrase, self.rules)

    def test_validation_and_completion_gates_are_fail_closed(self) -> None:
        for phrase in (
            "successful open/parse check",
            "Page, slide, frame, duration",
            "source was not overwritten",
            "A second review confirms",
            "needs_review",
            "checksum mismatch",
        ):
            self.assertIn(phrase, self.rules)
        self.assertNotRegex(
            self.rules,
            re.compile(r"(?i)(bearer\s+[a-z0-9._-]{12,}|sk-[a-z0-9]{12,})"),
        )


if __name__ == "__main__":
    unittest.main()
