from __future__ import annotations

import unittest

from orville_core.automation import WorkflowExecutor, WorkflowStep


class WorkflowDryRunTests(unittest.TestCase):
    def test_dry_run_skips_external_mutation_and_reports_preview(self) -> None:
        calls: list[str] = []
        executor = WorkflowExecutor({
            "local": lambda _payload: calls.append("local") or {"local": True},
            "publish": lambda _payload: calls.append("publish") or {"published": True},
        })
        steps = (
            WorkflowStep("prepare", "local"),
            WorkflowStep("publish", "publish", {"mutates_external_state": True}, requires_approval=True),
        )
        result = executor.execute(steps, {}, dry_run=True)
        self.assertEqual(calls, ["local"])
        self.assertTrue(result["_dry_run"])
        self.assertEqual(result["local"], True)
        self.assertEqual(result["dry_run_actions"], [{
            "step_id": "publish",
            "kind": "publish",
            "executed": False,
            "requires_approval": True,
            "reason": "external side effects are disabled in dry-run mode",
        }])
        self.assertNotIn("published", result)

    def test_normal_execution_still_requires_approval_for_mutating_step(self) -> None:
        executor = WorkflowExecutor({"publish": lambda _payload: {"published": True}})
        step = WorkflowStep("publish", "publish", {"mutates_external_state": True}, requires_approval=True)
        with self.assertRaisesRegex(PermissionError, "requires approval"):
            executor.execute((step,), {})
        self.assertEqual(executor.execute((step,), {}, approved_steps=frozenset({"publish"}))["published"], True)

    def test_dry_run_requires_no_provider_or_network_boundary(self) -> None:
        executor = WorkflowExecutor({})
        result = executor.execute((WorkflowStep("delete", "delete", {"mutates_external_state": True}),), {}, dry_run=True)
        self.assertEqual(result["dry_run_actions"][0]["step_id"], "delete")
        self.assertTrue(result["_dry_run"])


if __name__ == "__main__":
    unittest.main()
