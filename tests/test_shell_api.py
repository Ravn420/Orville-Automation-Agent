from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from orville_core.api import create_app


def test_restored_shell_control_plane_contracts():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        app = create_app(api_token="shell-token", storage="json", checkpoint_dir=root / ".orville")
        client = TestClient(app)
        headers = {"Authorization": "Bearer shell-token"}

        created = client.post("/api/v1/projects", headers=headers, json={"name": "Shell Project", "description": "test"})
        assert created.status_code == 200
        project = created.json()["project"]
        project_id = project["project_id"]

        task = client.post(f"/api/v1/projects/{project_id}/tasks", headers=headers, json={"request": "Add a health check", "mode": "code-completion"})
        assert task.status_code == 200
        task_id = task.json()["task"]["task_id"]

        assert client.get("/api/v1/projects", headers=headers).json()["projects"][0]["project_id"] == project_id
        assert client.get(f"/api/v1/projects/{project_id}/tasks", headers=headers).json()["tasks"][0]["task_id"] == task_id

        memory = client.post(f"/api/v1/projects/{project_id}/memory", headers=headers, json={"key": "style", "value": "Use type hints"})
        assert memory.status_code == 200
        assert client.get(f"/api/v1/projects/{project_id}/memory", headers=headers).json()["memory"][0]["value"] == "Use type hints"

        agent = client.get("/api/v1/personal-agent", headers=headers)
        assert agent.status_code == 200
        assert agent.json()["agent"]["computer"] == "local-windows-host"
        capabilities = client.get("/api/v1/capabilities", headers=headers)
        assert capabilities.status_code == 200
        flags = capabilities.json()["feature_flags"]
        assert flags["agentic_code_generation"] is True
        assert flags["workflow_automation"] is True
        assert flags["browser_automation"] is False
        assert any(item["adapter_id"] == "local-workspace" for item in capabilities.json()["adapters"])
        blocked_research = client.post("/api/v1/research/fetch", headers=headers, json={"locator": "https://example.com"})
        assert blocked_research.status_code == 400
        assert "allowlisted" in blocked_research.json()["detail"]
        artifact = client.post("/api/v1/artifacts/text", headers=headers, json={"name": "report.md", "content": "# Verified output\n"})
        assert artifact.status_code == 200
        assert artifact.json()["artifact"]["name"] == "report.md"
        traversal = client.post("/api/v1/artifacts/text", headers=headers, json={"name": "../escape.md", "content": "blocked"})
        assert traversal.status_code == 200
        assert traversal.json()["artifact"]["name"] == "escape.md"
        paused = client.post("/api/v1/personal-agent", headers=headers, json={"enabled": False})
        assert paused.json()["agent"]["state"] == "paused"
