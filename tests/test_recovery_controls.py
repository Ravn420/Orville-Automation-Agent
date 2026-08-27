from pathlib import Path

import pytest

from orville_core.checkpoint import CheckpointStore
from orville_core.engine import OrchestrationEngine
from orville_core.models import RunStatus, TaskGraph, TaskNode, TaskStatus


def make_graph(graph_id: str, *, max_attempts: int = 1) -> TaskGraph:
    return TaskGraph(graph_id, "recovery controls", [TaskNode("task-1", "task", "handler", max_attempts=max_attempts)])


def test_pause_resume_is_durable_and_reaches_completion(tmp_path: Path) -> None:
    store = CheckpointStore(tmp_path / "checkpoints")
    graph = make_graph("pause-graph")
    engine = OrchestrationEngine(store, {"handler": lambda task, context: {"ok": True}})

    paused = engine.run(graph, context={"pause_requested": True}, run_id="pause-run")
    assert paused.status is RunStatus.PAUSED
    assert store.load("pause-run").context["pause_requested"] is True

    engine.resume("pause-run")
    completed = engine.run(graph, run_id="pause-run", resume=True)
    assert completed.status is RunStatus.COMPLETED
    assert any(event.event_type == "run_resume_requested" for event in completed.events)


def test_retry_resets_failed_task_and_resumes_from_durable_state(tmp_path: Path) -> None:
    store = CheckpointStore(tmp_path / "checkpoints")
    graph = make_graph("retry-graph")
    calls = 0

    def flaky(task, context):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("synthetic failure")
        return {"recovered": True}

    engine = OrchestrationEngine(store, {"handler": flaky})
    failed = engine.run(graph, run_id="retry-run")
    assert failed.status is RunStatus.FAILED
    engine.retry("retry-run", "task-1")
    completed = engine.run(graph, run_id="retry-run", resume=True)
    assert completed.status is RunStatus.COMPLETED
    assert store.load("retry-run").graph.tasks[0].status is TaskStatus.VERIFIED
    assert any(event.event_type == "task_retry_requested" for event in completed.events)


def test_replay_and_state_inspection_are_bounded_and_non_mutating(tmp_path: Path) -> None:
    store = CheckpointStore(tmp_path / "checkpoints")
    graph = make_graph("inspect-graph")
    engine = OrchestrationEngine(store, {"handler": lambda task, context: {"secret": "not projected"}})
    result = engine.run(graph, run_id="inspect-run")

    before = store.load("inspect-run").to_dict()
    prefix = engine.replay("inspect-run", through_sequence=2)
    projection = engine.inspect_state("inspect-run")
    after = store.load("inspect-run").to_dict()
    assert prefix and prefix[-1].sequence <= 2
    assert projection["run_status"] == "completed"
    assert projection["task_count"] == 1
    assert projection["operation_checkpoint_count"] == 2
    assert "secret" not in projection
    assert before == after
    with pytest.raises(ValueError):
        engine.replay(result.run_id, through_sequence=-1)


def test_cancel_is_durable_and_clears_pause_request(tmp_path: Path) -> None:
    store = CheckpointStore(tmp_path / "checkpoints")
    graph = make_graph("cancel-graph")
    engine = OrchestrationEngine(store, {"handler": lambda task, context: {"ok": True}})
    engine.run(graph, context={"pause_requested": True}, run_id="cancel-run")
    engine.cancel("cancel-run")
    checkpoint = store.load("cancel-run")
    assert checkpoint.context["cancel_requested"] is True
    assert "pause_requested" not in checkpoint.context
