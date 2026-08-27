import json
import tempfile
import threading
import time
import unittest
from pathlib import Path

from orville_core import CheckpointStore, OrchestrationEngine, RunStatus, TaskGraph, TaskNode, TaskStatus


class OrchestrationTests(unittest.TestCase):
    def test_graph_rejects_cycles(self):
        with self.assertRaisesRegex(ValueError, "cycle"):
            TaskGraph(
                graph_id="cycle",
                name="Cycle",
                tasks=[
                    TaskNode("a", "A", "noop", depends_on=["b"]),
                    TaskNode("b", "B", "noop", depends_on=["a"]),
                ],
            )

    def test_executes_dependencies_in_order_and_persists_events(self):
        with tempfile.TemporaryDirectory() as directory:
            calls = []

            def handler(task, context):
                calls.append(task.task_id)
                previous = context.get("outputs", {}).get("compile")
                return {"task": task.task_id, "input": task.inputs.get("value"), "previous": previous}

            graph = TaskGraph(
                graph_id="order",
                name="Dependency order",
                tasks=[
                    TaskNode("compile", "Compile", "run", inputs={"value": 1}),
                    TaskNode("test", "Test", "run", depends_on=["compile"], inputs={"value": 2}),
                    TaskNode("package", "Package", "run", depends_on=["test"]),
                ],
            )
            store = CheckpointStore(directory)
            engine = OrchestrationEngine(store, {"run": handler})
            result = engine.run(graph, run_id="order-run")

            self.assertEqual(result.status, RunStatus.COMPLETED)
            self.assertEqual(calls, ["compile", "test", "package"])
            self.assertEqual(result.outputs["test"]["previous"]["task"], "compile")
            self.assertEqual(store.load("order-run").graph.task_map()["package"].status, TaskStatus.VERIFIED)
            self.assertGreaterEqual(len(result.events), 10)

    def test_missing_handler_blocks_dependents(self):
        with tempfile.TemporaryDirectory() as directory:
            graph = TaskGraph(
                graph_id="missing",
                name="Missing handler",
                tasks=[
                    TaskNode("first", "First", "not_registered"),
                    TaskNode("second", "Second", "noop", depends_on=["first"]),
                ],
            )
            result = OrchestrationEngine(CheckpointStore(directory)).run(graph, run_id="missing-run")
            self.assertEqual(result.status, RunStatus.BLOCKED)
            checkpoint = CheckpointStore(directory).load("missing-run")
            self.assertEqual(checkpoint.graph.task_map()["first"].status, TaskStatus.FAILED)
            self.assertEqual(checkpoint.graph.task_map()["second"].status, TaskStatus.BLOCKED)

    def test_resume_retries_failed_task_from_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            def recover(task, context):
                return "recovered"

            graph = TaskGraph(
                graph_id="resume",
                name="Resume",
                tasks=[TaskNode("flaky", "Flaky", "flaky", max_attempts=2)],
            )
            store = CheckpointStore(directory)
            checkpoint = __import__("orville_core").Checkpoint(
                run_id="resume-run", graph=graph, run_status=RunStatus.FAILED
            )
            task = checkpoint.graph.task_map()["flaky"]
            task.status = TaskStatus.FAILED
            task.attempts = 1
            task.error = "RuntimeError: transient failure"
            store.save(checkpoint)
            second = OrchestrationEngine(store, {"flaky": recover}).run(graph, run_id="resume-run", resume=True)
            self.assertEqual(second.status, RunStatus.COMPLETED)
            self.assertEqual(second.outputs["flaky"], "recovered")

    def test_default_parallelism_is_bounded_to_three_tasks(self):
        with tempfile.TemporaryDirectory() as directory:
            active = 0
            peak = 0
            lock = threading.Lock()

            def handler(task, context):
                nonlocal active, peak
                with lock:
                    active += 1
                    peak = max(peak, active)
                time.sleep(0.03)
                with lock:
                    active -= 1
                return task.task_id

            graph = TaskGraph(
                "parallel-default",
                "parallel-default",
                [TaskNode(str(index), str(index), "work") for index in range(6)],
            )
            result = OrchestrationEngine(CheckpointStore(directory), {"work": handler}).run(graph)
            self.assertEqual(result.status, RunStatus.COMPLETED)
            self.assertLessEqual(peak, 3)

    def test_parallel_ready_tasks_execute_and_reconcile(self):
        with tempfile.TemporaryDirectory() as directory:
            def handler(task, context):
                time.sleep(0.02)
                return task.task_id
            graph = TaskGraph("parallel", "parallel", [TaskNode("a", "A", "work"), TaskNode("b", "B", "work")])
            result = OrchestrationEngine(CheckpointStore(directory), {"work": handler}, max_workers=2).run(graph)
            self.assertEqual(result.status, RunStatus.COMPLETED)
            self.assertEqual(result.outputs, {"a": "a", "b": "b"})
            self.assertTrue(any(event.details.get("parallel") for event in result.events if event.event_type == "task_verified"))

    def test_task_timeout_is_persisted_as_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            def slow(task, context):
                time.sleep(0.03)
                return "late"
            graph = TaskGraph("timeout", "timeout", [TaskNode("slow", "Slow", "slow", timeout_seconds=0.001)])
            result = OrchestrationEngine(CheckpointStore(directory), {"slow": slow}).run(graph)
            self.assertEqual(result.status, RunStatus.FAILED)
            self.assertIn("timeout", result.events[-2].details.get("error", "").lower())

    def test_conditional_task_is_skipped(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = OrchestrationEngine(CheckpointStore(directory), {"noop": lambda task, context: "ran"})
            graph = TaskGraph("condition", "condition", [TaskNode("skip", "Skip", "noop", inputs={"when": {"key": "flags.enabled", "equals": True}})])
            result = engine.run(graph, context={"flags": {"enabled": False}})
            self.assertEqual(result.status, RunStatus.COMPLETED)
            self.assertTrue(result.outputs["skip"]["skipped"])

    def test_approval_pauses_and_resume_after_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = OrchestrationEngine(CheckpointStore(directory), {"noop": lambda task, context: "approved"})
            graph = TaskGraph("approval", "approval", [TaskNode("gate", "Gate", "noop", approval_required=True)])
            waiting = engine.run(graph, run_id="approval-run")
            self.assertEqual(waiting.status, RunStatus.WAITING_APPROVAL)
            engine.approve("approval-run", "gate")
            completed = engine.run(graph, run_id="approval-run", resume=True)
            self.assertEqual(completed.status, RunStatus.COMPLETED)

    def test_cancel_request_is_persisted(self):
        with tempfile.TemporaryDirectory() as directory:
            store = CheckpointStore(directory)
            engine = OrchestrationEngine(store, {"noop": lambda task, context: "ran"})
            graph = TaskGraph("cancel", "cancel", [TaskNode("task", "Task", "noop")])
            result = engine.run(graph, run_id="cancel-run", context={"cancel_requested": True})
            self.assertEqual(result.status, RunStatus.CANCELLED)

    def test_idempotency_reuses_persisted_output(self):
        with tempfile.TemporaryDirectory() as directory:
            calls = []
            def handler(task, context):
                calls.append(task.task_id)
                return "once"
            engine = OrchestrationEngine(CheckpointStore(directory), {"work": handler})
            first = TaskGraph("idem-1", "idem", [TaskNode("work", "Work", "work", idempotency_key="same")])
            second = TaskGraph("idem-2", "idem", [TaskNode("work", "Work", "work", idempotency_key="same")])
            engine.run(first, run_id="idem-run-1")
            result = engine.run(second, run_id="idem-run-2", context={"idempotency": {"same": "cached"}})
            self.assertEqual(result.outputs["work"], "cached")
            self.assertEqual(calls, ["work"])

    def test_graph_rejects_owned_path_conflicts(self):
        with self.assertRaisesRegex(ValueError, "owned path conflict"):
            TaskGraph("ownership", "ownership", [TaskNode("a", "A", "noop", owned_paths=["src/main.py"]), TaskNode("b", "B", "noop", owned_paths=["src/main.py"])])

    def test_checkpoint_file_is_valid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            graph = TaskGraph("json", "JSON", [TaskNode("one", "One", "noop")])
            store = CheckpointStore(directory)
            OrchestrationEngine(store, {"noop": lambda task, context: True}).run(graph, run_id="json-run")
            payload = json.loads(Path(directory, "json-run.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 1)
            self.assertEqual(payload["run_status"], "completed")


class GraphInputOwnershipTests(unittest.TestCase):
    def test_missing_required_input_is_rejected_before_execution(self):
        with self.assertRaisesRegex(ValueError, "missing required inputs"):
            TaskGraph("missing-input", "Missing input", [TaskNode("task", "Task", "noop", required_inputs=["workspace"], inputs={})])

    def test_owned_paths_require_explicit_owner(self):
        with self.assertRaisesRegex(ValueError, "no owner"):
            TaskGraph("missing-owner", "Missing owner", [TaskNode("task", "Task", "noop", owned_paths=["src/main.py"])])

    def test_required_inputs_and_owner_round_trip(self):
        graph = TaskGraph("round-trip", "Round trip", [TaskNode("task", "Task", "noop", required_inputs=["workspace"], inputs={"workspace": "/repo"}, owned_paths=["src/main.py"], owner="code")])
        restored = TaskGraph.from_dict(graph.to_dict())
        self.assertEqual(restored.tasks[0].required_inputs, ["workspace"])
        self.assertEqual(restored.tasks[0].owner, "code")


if __name__ == "__main__":
    unittest.main()
