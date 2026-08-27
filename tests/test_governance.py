import tempfile
import unittest
from pathlib import Path

from orville_core.governance import GovernanceStore


class GovernanceTests(unittest.TestCase):
    def test_findings_metrics_evaluations_and_release_gates(self):
        with tempfile.TemporaryDirectory() as directory:
            store = GovernanceStore(Path(directory) / "governance.db")
            finding = store.record_finding("project-1", "secret-scan", "high", "Synthetic secret detected", "config.py")
            self.assertEqual(store.list_findings("project-1")[0].finding_id, finding.finding_id)
            metric = store.record_metric("project-1", "task.duration", 1.5, {"mode": "testing"})
            self.assertEqual(metric.value, 1.5)
            evaluation = store.run_evaluation("project-1", "acceptance", [{"name": "a", "passed": True}, {"name": "b", "passed": False}])
            self.assertFalse(evaluation.passed)
            self.assertEqual(evaluation.score, 0.5)
            with self.assertRaises(PermissionError):
                store.record_release("project-1", "rev-1", "production", "user-1", False, True, "rev-0")
            release = store.record_release("project-1", "rev-1", "staging", "user-1", True, True, "rev-0")
            self.assertEqual(release.rollback_target, "rev-0")


if __name__ == "__main__":
    unittest.main()
