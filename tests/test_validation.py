import tempfile
import unittest
from pathlib import Path

from orville_core.validation import RepairBudget, ValidationRunner
from orville_core.workspace import WorkspaceSession


class ValidationTests(unittest.TestCase):
    def test_validation_ladder_passes_and_reports_structured_checks(self):
        with tempfile.TemporaryDirectory() as source_dir:
            source = Path(source_dir)
            (source / "tests").mkdir()
            (source / "tests" / "test_ok.py").write_text("import unittest\nclass T(unittest.TestCase):\n    def test_ok(self): self.assertTrue(True)\n", encoding="utf-8")
            workspace = WorkspaceSession.create(source, workspace_parent=source.parent, workspace_id="validation")
            try:
                report = ValidationRunner(workspace).run()
                self.assertTrue(report.passed)
                self.assertEqual([check.status for check in report.checks], ["passed", "passed"])
            finally:
                workspace.cleanup()

    def test_repair_budget_stops_after_three_attempts(self):
        budget = RepairBudget()
        self.assertTrue(all(budget.can_attempt("tests") for _ in range(3)))
        for _ in range(3):
            budget.record("tests")
        self.assertFalse(budget.can_attempt("tests"))


if __name__ == "__main__":
    unittest.main()
