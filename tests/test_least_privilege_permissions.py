"""Focused tests for task-scoped least-privilege permissions."""

from pathlib import Path

import pytest

from orville_core.security import LeastPrivilegePolicy, SecurityViolation


def test_empty_grants_deny_all_resource_classes(tmp_path: Path) -> None:
    policy = LeastPrivilegePolicy()
    with pytest.raises(SecurityViolation):
        policy.check_connector("missing")
    with pytest.raises(SecurityViolation):
        policy.check_repository("missing")
    with pytest.raises(SecurityViolation):
        policy.resolve_file(tmp_path / "file.txt")
    with pytest.raises(SecurityViolation):
        policy.check_remote("api.example.test", "health")


def test_connector_scopes_and_repository_writes_are_minimized() -> None:
    policy = LeastPrivilegePolicy(
        connector_scopes={"issues": frozenset({"read"})},
        repository_ids=frozenset({"repo-1"}),
    )
    policy.check_connector("issues", {"read"})
    policy.check_repository("repo-1")
    with pytest.raises(SecurityViolation, match="scopes are insufficient"):
        policy.check_connector("issues", {"read", "write"})
    with pytest.raises(SecurityViolation, match="writes are disabled"):
        policy.check_repository("repo-1", write=True)
    with pytest.raises(SecurityViolation):
        policy.check_repository("repo-2")


def test_file_roots_and_remote_host_action_allowlists_are_independent(tmp_path: Path) -> None:
    root = tmp_path / "task"
    root.mkdir()
    allowed_file = root / "output.txt"
    allowed_file.write_text("fixture", encoding="utf-8")
    policy = LeastPrivilegePolicy(
        file_roots=(root,),
        remote_hosts=frozenset({"API.EXAMPLE.TEST."}),
        remote_actions=frozenset({"health"}),
    )
    assert policy.resolve_file(allowed_file) == allowed_file.resolve()
    policy.check_remote("api.example.test", "health")
    with pytest.raises(SecurityViolation):
        policy.resolve_file(tmp_path / "outside.txt")
    with pytest.raises(SecurityViolation):
        policy.check_remote("api.example.test", "publish")
    with pytest.raises(SecurityViolation):
        policy.check_remote("other.example.test", "health")


def test_write_grants_are_explicit(tmp_path: Path) -> None:
    root = tmp_path / "task"
    root.mkdir()
    policy = LeastPrivilegePolicy(
        repository_ids=frozenset({"repo-1"}),
        file_roots=(root,),
        allow_repository_write=True,
        allow_file_write=True,
    )
    policy.check_repository("repo-1", write=True)
    assert policy.resolve_file(root / "new.txt", write=True) == (root / "new.txt").resolve()
