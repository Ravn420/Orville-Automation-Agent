import tempfile
import unittest
from pathlib import Path

from case_app.exporter import export_text


class ExporterTests(unittest.TestCase):
    def test_writes_nested_relative_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            destination = export_text(root, "reports/result.txt", "ok")
            self.assertEqual(destination.read_text(encoding="utf-8"), "ok")
            self.assertTrue(destination.is_relative_to(root))

    def test_rejects_traversal_outside_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(ValueError):
                export_text(root, "../outside.txt", "must not escape")


if __name__ == "__main__":
    unittest.main()
