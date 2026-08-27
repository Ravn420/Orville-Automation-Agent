from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from orville_core.enterprise_identity import EnterpriseAuthorizationError, IdentityClaims, SQLiteEnterpriseAuthorizationStore


class EnterpriseIdentityTests(unittest.TestCase):
    def claims(self, scopes: set[str], tenant: str = "tenant-a") -> IdentityClaims:
        now = time.time()
        return IdentityClaims("actor-1", tenant, "subject-1", frozenset(scopes), now - 1, now + 3600, "session-1")

    def test_tenant_scoped_least_privilege_and_audit(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = SQLiteEnterpriseAuthorizationStore(Path(directory) / "identity.db")
            store.grant("tenant-a", "actor-1", {"orville:read", "orville:deploy"})
            decision = store.authorize(self.claims({"orville:read"}), "read")
            self.assertTrue(decision.allowed)
            with self.assertRaises(EnterpriseAuthorizationError):
                store.authorize(self.claims({"orville:read"}), "deploy_canary")
            with self.assertRaises(EnterpriseAuthorizationError):
                store.authorize(self.claims({"orville:read"}, "tenant-b"), "read")
            self.assertEqual(len(store.audit_events("tenant-a")), 2)

    def test_sensitive_actions_require_matching_unexpired_approval_and_revocation(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
            store = SQLiteEnterpriseAuthorizationStore(Path(directory) / "identity.db")
            store.grant("tenant-a", "actor-1", {"orville:deploy"})
            with self.assertRaises(EnterpriseAuthorizationError):
                store.authorize(self.claims({"orville:deploy"}), "deploy_canary")
            store.approve("approval-1", "tenant-a", "actor-1", "deploy_canary", time.time() + 60)
            self.assertTrue(store.authorize(self.claims({"orville:deploy"}), "deploy_canary", approval_reference="approval-1").allowed)
            store.revoke("tenant-a", "actor-1")
            with self.assertRaises(EnterpriseAuthorizationError):
                store.authorize(self.claims({"orville:deploy"}), "deploy_canary", approval_reference="approval-1")


if __name__ == "__main__":
    unittest.main()
