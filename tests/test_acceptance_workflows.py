"""Acceptance coverage for complete representative local Orville workflows.

These tests intentionally use deterministic local handlers and temporary roots. They
exercise the workflow contract end to end without provider credentials or network
access: objective normalization, DAG execution, independent verification, durable
checkpoint state, and retained artifacts.
"""

from __future__ import annotations

from pathlib import Path

from orville_core import CheckpointStore, OrchestrationEngine, TaskGraph, TaskIntake, TaskNode, verify_output
from orville_core.artifacts import ArtifactStore


def test_representative_coding_workflow_delivers_verified_artifact(tmp_path: Path) -> None:
    """A coding objective becomes a graph, executes locally, and delivers evidence."""
    artifact_store = ArtifactStore(tmp_path / "artifacts")
    checkpoint_store = CheckpointStore(tmp_path / "checkpoints")
    objective = {
        "objective": "Build a local status report generator",
        "deliverables": ["source", "tests", "documentation"],
        "acceptance_criteria": ["generated report exists", "verification passes"],
        "risk_level": "normal",
    }
    graph = TaskIntake.to_graph(objective)

    def intake_handler(task: TaskNode, context: dict[str, object]) -> dict[str, object]:
        output_path = artifact_store.root / "status_report.py"
        output_path.write_text("def render_status():\n    return 'ready'\n", encoding="utf-8")
        return {
            "text": "Generated the local status report implementation and documentation.",
            "artifact_path": output_path.as_posix(),
            "deliverables": task.inputs["deliverables"],
        }

    def verifier(task: TaskNode, output: dict[str, object], context: dict[str, object]):
        return verify_output(task.task_id, output, criteria=["generated", "documentation"])

    engine = OrchestrationEngine(checkpoint_store, {"intake.objective": intake_handler}, verifiers={"intake.objective": verifier})
    result = engine.run(graph, run_id="acceptance-coding")

    assert result.status.value == "completed"
    assert result.outputs["intake.objective"]["deliverables"] == ["source", "tests", "documentation"]
    assert result.outputs["intake.objective"]["artifact_path"].endswith("status_report.py")
    assert checkpoint_store.load("acceptance-coding").context["verifications"]["intake.objective"]["passed"] is True
    assert any(event.event_type == "run_completed" for event in result.events)
    records = artifact_store.list()
    assert [record.name for record in records] == ["status_report.py"]


def test_representative_research_workflow_preserves_evidence_and_verification(tmp_path: Path) -> None:
    """A research workflow gathers local evidence, synthesizes it, and verifies output."""
    checkpoint_store = CheckpointStore(tmp_path / "checkpoints")
    graph = TaskGraph(
        "acceptance-research",
        "Representative local research workflow",
        [
            TaskNode("gather", "Gather local evidence", "gather"),
            TaskNode("synthesize", "Synthesize findings", "synthesize", depends_on=["gather"]),
            TaskNode("review", "Review findings", "review", depends_on=["synthesize"]),
        ],
    )

    def gather(task: TaskNode, context: dict[str, object]) -> dict[str, object]:
        return {"sources": [{"source_id": "fixture-1", "title": "Local fixture", "claim": "offline execution works"}]}

    def synthesize(task: TaskNode, context: dict[str, object]) -> dict[str, object]:
        evidence = context["outputs"]["gather"]
        return {"text": "Offline execution works according to fixture-1.", "source_ids": [item["source_id"] for item in evidence["sources"]]}

    def review(task: TaskNode, context: dict[str, object]) -> dict[str, object]:
        synthesis = context["outputs"]["synthesize"]
        return {"text": synthesis["text"], "reviewed": True, "source_ids": synthesis["source_ids"]}

    def verify_review(task: TaskNode, output: dict[str, object], context: dict[str, object]):
        return verify_output(task.task_id, output, criteria=["offline execution works", "fixture-1"])

    engine = OrchestrationEngine(
        checkpoint_store,
        {"gather": gather, "synthesize": synthesize, "review": review},
        verifiers={"review": verify_review},
    )
    result = engine.run(graph, context={"objective": "Research local execution"}, run_id="acceptance-research")

    assert result.status.value == "completed"
    assert result.outputs["gather"]["sources"][0]["source_id"] == "fixture-1"
    assert result.outputs["review"]["reviewed"] is True
    checkpoint = checkpoint_store.load("acceptance-research")
    assert checkpoint.context["outputs"]["synthesize"]["source_ids"] == ["fixture-1"]
    assert checkpoint.context["verifications"]["review"]["passed"] is True
    assert [task.status.value for task in checkpoint.graph.tasks] == ["verified", "verified", "verified"]
    assert any(event.event_type == "task_verified_independently" and event.task_id == "review" for event in result.events)
