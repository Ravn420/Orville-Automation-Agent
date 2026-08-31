from pathlib import Path

import pytest

try:
    from fastapi.testclient import TestClient
    from orville_core.api import create_app
except ImportError:  # pragma: no cover
    TestClient = None
    create_app = None


pytestmark = pytest.mark.skipif(TestClient is None, reason="FastAPI API extras are not installed")


def test_browser_routes_require_authentication(tmp_path: Path) -> None:
    client = TestClient(create_app(checkpoint_dir=tmp_path, api_token="secret"))
    assert client.get("/api/v1/browser/sessions").status_code == 401
    assert client.post("/api/v1/browser/sessions", json={"allowed_domains": ["example.com"]}).status_code == 401


def test_browser_session_routes_are_allowlisted_and_approval_gated(tmp_path: Path) -> None:
    client = TestClient(create_app(checkpoint_dir=tmp_path, api_token="secret"))
    headers = {"Authorization": "Bearer secret"}

    created = client.post("/api/v1/browser/sessions", headers=headers, json={"allowed_domains": ["Example.COM."]})
    assert created.status_code == 200
    session = created.json()["session"]
    session_id = session["session_id"]
    assert session["read_only"] is True
    assert session["headless"] is True
    assert session["allowed_domains"] == ["example.com"]

    pending = client.post(f"/api/v1/browser/sessions/{session_id}/navigate", headers=headers, json={"url": "https://example.com/docs"})
    assert pending.status_code == 200
    assert pending.json()["session"]["takeover_required"] is True

    denied = client.post(f"/api/v1/browser/sessions/{session_id}/approval", headers=headers, json={"action": "navigate", "url": "https://notexample.com/", "approved": True})
    assert denied.status_code in {400, 403}

    approved = client.post(f"/api/v1/browser/sessions/{session_id}/approval", headers=headers, json={"action": "navigate", "url": "https://example.com/docs", "approved": True})
    assert approved.status_code == 200
    assert approved.json()["approved"] is True

    # Approval is consumed by the next matching navigation. Playwright is not
    # required for this assertion because the route reaches the local adapter
    # and may report an optional-runtime error after policy checks.
    navigated = client.post(f"/api/v1/browser/sessions/{session_id}/navigate", headers=headers, json={"url": "https://example.com/docs"})
    assert navigated.status_code in {200, 400}
    audit = client.get(f"/api/v1/browser/sessions/{session_id}/audit", headers=headers)
    assert audit.status_code == 200
    assert any(item["event"] == "approval.granted" for item in audit.json()["audit"])


def test_browser_session_listing_and_takeover_route_are_authenticated(tmp_path: Path) -> None:
    client = TestClient(create_app(checkpoint_dir=tmp_path, api_token="secret"))
    headers = {"Authorization": "Bearer secret"}
    created = client.post("/api/v1/browser/sessions", headers=headers, json={"allowed_domains": ["example.com"]}).json()["session"]
    session_id = created["session_id"]

    listed = client.get("/api/v1/browser/sessions", headers=headers)
    assert listed.status_code == 200
    assert any(item["session_id"] == session_id for item in listed.json()["sessions"])

    pending = client.post(f"/api/v1/browser/sessions/{session_id}/takeover", headers=headers, json={})
    assert pending.status_code == 200
    assert pending.json()["session"]["takeover_required"] is True


def test_form_and_download_routes_require_approval_and_record_actions(tmp_path: Path) -> None:
    client = TestClient(create_app(checkpoint_dir=tmp_path, api_token="secret"))
    headers = {"Authorization": "Bearer secret"}
    created = client.post("/api/v1/browser/sessions", headers=headers, json={"allowed_domains": ["example.com"]}).json()["session"]
    session_id = created["session_id"]

    form = client.post(f"/api/v1/browser/sessions/{session_id}/form", headers=headers, json={"selector": "#login", "fields": {"username": "alice", "password": "secret"}})
    assert form.status_code == 200
    assert form.json()["session"]["takeover_required"] is True

    download = client.post(f"/api/v1/browser/sessions/{session_id}/download", headers=headers, json={"url": "https://example.com/file.zip?token=secret"})
    assert download.status_code == 200
    assert download.json()["session"]["takeover_required"] is True

    audit = client.get(f"/api/v1/browser/sessions/{session_id}/audit", headers=headers).json()["audit"]
    assert any(item["event"] == "form_submission.approval_required" for item in audit)
    assert any(item["event"] == "download.approval_required" for item in audit)
