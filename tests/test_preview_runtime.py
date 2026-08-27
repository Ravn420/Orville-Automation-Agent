import tempfile
import unittest
from pathlib import Path
from urllib.request import urlopen

from orville_core.preview_runtime import PreviewRuntime


class PreviewRuntimeTests(unittest.TestCase):
    def test_start_status_http_and_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.html").write_text("<h1>Orville</h1>", encoding="utf-8")
            runtime = PreviewRuntime()
            try:
                record = runtime.start("preview-1", "rev-1", root)
                self.assertEqual(record.status, "running")
                with urlopen(f"http://{record.host}:{record.port}/index.html", timeout=5) as response:
                    self.assertEqual(response.status, 200)
                    self.assertIn("Orville", response.read().decode())
                stopped = runtime.stop("preview-1")
                self.assertEqual(stopped.status, "stopped")
            finally:
                runtime.stop_all()


if __name__ == "__main__":
    unittest.main()
