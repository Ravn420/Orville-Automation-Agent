import pytest

from orville_core.cloud_relay import (
    AccessMode,
    AccessRecord,
    CloudRelayBoundary,
    QuotaLedger,
    RelayConfig,
    RelayError,
    RelayRequest,
    RelayStatus,
)


def boundary() -> CloudRelayBoundary:
    relay = CloudRelayBoundary(
        RelayConfig(
            relay_url="https://relay.example.test/v1",
            model="blackboxai/openai/gpt-5.5",
            allowed_hosts=frozenset({"relay.example.test"}),
        ),
        quota=QuotaLedger({"managed": 2, "user_connected": 10}),
    )
    relay.set_access(AccessRecord(AccessMode.MANAGED, RelayStatus.READY, subject="device-1", plan="orville-free"))
    return relay


def test_managed_access_admits_without_client_provider_credential():
    relay = boundary()
    result = relay.admit(RelayRequest(subject="device-1", estimated_units=1))
    assert result["access_mode"] == "managed"
    assert result["provider_credential_in_client"] is False
    assert result["remaining_units"] == 1


def test_user_connected_access_is_separate_from_managed_access():
    relay = boundary()
    relay.set_access(AccessRecord(AccessMode.USER_CONNECTED, RelayStatus.READY, subject="user-1", plan="blackbox-pro"))
    result = relay.admit(RelayRequest(subject="user-1", mode=AccessMode.USER_CONNECTED, estimated_units=1))
    assert result["access_mode"] == "user_connected"
    assert relay.quota.remaining("device-1", AccessMode.MANAGED) == 2
    assert relay.quota.remaining("user-1", AccessMode.USER_CONNECTED) == 9


def test_disconnected_blackbox_access_is_actionable():
    relay = boundary()
    with pytest.raises(RelayError, match="not_connected"):
        relay.admit(RelayRequest(subject="unknown-device"))


def test_restricted_content_requires_explicit_remote_approval():
    with pytest.raises(RelayError, match="explicit approval"):
        RelayRequest(subject="device-1", privacy_class="restricted")
    request = RelayRequest(subject="device-1", privacy_class="restricted", approved_remote=True)
    assert request.privacy_class == "restricted"


def test_quota_is_enforced_per_subject_and_mode():
    relay = boundary()
    relay.admit(RelayRequest(subject="device-1", estimated_units=2))
    with pytest.raises(RelayError, match="quota exceeded"):
        relay.admit(RelayRequest(subject="device-1", estimated_units=1))


def test_relay_config_rejects_non_https_urls():
    with pytest.raises(ValueError, match="HTTPS"):
        RelayConfig(relay_url="http://relay.example.test")


def test_public_status_contains_no_provider_secret():
    relay = boundary()
    status = relay.public_status("device-1")
    assert status["provider_credential_in_client"] is False
    assert status["relay"]["credential_configured"] is False
    assert "api_key" not in str(status).lower()


def test_managed_blackbox_provider_factory_rejects_client_api_key():
    from orville_core.providers import ProviderConfig, create_provider

    with pytest.raises(ValueError, match="must not receive"):
        create_provider(ProviderConfig(provider_id="relay", provider_type="blackbox-relay", model="model", base_url="https://relay.example.test", api_key="blackbox-secret"))


def test_managed_blackbox_provider_rejects_unsupported_capabilities_preflight():
    from orville_core.providers import LLMRequest, ModelCapabilities, ProviderConfig, ProviderError, create_provider

    provider = create_provider(ProviderConfig(provider_id="relay", provider_type="blackbox-relay", model="model", base_url="https://relay.example.test/v1", capabilities=ModelCapabilities(text=True)))
    with pytest.raises(ProviderError, match="streaming capability"):
        list(provider.stream(LLMRequest(messages=[{"role": "user", "content": "hello"}])))
    with pytest.raises(ProviderError, match="tool_calling capability"):
        provider.generate(LLMRequest(messages=[{"role": "user", "content": "hello"}], tools=[{"type": "function"}]))
    with pytest.raises(ProviderError, match="structured_output capability"):
        provider.generate(LLMRequest(messages=[{"role": "user", "content": "hello"}], response_schema={"type": "object"}))
    with pytest.raises(ProviderError, match="embeddings capability"):
        provider.embed("hello")


