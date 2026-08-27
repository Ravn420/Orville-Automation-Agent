import tempfile
import unittest
from pathlib import Path

from orville_core.security import SecurityViolation
from orville_core.workspace import WorkspaceError, WorkspaceSession


class WorkspaceTests(unittest.TestCase):
    def test_checksum_guarded_write_and_rollback(self):
        with tempfile.TemporaryDirectory() as source_dir:
            source = Path(source_dir)
            target = source / "app.py"
            target.write_text("print('one')\n", encoding="utf-8")
            workspace = WorkspaceSession.create(source, workspace_parent=source.parent, workspace_id="test")
            try:
                original = workspace.checksum(workspace.root / "app.py")
                workspace.write_file("app.py", "print('two')\n", expected_checksum=original)
                with self.assertRaises(WorkspaceError):
                    workspace.write_file("app.py", "print('three')\n", expected_checksum=original)
                revision = workspace.create_revision(created_by="test")
                workspace.write_file("app.py", "print('four')\n")
                workspace.rollback(revision.revision_id)
                self.assertEqual(workspace.read_file("app.py"), "print('two')\n")
            finally:
                workspace.cleanup()

    def test_sensitive_paths_are_excluded_from_workspace_context(self):
        with tempfile.TemporaryDirectory() as source_dir:
            source = Path(source_dir)
            (source / "app.py").write_text("print('safe')\n", encoding="utf-8")
            (source / ".env").write_text("BLACKBOX_API_KEY=synthetic-secret\n", encoding="utf-8")
            (source / "private.pem").write_text("synthetic-key\n", encoding="utf-8")
            (source / "credentials.json").write_text("{\"token\": \"synthetic-secret\"}\n", encoding="utf-8")
            workspace = WorkspaceSession.create(source, workspace_parent=source.parent, workspace_id="context")
            try:
                self.assertEqual(workspace.list_files(), ["app.py"])
                self.assertEqual([row["path"] for row in workspace.index_files()], ["app.py"])
                self.assertFalse((workspace.root / ".env").exists())
                self.assertFalse((workspace.root / "private.pem").exists())
                self.assertFalse((workspace.root / "credentials.json").exists())
            finally:
                workspace.cleanup()

    def test_context_manifest_enforces_privacy_and_approval(self):
        with tempfile.TemporaryDirectory() as source_dir:
            source = Path(source_dir)
            (source / "app.py").write_text("print('safe')\n", encoding="utf-8")
            workspace = WorkspaceSession.create(source, workspace_parent=source.parent, workspace_id="manifest")
            try:
                local = workspace.context_manifest()
                self.assertEqual(local["execution_location"], "local")
                with self.assertRaises(SecurityViolation):
                    workspace.context_manifest(privacy_class="cloud_approved")
                approved = workspace.context_manifest(privacy_class="cloud_approved", approved_remote=True)
                self.assertEqual(approved["execution_location"], "remote")
                self.assertTrue(approved["approved_remote"])
            finally:
                workspace.cleanup()

    def test_workspace_rejects_escape_and_non_allowlisted_command(self):
        with tempfile.TemporaryDirectory() as source_dir:
            source = Path(source_dir)
            workspace = WorkspaceSession.create(source, workspace_parent=source.parent, workspace_id="test")
            try:
                with self.assertRaises(SecurityViolation):
                    workspace.read_file("../outside.txt")
                with self.assertRaises(SecurityViolation):
                    workspace.run(["bash", "-c", "echo unsafe"])
            finally:
                workspace.cleanup()

    def test_allowlisted_command_is_bounded(self):
        with tempfile.TemporaryDirectory() as source_dir:
            source = Path(source_dir)
            workspace = WorkspaceSession.create(source, workspace_parent=source.parent, workspace_id="test")
            try:
                result = workspace.run(["python", "-c", "print('ok')"], timeout_seconds=10)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout.strip(), "ok")
            finally:
                workspace.cleanup()


if __name__ == "__main__":
    unittest.main()

    def test_index_and_diff_do_not_mutate_workspace(self):
        with tempfile.TemporaryDirectory() as source_dir:
            source = Path(source_dir)
            target = source / "app.py"
            target.write_text("print('one')\n", encoding="utf-8")
            workspace = WorkspaceSession.create(source, workspace_parent=source.parent, workspace_id="index")
            try:
                rows = workspace.index_files()
                self.assertEqual([row["path"] for row in rows], ["app.py"])
                original_checksum = workspace.checksum(workspace.root / "app.py")
                preview = workspace.unified_diff("app.py", "print('two')\n", expected_checksum=original_checksum)
                self.assertTrue(preview["changed"])
                self.assertIn("-print('one')", str(preview["diff"]))
                self.assertEqual(workspace.read_file("app.py"), "print('one')\n")
            finally:
                workspace.cleanup()
