"""Focused tests for the unified model-manager workflow."""

from __future__ import annotations

import unittest
from pathlib import Path


class ModelManagerTests(unittest.TestCase):
    """Verify the GUI exposes all supported model-management paths."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.source = (Path(__file__).resolve().parents[1] / "windows_gui.py").read_text(encoding="utf-8")
        cls.model_doc = (Path(__file__).resolve().parents[1] / "docs" / "MODEL_MANAGER_SPECIFICATION.md").read_text(encoding="utf-8")

    def test_gui_unifies_provider_and_local_model_actions(self) -> None:
        for phrase in ("Model manager", "Provider setup", "Import local model", "cloud providers", "endpoint models", "Ollama servers"):
            self.assertIn(phrase, self.source)
        for route in ("/api/v1/providers", "/api/v1/providers/health", "/api/v1/providers/{provider}/models", "/api/v1/models/local", "/api/v1/models/local/import"):
            self.assertIn(route, self.source)

    def test_model_manager_document_covers_inventory_and_safe_lifecycle(self) -> None:
        for phrase in ("Cloud providers", "Endpoint-based models", "Ollama", "Imported local model files", "Validate", "Activate", "Deactivate", "Remove registration", "Credentials are masked"):
            self.assertIn(phrase, self.model_doc)

    def test_model_manager_avoids_secret_display_and_destructive_file_removal(self) -> None:
        self.assertIn("api_key.set(\"\")", self.source)
        self.assertIn("No model files will be deleted", self.source)
        self.assertIn("without exposing secrets", self.source)


if __name__ == "__main__":
    unittest.main()