def test_managed_blackbox_provider_uses_openai_compatible_relay_contract():
    from orville_core.providers import LLMRequest, ProviderConfig, create_provider

    class FakeHttp:
        def __init__(self):
            self.calls = []

        def request(self, method, url, *, headers=None, payload=None, timeout=60.0):
            self.calls.append((method, url, headers or {}, payload or {}))
            if url.endswith("/health"):
                return {"ok": True, "status": "ready"}
            return {"choices": [{"message": {"content": "relay response"}, "finish_reason": "stop"}]}

        def stream_json(self, *args, **kwargs):
            return iter([])

    http = FakeHttp()
    provider = create_provider(ProviderConfig(provider_id="relay", provider_type="blackbox-relay", model="model", base_url="https://relay.example.test/v1"), http)
    response = provider.generate(LLMRequest(messages=[{"role": "user", "content": "hello"}]))
    assert response.text == "relay response"
    assert http.calls[0][1] == "https://relay.example.test/v1/chat/completions"
    assert "Authorization" not in http.calls[0][2]
    assert provider.health_check()["credential_configured"] is False


def test_blackbox_fallback_selects_first_configured_local_provider_for_failure_states():
    relay = boundary()
    for relay_status in (RelayStatus.NOT_CONNECTED, RelayStatus.EXPIRED, RelayStatus.INVALID, RelayStatus.RATE_LIMITED, RelayStatus.UNAVAILABLE, RelayStatus.DISABLED):
        relay.set_access(AccessRecord(AccessMode.MANAGED, relay_status, subject="device-1"))
        decision = relay.fallback_status("device-1", ["ollama", "local-secondary"])
        assert decision.available is True
        assert decision.fallback_provider_id == "ollama"
        assert relay.public_status("device-1", ["ollama"]) ["fallback"]["fallback_provider_id"] == "ollama"


def test_blackbox_fallback_reports_actionable_unavailable_state_without_local_provider():
    relay = boundary()
    relay.set_access(AccessRecord(AccessMode.MANAGED, RelayStatus.RATE_LIMITED, subject="device-1"))
    decision = relay.fallback_status("device-1")
    assert decision.available is False
    assert decision.fallback_provider_id is None
    assert "configure a local provider" in decision.reason


def test_blackbox_ready_state_does_not_replace_relay_with_local_fallback():
    relay = boundary()
    decision = relay.fallback_status("device-1", ["ollama"])
    assert decision.available is True
    assert decision.fallback_provider_id is None
    assert decision.primary_status is RelayStatus.READY


def test_fallback_status_is_redacted_and_actionable():
    relay = boundary()
    relay.set_access(AccessRecord(AccessMode.MANAGED, RelayStatus.UNAVAILABLE, subject="device-1"))
    public = relay.public_status("device-1", ["ollama"])
    assert public["fallback"] == {
        "primary_status": "unavailable",
        "fallback_provider_id": "ollama",
        "available": True,
        "reason": "Blackbox relay is unavailable; use configured local provider",
    }
    assert "credential" not in str(public["fallback"]).lower()


def test_managed_relay_requires_server_side_credential_and_redacts_clients():
    from fastapi.testclient import TestClient
    from orville_core.relay_server import RelayServiceError, create_relay_app

    with pytest.raises(RelayServiceError, match="BLACKBOX_API_KEY"):
        create_relay_app(client_token="client-token")
    app = create_relay_app(blackbox_api_key="server-only-key", client_token="client-token")
    health = TestClient(app).get("/health")
    assert health.status_code == 200
    assert health.json() == {
        "ok": True,
        "status": "ready",
        "provider": "blackbox",
        "credential_configured": False,
        "managed_relay": True,
    }
    assert "server-only-key" not in health.text


def test_pre_execution_summary_reports_supported_and_unsupported_capabilities():
    from orville_core.cloud_relay import AccessMode, AccessRecord, CloudRelayBoundary, RelayConfig, RelayRequest, RelayStatus

    boundary = CloudRelayBoundary(RelayConfig("https://relay.example.test"))
    boundary.set_access(AccessRecord(mode=AccessMode.MANAGED, status=RelayStatus.READY, subject="subject-1"))
    summary = boundary.admit(RelayRequest(subject="subject-1"))
    assert "text" in summary["supported_capabilities"]
    assert "structured_output" in summary["supported_capabilities"]
    assert "image_generation" in summary["unsupported_capabilities"]
    assert set(summary["supported_capabilities"]).isdisjoint(summary["unsupported_capabilities"])


def test_managed_relay_contract_exposes_limits_terms_and_tenant_authorization():
    config = RelayConfig("https://relay.example.test", allowed_hosts=frozenset({"relay.example.test"}))
    public = config.redacted()
    assert public["service_limits"]["managed_units"] == 100
    assert public["privacy_terms_url"].startswith("https://")
    assert public["tenant_authorization_required"] is True
