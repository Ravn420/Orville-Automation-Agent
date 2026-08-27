from __future__ import annotations

import pytest

from orville_core.blackbox_contract import BlackboxApiKeyContract, BlackboxContractError, validate_blackbox_error_payload


def test_public_and_enterprise_endpoint_families_validate_without_network_calls():
    public = BlackboxApiKeyContract().validate()
    enterprise = BlackboxApiKeyContract(base_url="https://enterprise.blackbox.ai", model="blackboxai/openai/gpt-5.5").validate()
    assert public == "https://api.blackbox.ai"
    assert enterprise == "https://enterprise.blackbox.ai"
    assert BlackboxApiKeyContract(base_url="https://enterprise.blackbox.ai").public()["endpoint_family"] == "enterprise"


@pytest.mark.parametrize("url", ["http://api.blackbox.ai", "https://user:pass@api.blackbox.ai", "https://example.test", "https://api.blackbox.ai/#fragment"])
def test_blackbox_contract_rejects_unsafe_or_undocumented_endpoint(url: str):
    with pytest.raises(BlackboxContractError):
        BlackboxApiKeyContract(base_url=url).validate()


def test_blackbox_error_envelope_is_normalized_without_retaining_body():
    assert validate_blackbox_error_payload({"error": {"code": "rate_limit_exceeded", "message": "secret response"}}) == "rate_limit_exceeded"
    assert validate_blackbox_error_payload({"error": "unauthorized"}) == "provider_error"
    with pytest.raises(BlackboxContractError, match="error envelope"):
        validate_blackbox_error_payload({"message": "not an error envelope"})
