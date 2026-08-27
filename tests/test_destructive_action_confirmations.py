"""Focused validation for destructive-action confirmation requirements."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs" / "DESTRUCTIVE_ACTION_CONFIRMATIONS.md"


class DestructiveActionConfirmationTests(unittest.TestCase):
    """Verify destructive actions are explicit, bounded, and recoverable."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = CONTRACT_PATH.read_text(encoding="utf-8")

    def test_action_classes_and_consequence_previews_are_present(self) -> None:
        for phrase in (
            "Delete artifact",
            "Overwrite or replace",
            "Revoke credential",
            "Publish, deploy, or promote",
            "Enable schedule or external notification",
            "Reset or remove durable configuration",
            "exact target and scope",
            "reversible alternative",
            "ambiguous labels",
        ):
            self.assertIn(phrase, self.contract)

    def test_confirmation_and_failure_states_are_fail_closed(self) -> None:
        for phrase in (
            "awaiting_confirmation",
            "awaiting_approval",
            "single-use",
            "stale preview",
            "Rejected, expired, cancelled, or failed",
            "must not claim success",
            "silently retry",
            "operation identifier",
            "reconcile status",
        ):
            self.assertIn(phrase, self.contract)

    def test_accessibility_audit_and_secret_boundaries_are_present(self) -> None:
        for phrase in (
            "modal focus trap",
            "visible focus indicator",
            "Escape-to-cancel",
            "assistive technology",
            "action fingerprint",
            "Backend authorization",
            "idempotency",
            "audit recording",
            "credentials",
            "bearer tokens",
            "secret-bearing URLs",
        ):
            self.assertIn(phrase, self.contract)
        self.assertNotRegex(
            self.contract,
            re.compile(r"(?i)(bearer\s+[a-z0-9._-]{12,}|sk-[a-z0-9]{12,})"),
        )


if __name__ == "__main__":
    unittest.main()
