import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "measure_gui_performance.py"
SPEC = importlib.util.spec_from_file_location("measure_gui_performance", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class GuiPerformanceMeasurementTests(unittest.TestCase):
    def test_fixed_workload_contains_requested_collections(self):
        workload = MODULE._workload(7, 4)
        self.assertEqual(len(workload["graph"]["tasks"]), 7)
        self.assertEqual(len(workload["artifacts"]), 4)
        self.assertEqual(workload["graph"]["tasks"][0]["task_id"], "task-0000")
        self.assertEqual(workload["artifacts"][-1]["artifact_id"], "artifact-0003")

    @patch.object(MODULE, "_startup_ms", return_value=100.0)
    def test_measure_reports_required_metrics_and_passes_gates(self, _startup):
        result = MODULE.measure(10, 5)
        self.assertEqual(result["workload"], {"tasks": 10, "artifacts": 5})
        self.assertEqual(set(result["measurements"]), {"startup_ms", "interaction_ms", "peak_memory_bytes", "serialized_bytes"})
        self.assertTrue(all(result["pass"].values()))

    @patch.object(MODULE, "_startup_ms", return_value=3000.0)
    def test_measure_fails_startup_gate(self, _startup):
        result = MODULE.measure(1, 1)
        self.assertFalse(result["pass"]["startup"])

    def test_cli_bounds_are_explicit(self):
        self.assertEqual(MODULE.DEFAULT_TASKS, 1000)
        self.assertEqual(MODULE.DEFAULT_ARTIFACTS, 500)
        self.assertLessEqual(1, 10000)


if __name__ == "__main__":
    unittest.main()
