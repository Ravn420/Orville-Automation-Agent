"""Focused validation for localization-ready text handling."""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path

from orville_core.localization import TextCatalog


class LocalizationTests(unittest.TestCase):
    """Verify text resources are separate from business logic and fail safely."""

    def test_catalog_loads_stable_keys_and_interpolates_parameters(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "en-US.json").write_text(
                json.dumps({"greeting": "Hello, {name}", "retry": "Retry"}), encoding="utf-8"
            )
            catalog = TextCatalog(root)
            self.assertEqual(catalog.text("greeting", {"name": "Orville"}), "Hello, Orville")
            self.assertEqual(catalog.text("retry"), "Retry")

    def test_locale_falls_back_to_default_and_missing_keys_are_safe(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "en-US.json").write_text(json.dumps({"known": "Known", "fallback": "Default"}), encoding="utf-8")
            (root / "fr-FR.json").write_text(json.dumps({"known": "Connu"}), encoding="utf-8")
            catalog = TextCatalog(root, locale="fr-FR")
            self.assertEqual(catalog.text("known"), "Connu")
            self.assertEqual(catalog.text("fallback"), "Default")
            self.assertEqual(catalog.text("missing.key"), "missing.key")

    def test_repository_resource_is_secret_safe_and_has_workflow_copy(self) -> None:
        root = Path(__file__).resolve().parents[1]
        resource = (root / "config" / "locales" / "en-US.json").read_text(encoding="utf-8")
        for key in ("workflow.describe", "workflow.prepare", "workflow.work", "workflow.review", "error.invalid_input", "error.operation_failed", "action.retry", "action.cancel"):
            self.assertIn(key, resource)
        self.assertNotRegex(resource, re.compile(r"(?i)(bearer\s+[a-z0-9._-]{12,}|sk-[a-z0-9]{12,})"))


if __name__ == "__main__":
    unittest.main()
