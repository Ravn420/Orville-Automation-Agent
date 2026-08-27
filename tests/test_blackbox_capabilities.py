from __future__ import annotations

import pytest

from orville_core.blackbox_capabilities import BlackboxCapabilityError, BlackboxCapabilityNegotiator


def test_standard_endpoint_exposes_only_advertised_basic_capabilities():
    result = BlackboxCapabilityNegotiator().negotiate(
        base_url="https://api.blackbox.ai",
        model="blackboxai/openai/gpt-5.5",
        account_plan="free",
        advertised={"chat", "streaming", "tool_calling", "agent_tasks"},
    )
    assert result.supported == {"chat", "streaming", "tool_calling"}
    assert "agent_tasks" in result.unavailable_reasons
    assert result.public()["credential_configured"] is False


def test_enterprise_endpoint_and_plan_can_expose_agent_capabilities():
    result = BlackboxCapabilityNegotiator().negotiate(
        base_url="https://enterprise.blackbox.ai",
        model="blackboxai/openai/gpt-5.5",
        account_plan="enterprise",
        advertised={"chat", "agent_tasks", "github_operations", "remote_task_resumption", "embeddings"},
    )
    assert result.supported == {"chat", "agent_tasks", "github_operations", "remote_task_resumption", "embeddings"}
    assert result.endpoint_family == "enterprise"


@pytest.mark.parametrize("base_url", ["http://api.blackbox.ai", "https://example.test", "https://user:pass@api.blackbox.ai"])
def test_negotiation_rejects_undocumented_endpoint_families(base_url: str):
    with pytest.raises(BlackboxCapabilityError):
        BlackboxCapabilityNegotiator().negotiate(base_url=base_url, model="model", advertised={"chat"})


def test_negotiation_rejects_unknown_capability():
    with pytest.raises(BlackboxCapabilityError, match="unknown"):
        BlackboxCapabilityNegotiator().negotiate(base_url="https://api.blackbox.ai", model="model", advertised={"chat", "future_capability"})


def test_api_exposes_negotiated_capabilities_without_credentials(tmp_path):
    from fastapi.testclient import TestClient
    from orville_core.api import create_app

    client = TestClient(create_app(checkpoint_dir=tmp_path, api_token="test-token"))
    response = client.post(
        "/api/v1/cloud/blackbox/capabilities",
        headers={"Authorization": "Bearer test-token"},
        json={"base_url": "https://api.blackbox.ai", "model": "blackboxai/openai/gpt-5.5", "account_plan": "free", "advertised": ["chat", "streaming", "agent_tasks"]},
    )
    assert response.status_code == 200
    body = response.json()["capabilities"]
    assert body["supported"] == ["chat", "streaming"]
    assert body["credential_configured"] is False
