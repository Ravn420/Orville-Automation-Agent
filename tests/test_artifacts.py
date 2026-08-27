import tempfile
import unittest
from pathlib import Path

from orville_core.artifacts import ArtifactStore
from orville_core.security import SecurityViolation


class ArtifactTests(unittest.TestCase):
    def test_register_and_list_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "artifacts"
            root.mkdir()
            path = root / "report.md"
            path.write_text("verified", encoding="utf-8")
            store = ArtifactStore(root)
            record = store.register(path)
            self.assertEqual(record.name, "report.md")
            self.assertEqual(record.media_type, "text/markdown")
            self.assertEqual(store.list()[0].sha256, record.sha256)

    def test_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "artifacts"
            store = ArtifactStore(root)
            with self.assertRaises(SecurityViolation):
                store.open("../secret.txt")


if __name__ == "__main__":
    unittest.main()
