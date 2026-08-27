"""Focused validation for the imported-model workflow contract."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs" / "IMPORTED_MODEL_WORKFLOW.md"


class ImportedModelWorkflowTests(unittest.TestCase):
    """Verify the import, validation, activation, and diagnostics contract."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = CONTRACT_PATH.read_text(encoding="utf-8")

    def test_workflow_stages_cover_required_operations(self) -> None:
        for phrase in (
            "Select source",
            "Choose storage",
            "Scan metadata",
            "Validate compatibility",
            "Review and activate",
            "View diagnostics",
            "Deactivate or remove",
            "reference, copy, or approved link mode",
            "checksum",
            "license restrictions",
        ):
            self.assertIn(phrase, self.contract)

    def test_diagnostics_and_lifecycle_states_are_stable(self) -> None:
        for phrase in (
            "imported",
            "active",
            "inactive",
            "validation-failed",
            "needs-review",
            "code, severity, safe message",
            "unsupported_format",
            "runtime_mismatch",
            "insufficient_vram",
            "attestation_failed",
            "duplicate imports are deterministic",
        ):
            self.assertIn(phrase, self.contract)

    def test_security_and_acceptance_boundaries_are_explicit(self) -> None:
        for phrase in (
            "never uploads the selected path",
            "never executes scripts",
            "API credentials",
            "raw exception text",
            "approved roots",
            "does not delete model files by default",
            "synthetic file import",
            "synthetic folder import",
            "production runtime provisioning",
        ):
            self.assertIn(phrase, self.contract)
        self.assertNotRegex(
            self.contract,
            re.compile(r"(?i)(bearer\s+[a-z0-9._-]{12,}|sk-[a-z0-9]{12,})"),
        )


if __name__ == "__main__":
    unittest.main()
