import tempfile
import unittest
from pathlib import Path

from orville_core.identity import MembershipDirectory, ProjectRole, SQLiteMembershipDirectory


class IdentityTests(unittest.TestCase):
    def test_durable_membership_persists_and_revokes(self):
        with tempfile.TemporaryDirectory() as directory:
            directory_store = SQLiteMembershipDirectory(Path(directory) / "identity.db")
            directory_store.add("project-1", "owner", ProjectRole.OWNER)
            directory_store.add("project-1", "viewer", ProjectRole.VIEWER, invited_by="owner")
            self.assertEqual(directory_store.authorize("project-1", "viewer", "read").role, ProjectRole.VIEWER)
            with self.assertRaises(PermissionError):
                directory_store.authorize("project-1", "viewer", "execute")
            directory_store.revoke("project-1", "viewer")
            with self.assertRaises(PermissionError):
                directory_store.get("project-1", "viewer")

    def test_role_authorization_is_least_privilege(self):
        directory = MembershipDirectory()
        directory.add("project-1", "dev", ProjectRole.DEVELOPER)
        directory.add("project-1", "reviewer", ProjectRole.REVIEWER)
        directory.authorize("project-1", "dev", "execute")
        directory.authorize("project-1", "reviewer", "approve")
        with self.assertRaises(PermissionError):
            directory.authorize("project-1", "dev", "publish")
        with self.assertRaises(PermissionError):
            directory.authorize("project-1", "unknown", "read")
        self.assertEqual(len(directory.list_members("project-1")), 2)


if __name__ == "__main__":
    unittest.main()
