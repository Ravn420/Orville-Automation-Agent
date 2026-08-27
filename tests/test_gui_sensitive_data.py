"""Focused checks for sensitive-data exposure boundaries in the GUI."""

from __future__ import annotations

import unittest
from pathlib import Path

from orville_core.gui_state import safe_display_value


class GuiSensitiveDataTests(unittest.TestCase):
    """Verify rendered GUI values are redacted and user prompts are not echoed."""

    @classmethod
    def setUpClass(cls) -> None:
        root = Path(__file__).resolve().parents[1]
        cls.source = (root / "windows_gui.py").read_text(encoding="utf-8")
        cls.document = (root / "docs" / "GUI_SENSITIVE_DATA.md").read_text(encoding="utf-8")

    def test_sensitive_keys_and_patterns_are_redacted(self) -> None:
        value = {
            "api_key": "sk-test-secret-value",
            "note": "Observed sk-test-secret-value in a diagnostic string",
            "prompt": "private objective text",
            "path": r"C:\Users\Operator\private\artifact.txt",
            "details": r"Saved at C:\Users\Operator\private\artifact.txt",
            "message": "Bearer abc.def.ghi",
        }
        rendered = str(safe_display_value(value))
        for secret in ("sk-test-secret-value", "private objective text", "C:\\Users\\Operator\\private\\artifact.txt", "abc.def.ghi"):
            self.assertNotIn(secret, rendered)
        for marker in ("[redacted for interface safety]", "[redacted-secret]", "[redacted-local-path]"):
            self.assertIn(marker, rendered)

    def test_gui_paths_use_safe_projection_and_do_not_echo_objective(self) -> None:
        for phrase in ("safe_display_value(result)", "safe_display_value(value)", "The local operation could not be completed.", "Configured runtime endpoint (hidden)"):
            self.assertIn(phrase, self.source)
        self.assertNotIn("self._write(text)\n        self._request(\"/api/v1/objectives\"", self.source)

    def test_contract_covers_required_exposure_categories_and_limits(self) -> None:
        for phrase in ("logs", "prompts", "API keys", "local paths", "raw exceptions", "provider responses", "credentials", "redaction", "Acceptance checks"):
            self.assertIn(phrase.lower(), self.document.lower())


if __name__ == "__main__":
    unittest.main()
