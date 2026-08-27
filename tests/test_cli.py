import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path

from orville_core.cli import main


class CliTests(unittest.TestCase):
    def test_config_and_readiness_commands(self):
        previous = os.environ.get("ORVILLE_API_TOKEN")
        os.environ["ORVILLE_API_TOKEN"] = "cli-test-token"
        try:
            with tempfile.TemporaryDirectory() as directory:
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(main(["--database", str(Path(directory) / "orville.db"), "config"]), 0)
                    self.assertEqual(main(["--database", str(Path(directory) / "orville.db"), "readiness"]), 0)
                self.assertIn("api_token_configured", output.getvalue())
                self.assertNotIn("cli-test-token", output.getvalue())
        finally:
            if previous is None:
                os.environ.pop("ORVILLE_API_TOKEN", None)
            else:
                os.environ["ORVILLE_API_TOKEN"] = previous

    def test_health_command(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(main(["--database", str(Path(directory) / "orville.db"), "health"]), 0)


if __name__ == "__main__":
    unittest.main()
