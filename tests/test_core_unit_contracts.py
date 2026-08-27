from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from orville_core import CheckpointStore, OrchestrationEngine, RunStatus, TaskGraph, TaskNode, TaskStatus
from orville_core.artifacts import ArtifactStore
from orville_core.routing import RoutingRequest, validate_endpoint


class CoreUnitContractTests(unittest.TestCase):
    def test_task_parsing_round_trip_preserves_execution_fields(self) -> None:
        source = {
            "task_id": "parse-1",
            "title": "Parse task",
            "handler": "handler",
            "depends_on": ["setup"],
            "inputs": {"value": 3},
            "max_attempts": 2,
            "timeout_seconds": 4.5,
            "approval_required": True,
            "approved": False,
            "idempotency_key": "task:parse-1",
            "owned_paths": ["docs/output.md"],
            "required_inputs": ["value"],
            "owner": "worker-1",
            "status": "ready",
            "attempts": 1,
            "output": {"ok": True},
            "error": None,
        }
        task = TaskNode.from_dict(source)
        self.assertEqual(task.to_dict(), source)
        self.assertEqual(TaskNode.from_dict(task.to_dict()).status, TaskStatus.READY)

    def test_graph_validation_rejects_unknown_dependency_and_owned_path_without_owner(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown tasks"):
            TaskGraph("unknown", "Unknown dependency", [TaskNode("a", "A", "noop", depends_on=["missing"])])
        with self.assertRaisesRegex(ValueError, "no owner"):
            TaskGraph("owner", "Owner required", [TaskNode("a", "A", "noop", owned_paths=["a.txt"])])

    def test_routing_validation_is_local_and_fail_closed(self) -> None:
        self.assertEqual(validate_endpoint("https://api.example.test/v1"), "https://api.example.test/v1")
        self.assertEqual(validate_endpoint("http://127.0.0.1:8080", local=True), "http://127.0.0.1:8080")
        with self.assertRaisesRegex(ValueError, "credentials"):
            validate_endpoint("https://user:pass@api.example.test")
        with self.assertRaisesRegex(ValueError, "unknown capabilities"):
            RoutingRequest(required_capabilities=frozenset({"telepathy"}))
        with self.assertRaisesRegex(ValueError, "privacy_class"):
            RoutingRequest(privacy_class="secret")

    def test_state_transition_persists_verified_task_and_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            graph = TaskGraph("state", "State transitions", [TaskNode("work", "Work", "echo")])
            result = OrchestrationEngine(CheckpointStore(directory), {"echo": lambda task, _context: {"value": task.task_id}}).run(graph, run_id="state-run")
            self.assertEqual(result.status, RunStatus.COMPLETED)
            checkpoint = CheckpointStore(directory).load("state-run")
            task = checkpoint.graph.task_map()["work"]
            self.assertEqual(task.status, TaskStatus.VERIFIED)
            self.assertEqual(task.attempts, 1)
            self.assertEqual(checkpoint.context["outputs"]["work"], {"value": "work"})
            self.assertIn("run_completed", [event.event_type for event in checkpoint.events])

    def test_artifact_registration_records_hash_media_type_and_explicit_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "artifacts"
            source = root / "report.json"
            root.mkdir()
            source.write_text('{"ok": true}', encoding="utf-8")
            record = ArtifactStore(root).register(source, artifact_id="artifact-1")
            self.assertEqual(record.artifact_id, "artifact-1")
            self.assertEqual(record.relative_path, "report.json")
            self.assertEqual(record.media_type, "application/json")
            self.assertEqual(record.size, source.stat().st_size)
            self.assertEqual(len(record.sha256), 64)


if __name__ == "__main__":
    unittest.main()
