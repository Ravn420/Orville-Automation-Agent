"""API-level tests for the MemoryStore routes (/api/v1/memory*)."""
import time

from fastapi.testclient import TestClient

from orville_core.api import create_app


def _client(tmp_path):
    app = create_app(api_token="mem-token", storage="json", checkpoint_dir=tmp_path / ".orville")
    return TestClient(app)


def test_memory_store_put_get_list_delete_isolation(tmp_path):
    client = _client(tmp_path)
    headers = {"Authorization": "Bearer mem-token"}

    # Put task memory
    put = client.post("/api/v1/memory", headers=headers, json={
        "scope": "task",
        "owner_id": "task-1",
        "key": "preference",
        "value": {"tone": "concise"},
        "source": "user",
    })
    assert put.status_code == 200
    record = put.json()["memory"]
    assert record["scope"] == "task"
    assert record["owner_id"] == "task-1"
    assert record["key"] == "preference"
    assert record["value"]["tone"] == "concise"
    assert record["memory_id"].startswith("mem-")

    # Inspect (list) task memory
    listing = client.get("/api/v1/memory", headers=headers, params={"scope": "task", "owner_id": "task-1"})
    assert listing.status_code == 200
    inspected = listing.json()
    assert inspected["scope"] == "task"
    assert inspected["owner_id"] == "task-1"
    assert inspected["count"] == 1
    assert inspected["isolated"] is True

    # Put project memory for a different owner
    client.post("/api/v1/memory", headers=headers, json={
        "scope": "project",
        "owner_id": "project-1",
        "key": "preference",
        "value": "formal",
    })

    # Isolation: task-1 cannot see project-1 memory
    task_listing = client.get("/api/v1/memory", headers=headers, params={"scope": "task", "owner_id": "task-1"})
    assert task_listing.json()["count"] == 1
    project_listing = client.get("/api/v1/memory", headers=headers, params={"scope": "project", "owner_id": "project-1"})
    assert project_listing.json()["count"] == 1

    # Delete with wrong owner fails
    wrong_delete = client.delete("/api/v1/memory/" + record["memory_id"], headers=headers, params={"owner_id": "task-2"})
    assert wrong_delete.status_code == 404

    # Delete with correct owner succeeds
    correct_delete = client.delete("/api/v1/memory/" + record["memory_id"], headers=headers, params={"owner_id": "task-1"})
    assert correct_delete.status_code == 200
    assert correct_delete.json()["deleted"] is True

    # Verify deleted memory is not listed
    post_delete = client.get("/api/v1/memory", headers=headers, params={"scope": "task", "owner_id": "task-1"})
    assert post_delete.json()["count"] == 0


def test_memory_store_secret_redaction_via_api(tmp_path):
    client = _client(tmp_path)
    headers = {"Authorization": "Bearer mem-token"}

    put = client.post("/api/v1/memory", headers=headers, json={
        "scope": "task",
        "owner_id": "task-1",
        "key": "creds",
        "value": {"api_key": "sk-secret-key-12345678", "token": "tok-abc123def456"},
    })
    assert put.status_code == 200
    body = put.json()["memory"]["value"]
    assert body["api_key"] == "[REDACTED]"
    assert body["token"] == "[REDACTED]"
    assert "sk-secret-key-12345678" not in put.text


def test_memory_store_ttl_retention_plan_and_purge(tmp_path):
    import time
    client = _client(tmp_path)
    headers = {"Authorization": "Bearer mem-token"}

    # Put a short-lived memory
    client.post("/api/v1/memory", headers=headers, json={
        "scope": "project",
        "owner_id": "project-1",
        "key": "temporary",
        "value": "ephemeral",
        "ttl_seconds": 1,
    })

    # Wait for the memory to expire (TTL is 1 second)
    time.sleep(1.5)

    # Retention plan with future cutoff shows the expired candidate
    future = "9999-01-01T00:00:00+00:00"
    plan = client.get("/api/v1/memory/retention/plan", headers=headers)
    assert plan.status_code == 200
    assert plan.json()["status"] == "plan_only"
    assert plan.json()["expired_count"] >= 1

    # Purge requires explicit confirmation
    no_confirm = client.post("/api/v1/memory/retention/purge", headers=headers, json={})
    assert no_confirm.status_code == 400
    assert "explicit confirmation required" in no_confirm.json()["detail"]

    # Purge with confirmation and future cutoff
    purge = client.post("/api/v1/memory/retention/purge", headers=headers, json={"confirm": True, "before": future})
    assert purge.status_code == 200
    assert purge.json()["purged"] >= 1

    # Verify the expired memory is gone
    listing = client.get("/api/v1/memory", headers=headers, params={"scope": "project", "owner_id": "project-1"})
    assert listing.json()["count"] == 0


def test_memory_store_validation_errors(tmp_path):
    client = _client(tmp_path)
    headers = {"Authorization": "Bearer mem-token"}

    # Invalid scope
    bad_scope = client.post("/api/v1/memory", headers=headers, json={
        "scope": "user",
        "owner_id": "user-1",
        "key": "k",
        "value": "v",
    })
    assert bad_scope.status_code == 400

    # Invalid TTL
    bad_ttl = client.post("/api/v1/memory", headers=headers, json={
        "scope": "task",
        "owner_id": "task-1",
        "key": "k",
        "value": "v",
        "ttl_seconds": 0,
    })
    assert bad_ttl.status_code == 400
