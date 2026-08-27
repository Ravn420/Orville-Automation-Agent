import pytest

from orville_core import ConnectorAuthPolicy, ConnectorPolicyError


def test_connector_policy_classifies_auth_rate_limit_and_transient_failures():
    policy = ConnectorAuthPolicy("blackbox", "api_key", required_scopes=("chat",), max_retries=2)
    assert policy.classify_failure(401)["category"] == "authentication"
    assert policy.classify_failure(403)["category"] == "authorization"
    assert policy.classify_failure(429)["category"] == "rate_limit"
    assert policy.classify_failure(503)["retryable"] is True


def test_connector_policy_redacts_credential_details_from_errors():
    policy = ConnectorAuthPolicy("blackbox", "api_key")
    result = policy.classify_failure(401, message="invalid bearer token abc")
    assert "abc" not in result["message"]
    assert "redacted" in result["message"]


def test_connector_policy_rejects_invalid_auth_and_retry_configuration():
    with pytest.raises(ConnectorPolicyError, match="authentication"):
        ConnectorAuthPolicy("x", "unknown")
    with pytest.raises(ConnectorPolicyError, match="scopes"):
        ConnectorAuthPolicy("x", "none", required_scopes=("read",))
    with pytest.raises(ConnectorPolicyError, match="HTTP"):
        ConnectorAuthPolicy("x", "oauth", retryable_statuses=(200,))
