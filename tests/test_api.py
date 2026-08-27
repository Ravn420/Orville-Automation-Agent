import tempfile
import unittest
from pathlib import Path

try:
    from fastapi.testclient import TestClient
    from orville_core.api import create_app
except ImportError:  # pragma: no cover
    TestClient = None
    create_app = None


@unittest.skipIf(TestClient is None, "FastAPI API extras are not installed")
class ApiTests(unittest.TestCase):
    def test_authentication_is_required(self):
        with tempfile.TemporaryDirectory() as directory:
            client = TestClient(create_app(checkpoint_dir=Path(directory), api_token="secret"))
            self.assertEqual(client.get("/api/v1/health").status_code, 401)
            self.assertEqual(client.get("/api/v1/health", headers={"Authorization": "Bearer secret"}).status_code, 200)

    def test_provider_discovery_privacy_policy_and_redacted_export(self):
        with tempfile.TemporaryDirectory() as directory:
            client = TestClient(create_app(checkpoint_dir=Path(directory), api_token="secret"))
            headers = {"Authorization": "Bearer secret"}
            added = client.post("/api/v1/providers", headers=headers, json={"provider_id": "manual", "provider_type": "anthropic", "model": "claude", "base_url": "https://api.anthropic.com"})
            self.assertEqual(added.status_code, 200)
            discovered = client.get("/api/v1/providers/manual/models", headers=headers)
            self.assertEqual(discovered.status_code, 200)
            self.assertTrue(discovered.json()["catalog"]["manual_model_entry"])
            policy = client.post("/api/v1/routing/privacy", headers=headers, json={"privacy_class": "restricted", "allowed_provider_ids": ["manual"], "local_only": False})
            self.assertEqual(policy.status_code, 200)
            self.assertTrue(policy.json()["policy"]["local_only"])
            policies = client.get("/api/v1/routing/privacy", headers=headers)
            self.assertEqual(policies.json()["policies"][0]["privacy_class"], "restricted")
            exported = client.get("/api/v1/config/export/redacted", headers=headers)
            self.assertEqual(exported.status_code, 200)
            self.assertFalse(exported.json()["secrets_included"])
            self.assertNotIn("api_key", exported.json()["providers"][0])
            local_policy = client.post("/api/v1/routing/privacy", headers=headers, json={"privacy_class": "local_only", "allowed_provider_ids": ["manual"], "local_only": False})
            self.assertEqual(local_policy.status_code, 200)
            self.assertTrue(local_policy.json()["policy"]["local_only"])
            cloud_policy = client.post("/api/v1/routing/privacy", headers=headers, json={"privacy_class": "cloud_approved", "allowed_provider_ids": ["manual"], "local_only": False, "allow_fallback": True})
            self.assertEqual(cloud_policy.status_code, 200)
            self.assertFalse(cloud_policy.json()["policy"]["local_only"])
            self.assertTrue(cloud_policy.json()["policy"]["allow_fallback"])

    def test_provider_rate_limit_and_usage_routes(self):
        with tempfile.TemporaryDirectory() as directory:
            client = TestClient(create_app(checkpoint_dir=Path(directory), api_token="secret"))
            headers = {"Authorization": "Bearer secret"}
            configured = client.post("/api/v1/provider-rate-limits", headers=headers, json={"provider_id": "local", "window_seconds": 60, "max_calls": 2, "max_tokens": 1000})
            self.assertEqual(configured.status_code, 200)
            inspected = client.get("/api/v1/provider-rate-limits/local", headers=headers)
            self.assertEqual(inspected.json()["rate_limit"]["max_calls"], 2)
            usage = client.get("/api/v1/provider-usage/local", headers=headers)
            self.assertEqual(usage.status_code, 200)
            self.assertEqual(usage.json()["usage"]["calls"], 0)

    def test_objective_intake_is_normalized(self):
        with tempfile.TemporaryDirectory() as directory:
            client = TestClient(create_app(checkpoint_dir=Path(directory), api_token="secret"))
            response = client.post("/api/v1/objectives", headers={"Authorization": "Bearer secret"}, json={"objective": "Build a task manager API", "deliverables": ["source code"]})
            self.assertEqual(response.status_code, 200)
            body = response.json()
            self.assertTrue(body["run_id"])
            self.assertTrue(body["task_ids"])
            self.assertEqual(body["classification"], "coding")

    def test_project_task_plan_and_event_lifecycle(self):
        with tempfile.TemporaryDirectory() as directory:
            client = TestClient(create_app(checkpoint_dir=Path(directory), api_token="secret"))
            headers = {"Authorization": "Bearer secret"}
            project_response = client.post("/api/v1/projects", headers=headers, json={"name": "Demo"})
            self.assertEqual(project_response.status_code, 200)
            project_id = project_response.json()["project"]["project_id"]
            task_response = client.post(f"/api/v1/projects/{project_id}/tasks", headers=headers, json={"request": "Add a test"})
            self.assertEqual(task_response.status_code, 200)
            task_id = task_response.json()["task"]["task_id"]
            plan_response = client.post(f"/api/v1/tasks/{task_id}/plan", headers=headers, json={"objective": "Inspect and implement", "affected_files": ["src/example.py"]})
            self.assertEqual(plan_response.status_code, 200)
            plan_id = plan_response.json()["plan"]["plan_id"]
            decision_response = client.post(f"/api/v1/plans/{plan_id}/approve", headers=headers, json={"approved": False, "actor_id": "user-1", "reason": "Review later"})
            self.assertEqual(decision_response.status_code, 200)
            events_response = client.get(f"/api/v1/tasks/{task_id}/events?after=0", headers=headers)
            self.assertEqual(events_response.status_code, 200)
            self.assertTrue(any(event["event_type"] == "plan.decision" for event in events_response.json()["events"]))

    def test_workflow_preview_and_security_routes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "preview-root"
            root.mkdir()
            client = TestClient(create_app(checkpoint_dir=Path(directory), api_token="secret"))
            headers = {"Authorization": "Bearer secret"}
            project = client.post("/api/v1/projects", headers=headers, json={"name": "Workflow Project"}).json()["project"]
            project_id = project["project_id"]
            workflow = client.post(f"/api/v1/projects/{project_id}/workflows", headers=headers, json={"name": "Manual", "trigger": "manual", "steps": []})
            self.assertEqual(workflow.status_code, 200)
            body = workflow.json()
            run = client.post(f"/api/v1/workflows/{body['workflow_id']}/run", headers=headers, json={"version_id": body["version_id"], "idempotency_key": "run-1"})
            self.assertEqual(run.status_code, 200)
            preview = client.post(f"/api/v1/projects/{project_id}/preview", headers=headers, json={"revision_id": "rev-1", "root": str(root), "route": "/", "viewport": "desktop"})
            self.assertEqual(preview.status_code, 200)
            findings = client.get(f"/api/v1/projects/{project_id}/security/findings", headers=headers)
            self.assertEqual(findings.status_code, 200)

    def test_project_state_is_redacted_to_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            client = TestClient(create_app(checkpoint_dir=Path(directory), api_token="secret"))
            response = client.get("/api/v1/state", headers={"Authorization": "Bearer secret"})
            self.assertEqual(response.status_code, 200)
            self.assertIn("project_id", response.json())


if __name__ == "__main__":
    unittest.main()


def test_api_key_is_absent_from_export_checkpoints_and_errors():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        client = TestClient(create_app(checkpoint_dir=root, api_token="secret"))
        headers = {"Authorization": "Bearer secret"}
        response = client.post("/api/v1/providers", headers=headers, json={"provider_id": "blackbox", "provider_type": "blackbox", "model": "blackboxai", "base_url": "https://api.blackbox.ai", "api_key": "sk-live-secret123"})
        assert response.status_code == 200
        exported = client.get("/api/v1/config/export/redacted", headers=headers)
        assert exported.status_code == 200
        assert "sk-live-secret123" not in exported.text
        state = client.get("/api/v1/state", headers=headers)
        assert state.status_code == 200
        assert "sk-live-secret123" not in state.text
        for persisted in root.rglob("*"):
            if persisted.is_file():
                assert "sk-live-secret123" not in persisted.read_bytes().decode("utf-8", errors="ignore")
