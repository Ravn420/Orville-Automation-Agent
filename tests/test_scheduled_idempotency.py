from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from orville_core.automation import AutomationDispatcher, RunStatus, TriggerType, WorkflowExecutor, WorkflowStep, WorkflowStore
from orville_core.scheduler import ScheduleStore


class ScheduledIdempotencyTests(unittest.TestCase):
    def _setup(self, handler):
        directory = tempfile.TemporaryDirectory()
        database = Path(directory.name) / "scheduled.db"
        workflows = WorkflowStore(database)
        schedules = ScheduleStore(database)
        workflow_id = workflows.create_workflow("retry-safe schedule")
        version = workflows.add_version(workflow_id, TriggerType.SCHEDULED, (WorkflowStep("step", "handler"),))
        workflows.set_enabled(workflow_id, version.version_id, True)
        schedule = schedules.create("schedule-1", workflow_id, 60)
        schedules.set_enabled(schedule.schedule_id, True)
        dispatcher = AutomationDispatcher(schedules, workflows, WorkflowExecutor({"handler": handler}))
        return directory, workflows, schedules, dispatcher, schedule

    def test_failed_occurrence_retries_with_same_idempotency_key(self) -> None:
        calls: list[int] = []

        def fail_once(_payload):
            calls.append(1)
            if len(calls) == 1:
                raise RuntimeError("synthetic failure")
            return {"ok": True}

        directory, workflows, schedules, dispatcher, schedule = self._setup(fail_once)
        try:
            with self.assertRaisesRegex(RuntimeError, "synthetic failure"):
                dispatcher.dispatch_schedule(schedule.schedule_id, worker_id="worker-a")
            after_failure = schedules.list()[0]
            self.assertEqual(len(schedules.history(schedule.schedule_id)), 1)
            self.assertIsNone(after_failure.lease_owner)

            retried = dispatcher.dispatch_schedule(schedule.schedule_id, worker_id="worker-a")
            self.assertEqual(retried.status, RunStatus.COMPLETED)
            self.assertEqual(len(calls), 2)
            self.assertEqual(len(workflows.list_runs(schedule.workflow_id)), 1)
            self.assertEqual(len(schedules.history(schedule.schedule_id)), 1)
            self.assertEqual(schedules.history(schedule.schedule_id)[0].status, "completed")
        finally:
            directory.cleanup()

    def test_completed_occurrence_key_is_durable_and_idempotent(self) -> None:
        calls: list[int] = []
        directory, workflows, schedules, dispatcher, schedule = self._setup(lambda _payload: calls.append(1) or {"ok": True})
        try:
            occurrence = schedules.list()[0].next_run_at
            first = dispatcher.dispatch_schedule(schedule.schedule_id, worker_id="worker-a")
            same = workflows.start_run(schedule.workflow_id, first.version_id, f"schedule:{schedule.schedule_id}:{occurrence}")
            self.assertEqual(first.run_id, same.run_id)
            self.assertEqual(first.status, RunStatus.COMPLETED)
            self.assertEqual(same.status, RunStatus.COMPLETED)
            self.assertEqual(len(calls), 1)
            self.assertEqual(len(workflows.list_runs(schedule.workflow_id)), 1)
            self.assertEqual(len(schedules.history(schedule.schedule_id)), 1)
        finally:
            directory.cleanup()


if __name__ == "__main__":
    unittest.main()
