"""Focused validation for the capability-aware generation workspace."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MOCKUP_PATH = ROOT / "docs" / "mockups" / "generation-workspace.html"
CONTRACT_PATH = ROOT / "docs" / "GENERATION_WORKSPACE.md"


class GenerationWorkspaceTests(unittest.TestCase):
    """Verify that generation requests are capability-aware and reviewable."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.mockup = MOCKUP_PATH.read_text(encoding="utf-8")
        cls.contract = CONTRACT_PATH.read_text(encoding="utf-8")

    def test_all_supported_capabilities_and_modality_controls_are_defined(self) -> None:
        for capability in ("text", "code", "image", "audio", "video", "vision", "embedding", "other"):
            self.assertIn(f'data-capability="{capability}"', self.mockup)
            self.assertIn(f"`{capability}`", self.contract)
        for control in ("prompt", "input-files", "output-format", "seed", "parameters", "model", "privacy"):
            self.assertIn(f'id="{control}"', self.mockup)

    def test_model_compatibility_is_filtered_from_declared_capabilities(self) -> None:
        for marker in ("data-capabilities", "compatible", "Only models supporting the selected capability", "updateModels", "needs_review"):
            self.assertIn(marker, self.mockup + self.contract)
        self.assertIn("capability set includes", self.contract)

    def test_review_and_execution_are_separate_and_redacted(self) -> None:
        for phrase in (
            "Redacted request review",
            "Review request",
            "Execute explicitly",
            "No task has executed",
            "no external request",
            "safe operation ID",
        ):
            self.assertIn(phrase, self.mockup + self.contract)
        self.assertNotRegex(
            self.mockup + self.contract,
            re.compile(r"(?i)(bearer\s+[a-z0-9._-]{12,}|sk-[a-z0-9]{12,})"),
        )

    def test_local_file_and_external_side_effect_boundaries_are_explicit(self) -> None:
        for phrase in (
            "Files remain local",
            "does not imply upload",
            "must not send a prompt",
            "External routing, publication, or durable writes require",
            "Credentials remain",
            "make no network request",
        ):
            self.assertIn(phrase, self.mockup + self.contract)
        self.assertIn("prefers-reduced-motion", self.mockup)


if __name__ == "__main__":
    unittest.main()
