"""Focused validation for the asset lifecycle procedure contract."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCEDURES_PATH = ROOT / "docs" / "ASSET_LIFECYCLE_PROCEDURES.md"


class AssetLifecycleProcedureTests(unittest.TestCase):
    """Verify that asset work has deterministic, rights-aware lifecycle rules."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.procedures = PROCEDURES_PATH.read_text(encoding="utf-8")

    def test_brief_captures_generation_constraints_and_acceptance(self) -> None:
        for field in (
            "asset_id",
            "asset_type",
            "purpose",
            "dimensions_or_duration",
            "format",
            "source_inputs",
            "generation_or_edit_plan",
            "license_constraints",
            "storage_class",
            "acceptance_checks",
            "approval_gate",
        ):
            self.assertIn(f"`{field}`", self.procedures)
        self.assertIn("A missing asset type, purpose, output constraint", self.procedures)
        self.assertIn("blocks generation", self.procedures)

    def test_workflow_preserves_sources_and_records_transformations(self) -> None:
        for phrase in (
            "Preserve originals as immutable sources",
            "new derived versions rather than overwriting a source",
            "input checksum",
            "output checksum",
            "validation result",
            "path-containment checks",
        ):
            self.assertIn(phrase, self.procedures)

    def test_licensing_states_fail_closed_for_unknown_rights(self) -> None:
        for state in (
            "user_owned",
            "licensed",
            "public_domain",
            "generated_with_terms",
            "unknown",
            "restricted",
        ):
            self.assertIn(f"`{state}`", self.procedures)
        self.assertIn("blocked from delivery or publication", self.procedures)
        self.assertIn("must not claim copyright ownership", self.procedures)

    def test_naming_storage_and_secret_boundaries_are_explicit(self) -> None:
        self.assertIn("<asset-id>--<descriptive-slug>--v<major>.<minor>.<extension>", self.procedures)
        for path in (
            "tmp/assets/<task-id>/",
            "artifacts/assets/<asset-id>/",
            "artifacts/",
            "logs/",
        ):
            self.assertIn(path, self.procedures)
        for phrase in (
            "must not be committed by default",
            "must never be stored in these directories",
            "credentials",
            "raw private data",
        ):
            self.assertIn(phrase, self.procedures)
        self.assertNotRegex(
            self.procedures,
            re.compile(r"(?i)(bearer\s+[a-z0-9._-]{12,}|sk-[a-z0-9]{12,})"),
        )


if __name__ == "__main__":
    unittest.main()
