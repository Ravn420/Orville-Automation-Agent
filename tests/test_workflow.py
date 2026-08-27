import tempfile
import unittest
from pathlib import Path

from orville_core import (
    AgentDefinition,
    AgentRegistry,
    LLMRequest,
    CheckpointStore,
    LLMResponse,
    OrchestrationEngine,
    ProjectState,
    ProviderConfig,
    ProviderRegistry,
    ProviderRouter,
    SoftwareObjective,
    TaskGraph,
    TaskIntake,
    TaskNode,
    VerificationRecord,
    default_agent_registry,
    model_task_handler,
    verify_output,
)


class FakeProvider:
    def __init__(self, provider_id="local"):
        self.config = ProviderConfig(provider_id, "ollama", "model", "http://localhost")

    def generate(self, request):
        return LLMResponse(self.config.provider_id, self.config.model, "generated answer", {})

    def stream(self, request):
        yield type("Chunk", (), {"text": "generated answer"})()

    def embed(self, inputs):
        return type("Embedding", (), {"embeddings": [[1.0]]})()

    def health_check(self):
        return {"ok": True}


class WorkflowTests(unittest.TestCase):
    def test_project_state_round_trips_atomically(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "STATE.json")
            state = ProjectState("orville", "build software", active_phase="intake", decisions=["local first"])
            state.save(path)
            restored = ProjectState.load(path)
            self.assertEqual(restored.project_id, "orville")
            self.assertEqual(restored.decisions, ["local first"])

    def test_intake_normalizes_objective_to_graph(self):
        graph = TaskIntake.to_graph({"objective": "Build a task manager", "deliverables": ["source", "tests"], "risk_level": "normal"})
        self.assertEqual(graph.tasks[0].handler, "intake.objective")
        self.assertIn("Build a task manager", graph.tasks[0].inputs["objective"])
        self.assertEqual(graph.tasks[0].inputs["classification"], "coding")

    def test_intake_classifies_and_requests_missing_details(self):
        objective = SoftwareObjective("Research and compare local models")
        self.assertEqual(TaskIntake.classify(objective.objective), "research")
        self.assertEqual(len(TaskIntake.clarification_questions(objective)), 3)

    def test_agent_registry_selects_verifier_separately(self):
        registry = default_agent_registry()
        self.assertEqual(registry.select("coding").agent_id, "code")
        self.assertEqual(registry.select("verification", verifier=True).agent_id, "verification")
        with self.assertRaises(LookupError):
            registry.select("coding", verifier=True)

    def test_verification_record_is_independent_and_reports_defect(self):
        record = verify_output("task-1", {"text": "short answer"}, criteria=["required phrase"])
        self.assertIsInstance(record, VerificationRecord)
        self.assertFalse(record.passed)
        self.assertIn("required phrase", record.defects)

    def test_model_handler_returns_routing_metadata(self):
        providers = ProviderRegistry()
        providers.register(FakeProvider())
        handler = model_task_handler(ProviderRouter(providers))
        result = handler(type("Task", (), {"task_id": "model-1", "inputs": {"prompt": "hello"}})(), {})
        self.assertEqual(result["text"], "generated answer")
        self.assertEqual(result["routing"]["selected_provider"], "local")
        self.assertEqual(result["routing"]["attempts"][0]["success"], True)

    def test_engine_persists_independent_verification_result(self):
        with tempfile.TemporaryDirectory() as directory:
            def handler(task, context):
                return {"text": "accepted output"}

            def verifier(task, output, context):
                return verify_output(task.task_id, output, criteria=["accepted"])

            engine = OrchestrationEngine(CheckpointStore(Path(directory)), {"run": handler}, verifiers={"run": verifier})
            graph = TaskGraph("verify-graph", "Verification graph", [TaskNode("run", "Run", "run")])
            result = engine.run(graph, run_id="verify-run")
            self.assertEqual(result.status.value, "completed")
            checkpoint = engine.checkpoint_store.load("verify-run")
            self.assertTrue(checkpoint.context["verifications"]["run"]["passed"])
            self.assertTrue(any(event.event_type == "task_verified_independently" for event in result.events))

    def test_model_handler_runs_through_checkpointed_engine(self):
        with tempfile.TemporaryDirectory() as directory:
            providers = ProviderRegistry()
            providers.register(FakeProvider())
            engine = OrchestrationEngine(CheckpointStore(Path(directory)), {"model": model_task_handler(ProviderRouter(providers))})
            graph = TaskGraph("model-graph", "Model graph", [TaskNode("generate", "Generate", "model", inputs={"prompt": "hello"})])
            result = engine.run(graph, run_id="model-run")
            self.assertEqual(result.status.value, "completed")
            self.assertEqual(result.outputs["generate"]["provider_id"], "local")
            self.assertEqual(engine.checkpoint_store.load("model-run").context["outputs"]["generate"]["routing"]["selected_provider"], "local")


class ClarificationGateTests(unittest.TestCase):
    def test_missing_planning_details_are_warnings(self):
        objective = SoftwareObjective("Build a service")
        gate = TaskIntake.clarification_gate(objective)
        self.assertFalse(gate["required"])
        self.assertTrue(gate["warnings"])

    def test_sensitive_action_requires_hard_gate(self):
        objective = SoftwareObjective("Deploy the service to production", deliverables=["deployment"], acceptance_criteria=["health check passes"], target_environment="production")
        gate = TaskIntake.clarification_gate(objective)
        self.assertTrue(gate["required"])
        self.assertTrue(gate["hard_gates"])

    def test_conflicting_constraints_are_detected(self):
        objective = SoftwareObjective("Keep the service offline but connect to the internet", deliverables=["code"], acceptance_criteria=["tests pass"], target_environment="linux")
        gate = TaskIntake.clarification_gate(objective)
        self.assertTrue(any("Conflicting constraints" in item for item in gate["hard_gates"]))


if __name__ == "__main__":
    unittest.main()
