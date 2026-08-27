from __future__ import annotations

import json

import pytest

from orville_core.task_threads import (
    SchemaError,
    TaskThreadStore,
    ThreadStatus,
    validate_schema,
)


SCHEMA = {
    "type": "object",
    "properties": {
        "accept": {"type": "boolean"},
        "mode": {"type": "string", "enum": ["safe", "fast"]},
    },
    "required": ["accept", "mode"],
    "additionalProperties": False,
}


def test_thread_messages_are_durable_and_redacted(tmp_path):
    database = tmp_path / "threads.sqlite"
    store = TaskThreadStore(database)
    thread = store.create_thread("Build the service")
    store.append_message(thread.thread_id, role="assistant", kind="text", content={"api_key": "secret", "text": "done"})

    reloaded = TaskThreadStore(database)
    messages = reloaded.list_messages(thread.thread_id)
    assert messages[0].content == "Build the service"
    assert messages[1].content["api_key"] != "secret"
    assert "secret" not in json.dumps(messages[1].content)


def test_schema_driven_wait_and_approval(tmp_path):
    store = TaskThreadStore(tmp_path / "threads.sqlite")
    thread = store.create_thread("Deploy")
    store.transition(thread.thread_id, ThreadStatus.RUNNING)
    event = store.request_wait(thread.thread_id, event_type="deployAction", description="Deploy the approved build", input_schema=SCHEMA, risk_class="high")
    assert store.get_thread(thread.thread_id).status == ThreadStatus.WAITING
    resolved = store.resolve_wait(event.event_id, {"accept": True, "mode": "safe"})
    assert resolved.status == "accepted"
    assert store.get_thread(thread.thread_id).status == ThreadStatus.RUNNING


def test_rejected_wait_cancels_thread(tmp_path):
    store = TaskThreadStore(tmp_path / "threads.sqlite")
    thread = store.create_thread("Delete files")
    store.transition(thread.thread_id, ThreadStatus.RUNNING)
    event = store.request_wait(thread.thread_id, event_type="deleteAction", description="Delete files", input_schema=SCHEMA, risk_class="critical")
    store.resolve_wait(event.event_id, {"accept": False, "mode": "safe"}, accept=False)
    assert store.get_thread(thread.thread_id).status == ThreadStatus.CANCELLED


def test_structured_output_is_consumed_once_and_has_zero_fallback(tmp_path):
    store = TaskThreadStore(tmp_path / "threads.sqlite")
    thread = store.create_thread("Extract data")
    store.arm_structured_output(thread.thread_id, {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"], "additionalProperties": False})
    result = store.complete_structured_output(thread.thread_id, {"wrong": True})
    assert result.success is False
    assert result.value == {"name": ""}
    second = store.complete_structured_output(thread.thread_id, {"name": "Orville"})
    assert second.success is False
    assert "armed" in (second.error or "")


def test_schema_rejects_unsafe_or_ambiguous_definitions():
    with pytest.raises(SchemaError, match="additionalProperties"):
        validate_schema({"type": "object", "properties": {}, "required": [], "additionalProperties": True})
    with pytest.raises(SchemaError, match="unsupported schema keywords"):
        validate_schema({"type": "object", "properties": {"x": {"type": "string", "pattern": ".*"}}, "required": ["x"], "additionalProperties": False})


def test_recovery_marks_running_threads(tmp_path):
    store = TaskThreadStore(tmp_path / "threads.sqlite")
    thread = store.create_thread("Long job")
    store.transition(thread.thread_id, ThreadStatus.RUNNING)
    recovered = store.recover_after_restart()
    assert [item.thread_id for item in recovered] == [thread.thread_id]
    assert store.get_thread(thread.thread_id).status == ThreadStatus.RECOVERING


def test_expected_version_prevents_lost_update(tmp_path):
    store = TaskThreadStore(tmp_path / "threads.sqlite")
    thread = store.create_thread("Versioned job")
    store.transition(thread.thread_id, ThreadStatus.RUNNING, expected_version=thread.version)
    with pytest.raises(RuntimeError, match="concurrently"):
        store.transition(thread.thread_id, ThreadStatus.WAITING, expected_version=thread.version)
