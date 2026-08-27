from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from orville_core.automation import AutomationDispatcher, RunStatus, TriggerType, WorkflowExecutor, WorkflowStep, WorkflowStore
from orville_core.scheduler import ScheduleStore
from orville_core.security import SecretRedactor


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "regressions"


class RegressionFixtureTests(unittest.TestCase):
    """Exercise retained fixtures for previously corrected failure modes."""

    @staticmethod
    def load(name: str) -> dict:
        return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))

    def test_manifest_references_existing_fixtures(self) -> None:
        manifest = self.load("manifest.json")
        self.assertEqual(manifest["schema_version"], 1)
        self.assertGreaterEqual(len(manifest["fixtures"]), 3)
        for entry in manifest["fixtures"]:
            self.assertTrue((FIXTURE_ROOT / entry["path"]).is_file(), entry["id"])
            self.assertTrue(entry["assertion"])

    def test_scheduled_retry_fixture_preserves_one_occurrence(self) -> None:
        fixture = self.load("scheduled-retry-same-slot.json")
        calls: list[int] = []

        def fail_once(_payload):
            calls.append(1)
            if len(calls) == 1:
                raise RuntimeError("fixture failure")
            return {"ok": True}

        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "scheduler.db"
            workflows = WorkflowStore(database)
            schedules = ScheduleStore(database)
            workflow_id = workflows.create_workflow("fixture schedule")
            version = workflows.add_version(workflow_id, TriggerType.SCHEDULED, (WorkflowStep("step", "fixture"),))
            workflows.set_enabled(workflow_id, version.version_id, True)
            schedule = schedules.create(fixture["schedule_id"], workflow_id, 60)
            schedules.set_enabled(schedule.schedule_id, True)
            dispatcher = AutomationDispatcher(schedules, workflows, WorkflowExecutor({"fixture": fail_once}))
            with self.assertRaisesRegex(RuntimeError, "fixture failure"):
                dispatcher.dispatch_schedule(schedule.schedule_id)
            completed = dispatcher.dispatch_schedule(schedule.schedule_id)
            self.assertEqual(completed.status, RunStatus.COMPLETED)
            self.assertEqual(len(calls), 2)
            self.assertEqual(len(workflows.list_runs(workflow_id)), fixture["expected_run_count"])
            self.assertEqual(len(schedules.history(schedule.schedule_id)), fixture["expected_execution_record_count"])

    def test_dry_run_fixture_skips_mutating_handler(self) -> None:
        fixture = self.load("workflow-dry-run-mutation.json")
        calls: list[str] = []
        executor = WorkflowExecutor({
            "local": lambda _payload: calls.append("local") or {"ready": True},
            "publish": lambda _payload: calls.append("publish") or {"published": True},
        })
        steps = tuple(WorkflowStep(item["step_id"], item["kind"], item["config"], requires_approval=item["requires_approval"]) for item in fixture["steps"])
        result = executor.execute(steps, {}, dry_run=True)
        self.assertEqual(calls, fixture["expected_handler_calls"])
        self.assertEqual(result["_dry_run"], fixture["expected_preview_marker"])
        self.assertEqual(result["dry_run_actions"][0]["step_id"], fixture["expected_skipped_step"])
        self.assertNotIn("published", result)

    def test_secret_redaction_fixture_contains_no_forbidden_values(self) -> None:
        fixture = self.load("nested-secret-redaction.json")
        redacted = SecretRedactor.redact(fixture["input"])
        rendered = str(redacted)
        for value in fixture["forbidden_values"]:
            self.assertNotIn(value, rendered)
        self.assertEqual(redacted["nested"]["api_key"], fixture["expected_nested_api_key"])


if __name__ == "__main__":
    unittest.main()
