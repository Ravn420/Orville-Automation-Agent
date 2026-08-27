"""Focused tests for durable approval checkpoints."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from orville_core.automation import TriggerType, WorkflowStore


class ApprovalCheckpointTests(unittest.TestCase):
    """Verify approval requests are durable, bounded, and single-use."""

    def test_checkpoint_is_durable_and_resolution_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "approval.db"
            store = WorkflowStore(database)
            workflow_id = store.create_workflow("Protected workflow")
            version = store.add_version(workflow_id, TriggerType.MANUAL, ())
            run = store.start_run(workflow_id, version.version_id, "approval-key")
            checkpoint = store.create_approval_checkpoint(run.run_id, "publish", action_summary="Publish reviewed artifact", target_summary="Artifact release-1")
            same = store.create_approval_checkpoint(run.run_id, "publish", action_summary="Changed text is ignored", target_summary="Changed target is ignored")
            self.assertEqual(checkpoint.approval_id, same.approval_id)
            self.assertEqual(checkpoint.status, "pending")
            resolved = store.resolve_approval_checkpoint(checkpoint.approval_id, approved=True, approver_id="operator-1", reason="Reviewed")
            repeated = store.resolve_approval_checkpoint(checkpoint.approval_id, approved=False, approver_id="operator-2", reason="Must not overwrite")
            self.assertEqual(resolved.status, "approved")
            self.assertEqual(repeated.status, "approved")
            reopened = WorkflowStore(database).approval_checkpoint(checkpoint.approval_id)
            self.assertEqual(reopened.approver_id, "operator-1")

    def test_checkpoint_requires_nonempty_safe_summaries_and_approver(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = WorkflowStore(Path(directory) / "approval.db")
            with self.assertRaises(ValueError):
                store.create_approval_checkpoint("run-1", "step-1", action_summary="", target_summary="target")
            checkpoint = store.create_approval_checkpoint("run-1", "step-1", action_summary="action", target_summary="target")
            with self.assertRaises(ValueError):
                store.resolve_approval_checkpoint(checkpoint.approval_id, approved=True, approver_id=" ")

    def test_checkpoint_source_and_contract_preserve_fail_closed_boundary(self) -> None:
        root = Path(__file__).resolve().parents[1]
        source = (root / "orville_core" / "automation.py").read_text(encoding="utf-8")
        document = (root / "docs" / "APPROVAL_CHECKPOINTS.md").read_text(encoding="utf-8")
        for phrase in ("ApprovalCheckpoint", "create_approval_checkpoint", "resolve_approval_checkpoint", "requires_approval"):
            self.assertIn(phrase, source)
        for phrase in ("irreversible", "high-impact", "single-use", "fail-closed", "typed acknowledgement", "safe reason codes"):
            self.assertIn(phrase, document)


if __name__ == "__main__":
    unittest.main()
