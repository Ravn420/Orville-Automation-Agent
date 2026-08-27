import tempfile
import unittest
from pathlib import Path

from orville_core.handoff import BundleExporter, RepositoryHandoff
from orville_core.workspace import WorkspaceSession


class HandoffTests(unittest.TestCase):
    def test_conflicting_local_and_remote_changes_are_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            source.mkdir()
            (source / "app.py").write_text("base\n", encoding="utf-8")
            workspace = WorkspaceSession.create(source, workspace_parent=Path(directory), workspace_id="handoff")
            try:
                (workspace.root / "app.py").write_text("local\n", encoding="utf-8")
                base_checksum = WorkspaceSession.checksum(source / "app.py")
                local_checksum = WorkspaceSession.checksum(workspace.root / "app.py")
                plan = RepositoryHandoff(workspace).prepare("feature/test", base_checksums={"app.py": base_checksum}, remote_checksums={"app.py": "remote-checksum"})
                self.assertEqual(plan.status, "blocked_by_conflict")
                self.assertEqual(plan.conflicts[0].path, "app.py")
            finally:
                workspace.cleanup()

    def test_export_bundle_contains_archive_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            source.mkdir()
            (source / "README.md").write_text("setup", encoding="utf-8")
            bundle = BundleExporter().export(source, Path(directory) / "bundle.zip")
            self.assertTrue(Path(bundle.archive_path).is_file())
            self.assertIn("README.md", bundle.included_files)


if __name__ == "__main__":
    unittest.main()
