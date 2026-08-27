from pathlib import Path

from orville_core.checkpoint import CheckpointStore
from orville_core.engine import OrchestrationEngine
from orville_core.models import TaskGraph, TaskNode, TaskStatus


def test_material_operation_has_durable_before_and_after_records(tmp_path: Path) -> None:
    store = CheckpointStore(tmp_path / "checkpoints")
    graph = TaskGraph(
        "graph-1",
        "operation checkpoint test",
        [TaskNode("task-1", "material", "handler", inputs={"operation_kind": "model"})],
    )
    result = OrchestrationEngine(store, {"handler": lambda task, context: {"ok": True}}).run(graph, run_id="run-1")

    checkpoint = store.load(result.run_id)
    records = checkpoint.operation_checkpoints
    assert [(record.phase, record.status, record.operation_kind) for record in records] == [
        ("before", "running", "model"),
        ("after", "succeeded", "model"),
    ]
    assert [record.sequence for record in records] == [1, 2]
    assert all(record.checkpoint_id.startswith("opcp-") for record in records)


def test_failed_operation_has_durable_after_record(tmp_path: Path) -> None:
    store = CheckpointStore(tmp_path / "checkpoints")
    graph = TaskGraph(
        "graph-2",
        "failed operation checkpoint test",
        [TaskNode("task-1", "material", "handler", inputs={"operation_kind": "artifact"})],
    )

    def fail(task, context):
        raise RuntimeError("synthetic failure")

    result = OrchestrationEngine(store, {"handler": fail}).run(graph, run_id="run-2")
    checkpoint = store.load(result.run_id)
    assert [record.phase for record in checkpoint.operation_checkpoints] == ["before", "after"]
    assert checkpoint.operation_checkpoints[-1].status == "failed"
    assert checkpoint.graph.tasks[0].status == TaskStatus.FAILED


def test_approval_operation_is_completed_after_approval_and_resume(tmp_path: Path) -> None:
    store = CheckpointStore(tmp_path / "checkpoints")
    graph = TaskGraph(
        "graph-3",
        "approval checkpoint test",
        [TaskNode("task-1", "protected", "handler", approval_required=True, inputs={"operation_kind": "approval"})],
    )
    engine = OrchestrationEngine(store, {"handler": lambda task, context: {"approved": True}})
    waiting = engine.run(graph, run_id="run-3")
    assert waiting.status.value == "waiting_approval"
    assert [record.phase for record in store.load("run-3").operation_checkpoints] == ["before"]

    engine.approve("run-3", "task-1")
    completed = engine.run(graph, run_id="run-3", resume=True)
    assert completed.status.value == "completed"
    records = store.load("run-3").operation_checkpoints
    assert [(record.phase, record.status) for record in records] == [
        ("before", "waiting_approval"),
        ("after", "approved"),
        ("before", "running"),
        ("after", "succeeded"),
    ]
