from __future__ import annotations

import pytest

from orville_core.agent_runtime import AgentProfile, AgentRuntimeStore
from orville_core.task_threads import TaskThreadStore, ThreadStatus


def test_agent_profile_persists_and_disabled_agents_cannot_spawn(tmp_path):
    database = tmp_path / "orville.db"
    threads = TaskThreadStore(database)
    runtime = AgentRuntimeStore(database, threads)
    profile = runtime.register_agent(AgentProfile("researcher", "Researcher", skills=("web-research",), connectors=("github",), tool_permissions=("read_file",)))
    assert runtime.get_agent(profile.agent_id).name == "Researcher"
    runtime.set_enabled(profile.agent_id, False)
    parent = threads.create_thread("Investigate")
    with pytest.raises(PermissionError, match="disabled"):
        runtime.create_child_task(parent.thread_id, "Child", agent_id=profile.agent_id)


def test_bounded_children_and_cancellation(tmp_path):
    database = tmp_path / "orville.db"
    threads = TaskThreadStore(database)
    runtime = AgentRuntimeStore(database, threads, max_depth=2, max_children=2)
    runtime.register_agent(AgentProfile("code", "Code Agent"))
    parent = threads.create_thread("Build")
    first, relation = runtime.create_child_task(parent.thread_id, "Write code", agent_id="code")
    second, _ = runtime.create_child_task(parent.thread_id, "Test code", agent_id="code", required=False)
    assert relation.depth == 1
    assert len(runtime.list_children(parent.thread_id)) == 2
    with pytest.raises(ValueError, match="child-task limit"):
        runtime.create_child_task(parent.thread_id, "Too many", agent_id="code")
    threads.transition(first.thread_id, ThreadStatus.RUNNING)
    threads.transition(second.thread_id, ThreadStatus.RUNNING)
    cancelled = runtime.cancel_tree(parent.thread_id)
    assert set(cancelled) == {first.thread_id, second.thread_id}
    assert threads.get_thread(first.thread_id).status == ThreadStatus.CANCELLED


def test_depth_limit(tmp_path):
    database = tmp_path / "orville.db"
    threads = TaskThreadStore(database)
    runtime = AgentRuntimeStore(database, threads, max_depth=1)
    runtime.register_agent(AgentProfile("worker", "Worker"))
    parent = threads.create_thread("Parent")
    child, _ = runtime.create_child_task(parent.thread_id, "Child", agent_id="worker")
    with pytest.raises(ValueError, match="depth limit"):
        runtime.create_child_task(child.thread_id, "Grandchild", agent_id="worker")
