from __future__ import annotations

import unittest
from pathlib import Path

from orville_core.security import SecretRedactor


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "SECRET_HANDLING_RULES.md"


class SecretHandlingRulesTests(unittest.TestCase):
    """Verify the documented secret-handling contract and redaction examples."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.document = DOC.read_text(encoding="utf-8")

    def test_all_required_retention_surfaces_are_defined(self) -> None:
        for phrase in (
            "Environment variables",
            "Configuration files",
            "Logs",
            "Artifacts and reports",
            "Screenshots and recordings",
            "Approved secret lifecycle",
            "Repository and path rules",
            "Display and interface rules",
        ):
            self.assertIn(phrase, self.document)

    def test_prohibited_storage_and_recovery_rules_are_explicit(self) -> None:
        for phrase in (
            "must never cross into committed source",
            "The value is never placed",
            "Rotate or revoke",
            "server-side adapter",
            "SecretRedactor",
            "approved protected secret boundaries",
            "synthetic credentials",
            "approved-root containment",
            "visual review and secret scan",
        ):
            self.assertIn(phrase, self.document)
        self.assertNotIn("sk-live-", self.document)
        self.assertNotIn("Bearer eyJ", self.document)

    def test_redactor_masks_nested_values_bearer_query_and_token_patterns(self) -> None:
        value = {
            "Authorization": "Bearer synthetic-bearer-value",
            "nested": {"api_key": "synthetic-api-key-value"},
            "url": "https://example.test/callback?access_token=synthetic-query-token",
            "message": "token-shaped tok_synthetic-secret-value",
        }
        redacted = SecretRedactor.redact(value)
        rendered = str(redacted)
        for secret in (
            "synthetic-bearer-value",
            "synthetic-api-key-value",
            "synthetic-query-token",
            "tok_synthetic-secret-value",
        ):
            self.assertNotIn(secret, rendered)
        self.assertEqual(redacted["nested"]["api_key"], "[REDACTED]")


if __name__ == "__main__":
    unittest.main()
