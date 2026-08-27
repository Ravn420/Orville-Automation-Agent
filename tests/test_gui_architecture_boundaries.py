"""Focused tests for GUI architecture and layer boundaries."""

from __future__ import annotations

import unittest
from pathlib import Path


class GuiArchitectureBoundaryTests(unittest.TestCase):
    """Verify the architecture decision remains explicit and standalone-safe."""

    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).resolve().parents[1]
        cls.document = (root / "docs" / "GUI_ARCHITECTURE_BOUNDARIES.md").read_text(encoding="utf-8")

    def test_document_names_all_layers_and_decision(self) -> None:
        for phrase in ("layered native-client architecture", "Presentation", "Client adapter", "API boundary", "Orchestration", "Model services", "Storage", "External integrations"):
            self.assertIn(phrase, self.document)

    def test_document_records_ownership_and_prohibited_coupling(self) -> None:
        for phrase in ("Must not own", "Task-graph mutation rules", "secret storage", "Durable truth", "Direct GUI access", "prohibited coupling"):
            self.assertIn(phrase, self.document)

    def test_document_preserves_standalone_security_and_lifecycle_boundaries(self) -> None:
        for phrase in ("standalone local operation", "same versioned API", "Credentials remain", "approval gates", "Loading, empty, offline, blocked, failed, partial, and long-running", "Acceptance checks"):
            self.assertIn(phrase, self.document)


if __name__ == "__main__":
    unittest.main()
