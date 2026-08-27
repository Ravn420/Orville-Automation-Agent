import tempfile
import unittest
from pathlib import Path

from orville_core.automation import RunStatus, TriggerType, WorkflowExecutor, WorkflowStep, WorkflowStore


class AutomationTests(unittest.TestCase):
    def test_idempotent_runs_and_dead_letter(self):
        with tempfile.TemporaryDirectory() as directory:
            store = WorkflowStore(Path(directory) / "automation.db")
            workflow_id = store.create_workflow("Daily check")
            version = store.add_version(workflow_id, TriggerType.SCHEDULED, (WorkflowStep("step-1", "echo", {"value": 1}),))
            first = store.start_run(workflow_id, version.version_id, "same-key")
            same = store.start_run(workflow_id, version.version_id, "same-key")
            self.assertEqual(first.run_id, same.run_id)
            failed = store.retry_or_dead_letter(first.run_id, "failure", max_attempts=2)
            self.assertEqual(failed.status, RunStatus.RUNNING)
            dead = store.retry_or_dead_letter(first.run_id, "failure", max_attempts=2)
            self.assertEqual(dead.status, RunStatus.DEAD_LETTER)

    def test_executor_requires_approval_and_merges_structured_output(self):
        executor = WorkflowExecutor({"echo": lambda payload: {"output": payload["value"]}})
        steps = (WorkflowStep("protected", "echo", {"value": "ok"}, requires_approval=True),)
        with self.assertRaises(PermissionError):
            executor.execute(steps, {})
        self.assertEqual(executor.execute(steps, {}, approved_steps=frozenset({"protected"}))["output"], "ok")


if __name__ == "__main__":
    unittest.main()

    def test_dispatcher_executes_enabled_schedule_and_releases_lease(self):
        from orville_core.automation import AutomationDispatcher
        from orville_core.scheduler import ScheduleStore
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "automation.db"
            workflows = WorkflowStore(database)
            schedules = ScheduleStore(database)
            workflow_id = workflows.create_workflow("Scheduled workflow")
            version = workflows.add_version(workflow_id, TriggerType.SCHEDULED, (WorkflowStep("echo", "echo", {"value": "done"}),))
            workflows.set_enabled(workflow_id, version.version_id, True)
            schedule = schedules.create("schedule-dispatch", workflow_id, 60)
            schedules.set_enabled(schedule.schedule_id, True)
            dispatcher = AutomationDispatcher(schedules, workflows, WorkflowExecutor({"echo": lambda payload: {"result": payload["value"]}}))
            run = dispatcher.dispatch_schedule(schedule.schedule_id, {"input": "ok"}, worker_id="test-worker")
            self.assertEqual(run.status, RunStatus.COMPLETED)
            self.assertIsNone(schedules.list()[0].lease_owner)
            self.assertEqual(len(workflows.list_runs(workflow_id)), 1)

    def test_dispatcher_failure_records_run_and_releases_lease(self):
        from orville_core.automation import AutomationDispatcher
        from orville_core.scheduler import ScheduleStore
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "automation.db"
            workflows = WorkflowStore(database)
            schedules = ScheduleStore(database)
            workflow_id = workflows.create_workflow("Failing workflow")
            version = workflows.add_version(workflow_id, TriggerType.SCHEDULED, (WorkflowStep("missing", "missing"),))
            workflows.set_enabled(workflow_id, version.version_id, True)
            schedule = schedules.create("schedule-failure", workflow_id, 60)
            schedules.set_enabled(schedule.schedule_id, True)
            dispatcher = AutomationDispatcher(schedules, workflows, WorkflowExecutor())
            with self.assertRaises(LookupError):
                dispatcher.dispatch_schedule(schedule.schedule_id)
            self.assertIsNone(schedules.list()[0].lease_owner)
            self.assertEqual(workflows.list_runs(workflow_id)[0].status, RunStatus.FAILED)
