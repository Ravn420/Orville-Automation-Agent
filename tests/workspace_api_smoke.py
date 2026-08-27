from pathlib import Path
from tempfile import TemporaryDirectory
from fastapi.testclient import TestClient
from orville_core.api import create_app

with TemporaryDirectory() as d:
    root = Path(d)
    (root / "app.py").write_text("print('one')\n", encoding="utf-8")
    app = create_app(api_token="test-token", storage="json", checkpoint_dir=root / ".orville")
    client = TestClient(app)
    headers = {"Authorization": "Bearer test-token"}
    response = client.post("/api/v1/workspaces", headers=headers, json={"root": str(root)})
    assert response.status_code == 200, response.text
    workspace_id = response.json()["workspace"]["workspace_id"]
    assert client.get(f"/api/v1/workspaces/{workspace_id}/files", headers=headers).status_code == 200
    file_response = client.get(f"/api/v1/workspaces/{workspace_id}/files/app.py", headers=headers)
    file_data = file_response.json()
    assert file_data["content"] == "print('one')\n"
    diff = client.post(f"/api/v1/workspaces/{workspace_id}/diff", headers=headers, json={"path": "app.py", "proposed_content": "print('two')\n", "expected_checksum": file_data.get("checksum")})
    assert diff.status_code == 200, diff.text
    blocked = client.post(f"/api/v1/workspaces/{workspace_id}/commands", headers=headers, json={"command": ["python", "-c", "print(1)"], "approved": False})
    assert blocked.status_code == 428
    ok = client.post(f"/api/v1/workspaces/{workspace_id}/commands", headers=headers, json={"command": ["python", "-c", "print(1)"], "approved": True})
    assert ok.status_code == 200, ok.text
    assert client.post(f"/api/v1/workspaces/{workspace_id}/repair", headers=headers, json={"max_attempts": 1}).status_code == 200
    assert client.post(f"/api/v1/workspaces/{workspace_id}/repair", headers=headers, json={"max_attempts": 1}).status_code == 409
print("workspace api smoke passed")
