from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


class StandaloneExamplesTests(unittest.TestCase):
    def run_example(self, relative_path: str) -> str:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT)
        completed = subprocess.run(
            [sys.executable, str(ROOT / relative_path)],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=True,
        )
        return completed.stdout

    def test_basic_workflow_runs_without_external_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            environment = os.environ.copy()
            environment["PYTHONPATH"] = str(ROOT)
            completed = subprocess.run(
                [sys.executable, str(EXAMPLES / "basic_run.py")],
                cwd=directory,
                env=environment,
                capture_output=True,
                text=True,
                check=True,
            )
        self.assertIn("status=completed", completed.stdout)
        self.assertIn("basic-demo-run", completed.stdout)

    def test_local_report_example_emits_json_without_credentials(self) -> None:
        output = self.run_example("examples/local_operational_report.py")
        report = json.loads(output)
        self.assertEqual(report["target"], "local")
        self.assertEqual(report["execution_count"], 1)
        self.assertEqual(report["failure_count"], 0)
        self.assertTrue(report["data_quality"]["bounded"])

    def test_example_sources_do_not_reference_manus_or_secret_inputs(self) -> None:
        for path in (EXAMPLES / "basic_run.py", EXAMPLES / "local_operational_report.py", EXAMPLES / "README.md"):
            text = path.read_text(encoding="utf-8").lower()
            self.assertNotIn("manus_mcp", text)
            self.assertNotIn("api_key=", text)
            self.assertNotIn("bearer ", text)


if __name__ == "__main__":
    unittest.main()
