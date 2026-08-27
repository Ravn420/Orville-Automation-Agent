from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from orville_core.protected_secrets import ProtectedSecretError, ProtectedSecretStore


class ProtectedSecretTests(unittest.TestCase):
    def test_runtime_resolution_rotation_and_secret_free_export(self):
        values = {"ORVILLE_TEST_KEY": "synthetic-secret"}
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = ProtectedSecretStore(Path(directory) / "secrets.db", values.get)
            reference = store.register("ORVILLE_TEST_KEY", "test-provider", "staging")
            self.assertEqual(store.resolve(reference.reference_id), "synthetic-secret")
            rotated = store.rotate(reference.reference_id, "ORVILLE_TEST_KEY_V2")
            self.assertEqual(rotated.version, 2)
            exported = store.redacted_export()
            self.assertNotIn("synthetic-secret", str(exported))
            self.assertNotIn("token", str(exported).lower())

    def test_missing_or_revoked_secret_fails_closed_and_scrub_works(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = ProtectedSecretStore(Path(directory) / "secrets.db", lambda _name: None)
            reference = store.register("ORVILLE_MISSING_KEY", "test-provider", "staging")
            with self.assertRaises(ProtectedSecretError):
                store.resolve(reference.reference_id)
            store.revoke(reference.reference_id)
            with self.assertRaises(ProtectedSecretError):
                store.resolve(reference.reference_id)
            runtime = {"credential": "secret", "other": "value"}
            ProtectedSecretStore.scrub(runtime, {"credential": "reference-id"})
            self.assertEqual(runtime["credential"], "[SCRUBBED]")

    def test_secret_names_are_restricted_to_environment_identifiers(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = ProtectedSecretStore(Path(directory) / "secrets.db")
            with self.assertRaises(ProtectedSecretError):
                store.register("bad-name", "provider", "staging")


if __name__ == "__main__":
    unittest.main()
