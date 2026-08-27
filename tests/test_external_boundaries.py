import io
from urllib.error import HTTPError
from unittest.mock import patch

import pytest

from orville_core.cloud_relay import AccessMode, AccessRecord, CloudRelayBoundary, RelayConfig, RelayRequest, RelayStatus
from orville_core.providers import JsonHttpClient, ProviderError


class _Response:
    def __init__(self, payload: bytes):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.payload


def test_json_http_client_external_success_boundary_is_json_and_credential_free():
    with patch("orville_core.providers.urlopen", return_value=_Response(b'{"ok": true}')) as opened:
        result = JsonHttpClient().request("GET", "https://relay.example.test/health")
    assert result == {"ok": True}
    assert opened.call_args.kwargs["timeout"] == 60.0


def test_json_http_client_external_error_boundary_is_actionable_and_redacted():
    error = HTTPError("https://relay.example.test", 401, "unauthorized", {}, io.BytesIO(b"Bearer sk-live-secret123"))
    with patch("orville_core.providers.urlopen", side_effect=error):
        with pytest.raises(ProviderError) as raised:
            JsonHttpClient().request("GET", "https://relay.example.test/health")
    assert raised.value.status_code == 401
    assert "check the API key and reconnect" in str(raised.value)
    assert "sk-live-secret123" not in str(raised.value)


def test_managed_relay_external_boundary_requires_ready_tenant_subject():
    boundary = CloudRelayBoundary(RelayConfig("https://relay.example.test"))
    boundary.set_access(AccessRecord(AccessMode.MANAGED, RelayStatus.READY, subject="tenant-1"))
    admitted = boundary.admit(RelayRequest(subject="tenant-1"))
    assert admitted["tenant_authorization_required"] is True
    assert admitted["execution_location"] == "remote"
    with pytest.raises(Exception, match="not_connected"):
        boundary.admit(RelayRequest(subject="unknown-tenant"))



def test_bounded_text_and_identifiers_reject_invalid_input():
    from orville_core.boundary import BoundaryValidationError, validate_bounded_text, validate_identifier
    assert validate_bounded_text("  objective  ", field="objective", max_length=40) == "objective"
    assert validate_identifier("run-01", field="run_id") == "run-01"
    with pytest.raises(BoundaryValidationError):
        validate_bounded_text("", field="objective", max_length=40)
    with pytest.raises(BoundaryValidationError):
        validate_identifier("run id", field="run_id")


def test_external_url_validation_rejects_credentials_and_unapproved_local_hosts():
    from orville_core.boundary import BoundaryValidationError, validate_external_url
    assert validate_external_url("https://example.test/api") == "https://example.test/api"
    with pytest.raises(BoundaryValidationError):
        validate_external_url("https://user:password@example.test/api")
    with pytest.raises(BoundaryValidationError):
        validate_external_url("http://127.0.0.1:8000")
    assert validate_external_url("http://127.0.0.1:8000", allow_local=True) == "http://127.0.0.1:8000"


def test_external_output_projection_is_recursive_bounded_and_secret_safe():
    from orville_core.boundary import sanitize_external_output
    output = sanitize_external_output({
        "token": "secret-value",
        "message": "Bearer abc.def.ghi",
        "path": r"C:\Users\Operator\private.txt",
        "items": list(range(100)),
        "nested": {"api_key": "sk-test-secret-value"},
    })
    assert output["token"] == "[redacted]"
    assert "abc.def.ghi" not in str(output)
    assert output["path"] == "[redacted-local-path]"
    assert len(output["items"]) == 80
    assert output["nested"]["api_key"] == "[redacted]"
