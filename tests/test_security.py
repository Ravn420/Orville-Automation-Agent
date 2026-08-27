import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from orville_core import FilesystemPolicy, NetworkPolicy, SecretRedactor, SecurityViolation, ToolPolicy, require_dry_run
from orville_core.security import CredentialReference, CredentialStatus, ProviderPermissionPolicy


class SecurityTests(unittest.TestCase):
    def test_credential_reference_lifecycle_and_provider_permissions(self):
        now = datetime.now(UTC)
        reference = CredentialReference("ref-blackbox", "blackbox", "bearer", scopes=("chat", "chat"), expires_at=now + timedelta(minutes=5))
        self.assertEqual(reference.scopes, ("chat",))
        self.assertEqual(reference.lifecycle_status(now=now), CredentialStatus.ACTIVE)
        ProviderPermissionPolicy("blackbox", allowed_actions=frozenset({"chat"})).check(reference, "chat", required_scopes={"chat"})
        expired = CredentialReference("ref-expired", "blackbox", "bearer", expires_at=now - timedelta(seconds=1))
        with self.assertRaises(SecurityViolation):
            expired.require_active(now=now)
        revoked = CredentialReference("ref-revoked", "blackbox", "bearer", status=CredentialStatus.REVOKED)
        with self.assertRaises(SecurityViolation):
            revoked.require_active(now=now)
        with self.assertRaises(SecurityViolation):
            ProviderPermissionPolicy("blackbox", allowed_actions=frozenset({"health"})).check(reference, "chat")

    def test_security_redactor_masks_embedded_tokens_and_account_identifiers(self):
        value = SecretRedactor.redact({"Authorization": "Bearer sk-live-secret123", "error": "account account-secret123"})
        self.assertNotIn("sk-live-secret123", str(value))
        self.assertNotIn("account-secret123", str(value))

    def test_tool_policy_fails_closed_until_approved(self):
        policy = ToolPolicy(allowed_tools={"read_file"})
        with self.assertRaises(SecurityViolation):
            policy.check("read_file")
        policy.authorize("read_file")
        policy.check("read_file")
        with self.assertRaises(SecurityViolation):
            policy.check("shell")

    def test_dry_run_blocks_side_effects(self):
        with self.assertRaises(SecurityViolation):
            require_dry_run(ToolPolicy(dry_run=True))

    def test_filesystem_policy_rejects_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            policy = FilesystemPolicy((Path(directory),), allow_write=False)
            self.assertTrue(policy.resolve(Path(directory, "file.txt")).is_absolute())
            with self.assertRaises(SecurityViolation):
                policy.resolve(Path(directory).parent / "outside.txt")
            with self.assertRaises(SecurityViolation):
                policy.resolve(Path(directory, "file.txt"), write=True)

    def test_network_policy_allowlist_and_private_default(self):
        policy = NetworkPolicy(frozenset({"api.example.com"}))
        policy.check_host("api.example.com")
        with self.assertRaises(SecurityViolation):
            policy.check_host("other.example.com")
        with self.assertRaises(SecurityViolation):
            NetworkPolicy(frozenset({"localhost"})).check_host("localhost")

    def test_secret_redactor_masks_nested_values_and_bearer_tokens(self):
        value = {"api_key": "secret", "nested": {"authorization": "Bearer abc123", "text": "safe"}}
        redacted = SecretRedactor.redact(value)
        self.assertEqual(redacted["api_key"], "[REDACTED]")
        self.assertEqual(redacted["nested"]["authorization"], "[REDACTED]")
        self.assertEqual(redacted["nested"]["text"], "safe")


if __name__ == "__main__":
    unittest.main()
