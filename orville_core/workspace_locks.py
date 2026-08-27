"""In-process dynamic workspace leases for parallel task execution."""
from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from time import monotonic
from typing import Any


class WorkspaceLeaseError(RuntimeError):
    pass


@dataclass(frozen=True)
class WorkspaceLease:
    lease_id: str
    task_id: str
    paths: frozenset[str]
    acquired_at: float

    def to_dict(self) -> dict[str, Any]:
        return {"lease_id": self.lease_id, "task_id": self.task_id, "paths": sorted(self.paths), "acquired_at": self.acquired_at}


@dataclass(frozen=True)
class BranchChange:
    branch_id: str
    path: str
    digest_before: str | None = None
    digest_after: str | None = None
    operation: str = "modify"


@dataclass(frozen=True)
class MergeDecision:
    status: str
    conflicts: tuple[str, ...] = ()
    approved_by: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"ready", "conflicted", "approved", "rejected"}:
            raise WorkspaceLeaseError("unsupported merge status")
        if self.status == "approved" and not self.approved_by:
            raise WorkspaceLeaseError("approved merge requires an approver")

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "conflicts": list(self.conflicts), "approved_by": self.approved_by}


def reconcile_branch_changes(changes: list[BranchChange]) -> MergeDecision:
    by_path: dict[str, list[BranchChange]] = {}
    for change in changes:
        path = change.path.replace("\\", "/").strip("/")
        if not path:
            raise WorkspaceLeaseError("branch change path must be non-empty")
        by_path.setdefault(path, []).append(change)
    conflicts = []
    for path, path_changes in by_path.items():
        if len(path_changes) < 2:
            continue
        signatures = {(item.operation, item.digest_after) for item in path_changes}
        if len(signatures) > 1:
            conflicts.append(path)
    return MergeDecision("conflicted" if conflicts else "ready", tuple(sorted(conflicts)))


class WorkspaceLeaseRegistry:
    def __init__(self) -> None:
        self._lock = RLock()
        self._leases: dict[str, WorkspaceLease] = {}

    def acquire(self, task_id: str, paths: tuple[str, ...] | list[str] = ()) -> WorkspaceLease:
        if not task_id.strip():
            raise WorkspaceLeaseError("task_id must be non-empty")
        normalized = frozenset(path.replace("\\", "/").strip("/") for path in paths if path.strip())
        with self._lock:
            conflicts = [lease for lease in self._leases.values() if normalized.intersection(lease.paths)]
            if conflicts:
                owners = ", ".join(sorted(lease.task_id for lease in conflicts))
                raise WorkspaceLeaseError(f"workspace paths are leased by: {owners}")
            lease = WorkspaceLease(f"lease-{task_id}-{len(self._leases) + 1}", task_id, normalized, monotonic())
            self._leases[lease.lease_id] = lease
            return lease

    def release(self, lease_id: str) -> None:
        with self._lock:
            self._leases.pop(lease_id, None)

    def release_task(self, task_id: str) -> None:
        with self._lock:
            for lease_id, lease in list(self._leases.items()):
                if lease.task_id == task_id:
                    self._leases.pop(lease_id, None)

    def active(self) -> list[WorkspaceLease]:
        with self._lock:
            return list(self._leases.values())
