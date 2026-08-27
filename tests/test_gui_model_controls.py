from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "orville_core" / "api.py"
DOC = ROOT / "docs" / "GUI_MODEL_CONTROLS.md"


class GuiModelControlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.api_text = API.read_text(encoding="utf-8")
        cls.doc_text = DOC.read_text(encoding="utf-8")

    def test_api_exposes_model_import_and_compatibility_controls(self) -> None:
        for phrase in (
            '@app.post("/api/v1/models/local/import", dependencies=[Depends(authenticate)])',
            '@app.post("/api/v1/models/compatibility", dependencies=[Depends(authenticate)])',
            '@app.get("/api/v1/providers/health", dependencies=[Depends(authenticate)])',
            "ProviderRouter",
            "PrivacyRoutingPolicyStore",
            "LocalModelCatalog",
        ):
            self.assertIn(phrase, self.api_text)

    def test_documentation_covers_requested_gui_controls(self) -> None:
        for phrase in (
            "Model catalog",
            "Local-model import",
            "Local-model activation",
            "Provider health",
            "Routing controls",
            "privacy class",
            "local-only",
            "fallback",
            "license",
            "provenance",
        ):
            self.assertIn(phrase, self.doc_text)

    def test_safety_boundaries_are_explicit(self) -> None:
        for phrase in (
            "never render API keys",
            "must not silently fall back",
            "explicit approval",
            "raw provider responses",
            "external model metadata",
            "trusted instructions",
        ):
            self.assertIn(phrase, self.doc_text)
        self.assertNotRegex(self.doc_text, r"(?i)sk-[A-Za-z0-9]{12,}|api[_-]?key\s*=\s*[\"'][^\"']{8,}[\"']")

    def test_verification_commands_reference_existing_paths(self) -> None:
        self.assertTrue(API.is_file())
        self.assertTrue(DOC.is_file())
        self.assertTrue((ROOT / "tests" / "test_gui_model_controls.py").is_file())
        self.assertIn("tests.test_gui_model_controls", self.doc_text)


if __name__ == "__main__":
    unittest.main()
