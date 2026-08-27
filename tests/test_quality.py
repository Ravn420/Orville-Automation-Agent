import tempfile
import unittest
from pathlib import Path

from orville_core.evaluation import EvaluationCheck, evaluate_output
from orville_core.observability import JsonlTraceRecorder
from orville_core.security import SecretRedactor


class QualityTests(unittest.TestCase):
    def test_trace_recorder_persists_and_redacts(self):
        with tempfile.TemporaryDirectory() as directory:
            recorder = JsonlTraceRecorder(Path(directory) / "trace.jsonl", SecretRedactor())
            recorder.record("trace-1", "model_call", {"api_key": "super-secret", "provider": "gemini"})
            records = recorder.read()
            self.assertEqual(len(records), 1)
            self.assertNotIn("super-secret", str(records[0].attributes))
            self.assertIn("gemini", str(records[0].attributes))

    def test_acceptance_criteria_are_evaluated(self):
        result = evaluate_output("generated source code with tests", ["source code", "tests"])
        self.assertTrue(result.passed)
        self.assertEqual(len(result.checks), 3)

    def test_failed_criteria_are_reported(self):
        result = evaluate_output("generated source code", ["deployment guide"])
        self.assertFalse(result.passed)
        self.assertFalse(result.checks[-1].passed)

    def test_custom_check_is_supported(self):
        result = evaluate_output({"files": 3}, checks=[lambda output: EvaluationCheck("files", output["files"] > 0, "files present")])
        self.assertTrue(result.passed)


if __name__ == "__main__":
    unittest.main()
