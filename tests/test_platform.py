import tempfile
import unittest
from pathlib import Path

from orville_core.platform import PlanMilestone, PlatformStore, TaskLifecycle


class PlatformStoreTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.store = PlatformStore(Path(self.tempdir.name) / "platform.db")
        self.project = self.store.create_project("Example", owner_id="user-1")

    def tearDown(self):
        self.tempdir.cleanup()

    def test_plan_rejection_cancels_task_without_workspace_or_repository_mutation(self):
        task = self.store.create_task(self.project.project_id, "Add a safe feature", mode="coding")
        plan = self.store.create_plan(
            task.task_id,
            "Inspect and implement the feature",
            affected_files=("src/example.py",),
            milestones=[PlanMilestone("m-1", "placeholder", 1, "Inspect repository", "ide")],
        )
        approval = self.store.decide_plan(plan.plan_id, approved=False, actor_id="user-1", reason="Needs revision")
        self.assertEqual(approval.decision, "rejected")
        self.assertEqual(self.store.get_task(task.task_id).status, TaskLifecycle.CANCELLED)
        events = self.store.list_events(task.task_id)
        self.assertEqual([event["event_type"] for event in events], ["task.created", "task.status_changed", "task.status_changed", "task.status_changed", "plan.created", "plan.decision", "task.status_changed"])
        self.assertEqual(events[-1]["payload"]["reason"], "plan rejected")

    def test_approved_plan_enters_workspace_ready(self):
        task = self.store.create_task(self.project.project_id, "Implement the approved feature")
        plan = self.store.create_plan(task.task_id, "Plan feature", acceptance_criteria=("tests pass",))
        approval = self.store.decide_plan(plan.plan_id, approved=True, actor_id="user-1")
        self.assertEqual(approval.decision, "approved")
        self.assertEqual(self.store.get_task(task.task_id).status, TaskLifecycle.WORKSPACE_READY)

    def test_stale_or_invalid_transition_is_rejected(self):
        task = self.store.create_task(self.project.project_id, "Do work")
        with self.assertRaises(ValueError):
            self.store.transition_task(task.task_id, TaskLifecycle.COMPLETED)

    def test_event_payload_redacts_secrets_and_supports_cursor_replay(self):
        task = self.store.create_task(self.project.project_id, "Inspect")
        first = self.store.append_event(task.task_id, "tool.called", "agent", {"api_key": "secret", "nested": {"token": "abc"}})
        second = self.store.append_event(task.task_id, "tool.finished", "agent", {"status": "ok"})
        events = self.store.list_events(task.task_id, after=first)
        self.assertEqual([event["sequence"] for event in events], [second])
        all_events = self.store.list_events(task.task_id)
        tool_event = next(event for event in all_events if event["event_type"] == "tool.called")
        self.assertEqual(tool_event["payload"]["api_key"], "[REDACTED]")
        self.assertEqual(tool_event["payload"]["nested"]["token"], "[REDACTED]")


if __name__ == "__main__":
    unittest.main()
