from __future__ import annotations

import json

import pytest

from orville_core.memory import MemoryStore


def test_task_and_project_memory_are_isolated_and_redacted(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    task = store.put("task", "task-1", "preference", {"api_key": "secret", "tone": "concise"})
    store.put("project", "project-1", "preference", {"tone": "formal"})
    assert task.value["api_key"] != "secret"
    assert store.get("task", "task-2", "preference") is None
    assert store.get("project", "project-1", "preference").value["tone"] == "formal"
    assert store.inspect("task", "task-1")["isolated"] is True
    assert "secret" not in json.dumps(store.inspect("task", "task-1"))


def test_put_is_user_editable_and_replaces_one_key(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    first = store.put("task", "task-1", "note", "one")
    second = store.put("task", "task-1", "note", "two")
    assert first.memory_id == second.memory_id
    assert store.get("task", "task-1", "note").value == "two"
    assert len(store.list("task", "task-1")) == 1


def test_retention_is_plan_only_until_explicit_purge(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    record = store.put("project", "project-1", "temporary", "value", ttl_seconds=1)
    expired = "9999-01-01T00:00:00+00:00"
    plan = store.retention_plan(now=expired)
    assert plan["status"] == "plan_only"
    assert plan["expired_count"] == 1
    assert store.get("project", "project-1", "temporary") is not None
    assert store.purge_expired(before=expired) == 1
    assert store.get("project", "project-1", "temporary") is None
    assert store.list("project", "project-1", include_expired=True) == []
    assert record.memory_id == plan["candidates"][0]["memory_id"]


def test_delete_requires_owner_and_is_tombstoned(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    record = store.put("task", "task-1", "note", "value")
    assert store.delete(record.memory_id, owner_id="task-2") is False
    assert store.delete(record.memory_id, owner_id="task-1") is True
    assert store.delete(record.memory_id, owner_id="task-1") is False


def test_memory_validation_is_bounded(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    with pytest.raises(ValueError):
        store.put("user", "user-1", "key", "value")
    with pytest.raises(ValueError):
        store.put("task", "task-1", "key", "value", ttl_seconds=0)
