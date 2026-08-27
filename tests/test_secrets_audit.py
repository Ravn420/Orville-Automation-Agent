import os
import tempfile
import unittest
from pathlib import Path

from orville_core.secrets_audit import AuditStore, SecretReferenceStore, SecretScanner


class SecretAuditTests(unittest.TestCase):
    def test_secret_references_never_store_values_and_resolve_from_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            store = SecretReferenceStore(Path(directory) / "secrets.db")
            os.environ["ORVILLE_TEST_SECRET"] = "super-secret"
            try:
                reference = store.register("ORVILLE_TEST_SECRET", "test", "local")
                self.assertEqual(store.resolve_for_process(reference.reference_id), "super-secret")
                self.assertNotIn("super-secret", str(store.list_references()))
            finally:
                os.environ.pop("ORVILLE_TEST_SECRET", None)

    def test_scanner_and_audit_store_redact_sensitive_data(self):
        matches = SecretScanner.find({"api_key": "secret-value"})
        self.assertTrue(matches)
        self.assertNotIn("secret-value", str(SecretScanner.redact({"api_key": "secret-value"})))
        payload = {
            "headers": {"Authorization": "Bearer sk-live-secret123"},
            "account_id": "account-secret123",
            "provider_error": "Blackbox returned sk-live-secret123 for account account-secret123",
        }
        redacted = SecretScanner.redact(payload)
        self.assertNotIn("sk-live-secret123", str(redacted))
        self.assertNotIn("account-secret123", str(redacted))
        self.assertEqual(redacted["headers"]["Authorization"], "[REDACTED]")
        self.assertEqual(redacted["account_id"], "[REDACTED]")
        with tempfile.TemporaryDirectory() as directory:
            record = AuditStore(Path(directory) / "audit.db").append("user-1", "plan.approve", "plan-1", "success", metadata={"token": "hidden"})
            self.assertEqual(record.outcome, "success")
            self.assertNotIn("hidden", str(record.metadata))


if __name__ == "__main__":
    unittest.main()
