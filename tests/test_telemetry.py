import json
import tempfile
import unittest
from pathlib import Path

from orville_core.telemetry import TelemetryRegistry


class TelemetryTests(unittest.TestCase):
    def test_metrics_snapshot_and_export(self):
        with tempfile.TemporaryDirectory() as directory:
            registry = TelemetryRegistry()
            registry.record("task.run", success=True, duration_seconds=1.0)
            registry.record("task.run", success=False, duration_seconds=3.0)
            registry.record("task.cost", value=2.0)
            snapshot = registry.snapshot()
            self.assertEqual(snapshot["metrics"]["task.run"]["count"], 2)
            self.assertEqual(snapshot["metrics"]["task.run"]["failures"], 1)
            self.assertEqual(snapshot["metrics"]["task.run"]["failure_rate"], 0.5)
            output = registry.export(Path(directory) / "metrics.json")
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["metrics"]["task.cost"]["value_mean"], 2.0)


if __name__ == "__main__":
    unittest.main()
