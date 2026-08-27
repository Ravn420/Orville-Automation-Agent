import json

import pytest

try:
    from fastapi.testclient import TestClient
    from orville_core.relay_server import create_relay_app
except ImportError:  # pragma: no cover
    TestClient = None
    create_relay_app = None


pytestmark = pytest.mark.skipif(TestClient is None, reason="FastAPI API extras are not installed")


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _limit=-1):
        return json.dumps(self.payload).encode()


def test_relay_requires_server_side_credentials():
    with pytest.raises(RuntimeError, match="BLACKBOX_API_KEY"):
        create_relay_app(client_token="orville-session")


def test_relay_rejects_missing_or_invalid_client_session():
    app = create_relay_app(blackbox_api_key="server-only-secret", client_token="orville-session")
    client = TestClient(app)
    assert client.get("/v1/models").status_code == 401
    assert client.get("/v1/models", headers={"X-Orville-Session": "wrong"}).status_code == 401


def test_relay_forwards_provider_key_only_upstream(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["headers"] = dict(request.headers)
        captured["body"] = json.loads(request.data.decode())
        captured["timeout"] = timeout
        return FakeResponse({"choices": [{"message": {"content": "ok"}}]})

    monkeypatch.setattr("orville_core.relay_server.urlopen", fake_urlopen)
    app = create_relay_app(blackbox_base_url="https://api.blackbox.test", blackbox_api_key="server-only-secret", client_token="orville-session")
    response = TestClient(app).post("/v1/chat/completions", headers={"X-Orville-Session": "orville-session"}, json={"model": "model", "messages": [{"role": "user", "content": "hello"}]})
    assert response.status_code == 200
    assert captured["headers"]["Authorization"] == "Bearer server-only-secret"
    assert captured["body"]["stream"] is False
    assert "server-only-secret" not in response.text


def test_relay_health_does_not_disclose_credential():
    app = create_relay_app(blackbox_api_key="server-only-secret", client_token="orville-session")
    body = TestClient(app).get("/health").json()
    assert body == {"ok": True, "status": "ready", "provider": "blackbox", "credential_configured": False, "managed_relay": True}
