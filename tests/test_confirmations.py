from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

from orville_core.confirmations import (
    ConfirmationGate,
    ConfirmationRequired,
    ConfirmationRequest,
    SENSITIVE_OPERATION_KINDS,
)


class ConfirmationTests(unittest.TestCase):
    def test_sensitive_operation_catalog_covers_required_actions(self) -> None:
        self.assertTrue({"payment", "publish", "delete", "account_change"}.issubset(SENSITIVE_OPERATION_KINDS))

    def test_missing_confirmation_fails_closed(self) -> None:
        request = ConfirmationRequest.create("publish", "production-site", "release-42", "operator")
        with self.assertRaises(ConfirmationRequired):
            ConfirmationGate().require(request, None)

    def test_matching_confirmation_is_single_use(self) -> None:
        now = datetime(2026, 8, 27, tzinfo=timezone.utc)
        request = ConfirmationRequest.create("delete", "workspace-7", "named-file.txt", "operator", now=now)
        gate = ConfirmationGate()
        receipt = gate.confirm(request, confirmer="operator", now=now + timedelta(seconds=1))
        gate.require(request, receipt, now=now + timedelta(seconds=2))
        with self.assertRaisesRegex(ConfirmationRequired, "already been used"):
            gate.require(request, receipt, now=now + timedelta(seconds=3))

    def test_mismatched_scope_and_expired_receipts_are_rejected(self) -> None:
        now = datetime(2026, 8, 27, tzinfo=timezone.utc)
        request = ConfirmationRequest.create("payment", "merchant-1", "10.00 USD", "operator", ttl_seconds=10, now=now)
        gate = ConfirmationGate()
        receipt = gate.confirm(request, confirmer="operator", now=now)
        other = ConfirmationRequest.create("payment", "merchant-1", "100.00 USD", "operator", now=now)
        with self.assertRaises(ConfirmationRequired):
            gate.require(other, receipt, now=now)
        expired_request = ConfirmationRequest.create("account_change", "account-1", "email", "operator", ttl_seconds=1, now=now)
        expired_receipt = gate.confirm(expired_request, confirmer="operator", now=now)
        with self.assertRaisesRegex(ConfirmationRequired, "expired"):
            gate.require(expired_request, expired_receipt, now=now + timedelta(seconds=2))


if __name__ == "__main__":
    unittest.main()
