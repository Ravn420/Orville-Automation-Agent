import pytest

from orville_core.workspace_locks import WorkspaceLeaseError, WorkspaceLeaseRegistry


def test_workspace_leases_reject_overlapping_paths_and_release_cleanly():
    registry = WorkspaceLeaseRegistry()
    first = registry.acquire("task-a", ["src/app.py"])
    with pytest.raises(WorkspaceLeaseError, match="task-a"):
        registry.acquire("task-b", ["src/app.py"])
    independent = registry.acquire("task-b", ["tests/test_app.py"])
    assert {lease.task_id for lease in registry.active()} == {"task-a", "task-b"}
    registry.release(first.lease_id)
    registry.release(independent.lease_id)
    assert registry.active() == []


def test_branch_reconciliation_detects_conflicts_and_normalizes_paths():
    from orville_core import BranchChange, reconcile_branch_changes

    ready = reconcile_branch_changes([BranchChange("a", "src/a.py", digest_after="same"), BranchChange("b", "src/b.py", digest_after="other")])
    assert ready.status == "ready"
    conflicted = reconcile_branch_changes([BranchChange("a", "src/a.py", digest_after="one"), BranchChange("b", "\\src\\a.py", digest_after="two")])
    assert conflicted.status == "conflicted"
    assert conflicted.conflicts == ("src/a.py",)


def test_merge_decision_requires_approver_for_approval():
    from orville_core import MergeDecision, WorkspaceLeaseError

    with pytest.raises(WorkspaceLeaseError, match="approver"):
        MergeDecision("approved")
    assert MergeDecision("approved", approved_by="orchestration").to_dict()["approved_by"] == "orchestration"


def test_workspace_leases_normalize_separators_and_release_by_task():
    registry = WorkspaceLeaseRegistry()
    lease = registry.acquire("task", ["\\src\\app.py\\"])
    assert lease.paths == frozenset({"src/app.py"})
    registry.release_task("task")
    assert registry.active() == []
