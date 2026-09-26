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


def test_execute_thread_persists_redacted_result_and_replays_without_rerunning(tmp_path):
    database = tmp_path / "orville.db"
    threads = TaskThreadStore(database)
    runtime = AgentRuntimeStore(database, threads)
    thread = threads.create_thread("Summarize the local report")
    calls = []

    def handler(request, context):
        calls.append((request, context["thread_id"]))
        return {"answer": "ready", "api_key": "sk_test_secret_value"}

    first = runtime.execute_thread(thread.thread_id, handler)
    replay = runtime.execute_thread(thread.thread_id, handler)

    assert first.status == ThreadStatus.STOPPED
    assert first.output == {"answer": "ready", "api_key": "[REDACTED]"}
    assert replay.replayed is True
    assert replay.output == first.output
    assert len(calls) == 1
    assert threads.get_thread(thread.thread_id).stop_reason == "completed"


def test_execute_thread_records_failure_and_requires_explicit_retry(tmp_path):
    database = tmp_path / "orville.db"
    threads = TaskThreadStore(database)
    runtime = AgentRuntimeStore(database, threads)
    thread = threads.create_thread("Run a bounded operation")
    attempts = []

    def handler(_request, _context):
        attempts.append(1)
        if len(attempts) == 1:
            raise RuntimeError("token=sk_test_secret_value upstream unavailable")
        return "recovered"

    failed = runtime.execute_thread(thread.thread_id, handler)
    assert failed.status == ThreadStatus.FAILED
    assert failed.error == "token=[REDACTED] upstream unavailable"
    assert runtime.execute_thread(thread.thread_id, handler).status == ThreadStatus.FAILED
    recovered = runtime.execute_thread(thread.thread_id, handler, retry_failed=True)
    assert recovered.status == ThreadStatus.STOPPED
    assert recovered.output == "recovered"
    assert len(attempts) == 2


def test_execute_thread_rejects_disabled_profile_without_starting(tmp_path):
    database = tmp_path / "orville.db"
    threads = TaskThreadStore(database)
    runtime = AgentRuntimeStore(database, threads)
    runtime.register_agent(AgentProfile("disabled", "Disabled", enabled=False))
    thread = threads.create_thread("Do not run", agent_id="disabled")

    with pytest.raises(PermissionError, match="disabled"):
        runtime.execute_thread(thread.thread_id, lambda *_: "unsafe")

    assert threads.get_thread(thread.thread_id).status == ThreadStatus.PLANNED
