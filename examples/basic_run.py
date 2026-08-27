"""Run a minimal Orville graph and persist its checkpoint."""

from pathlib import Path

from orville_core import CheckpointStore, OrchestrationEngine, TaskGraph, TaskNode


def echo(task: TaskNode, context: dict) -> dict:
    """Example task handler; production handlers should remain deterministic where possible."""
    return {"message": task.inputs.get("message", "completed"), "project": context.get("project")}


def main() -> None:
    graph = TaskGraph(
        graph_id="basic-demo",
        name="Basic Orville demonstration",
        tasks=[
            TaskNode("prepare", "Prepare workspace", "echo", inputs={"message": "workspace ready"}),
            TaskNode("finish", "Finish run", "echo", depends_on=["prepare"], inputs={"message": "run complete"}),
        ],
    )
    store = CheckpointStore(Path(".orville/checkpoints"))
    result = OrchestrationEngine(store, {"echo": echo}).run(
        graph,
        context={"project": "Orville"},
        run_id="basic-demo-run",
    )
    print(f"status={result.status} run_id={result.run_id} outputs={result.outputs}")


if __name__ == "__main__":
    main()
