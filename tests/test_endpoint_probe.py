from urllib.error import URLError

import pytest

from orville_core import probe_endpoint, validate_endpoint_url


def test_endpoint_probe_validates_urls_without_embedded_credentials():
    assert validate_endpoint_url("https://example.test/v1") == "https://example.test/v1"
    with pytest.raises(ValueError, match="credentials"):
        validate_endpoint_url("https://user:pass@example.test/v1")
    with pytest.raises(ValueError, match="fragment"):
        validate_endpoint_url("https://example.test/v1#fragment")


def test_endpoint_probe_uses_injectable_transport_and_redacts_failure_details():
    def transport(request, timeout):
        assert request.get_method() == "HEAD"
        assert timeout == 2
        return type("Response", (), {"status": 204})()

    result = probe_endpoint("https://example.test/v1", timeout_seconds=2, transport=transport)
    assert result.reachable is True
    assert result.status_code == 204

    def failing_transport(request, timeout):
        raise URLError("secret bearer token should not be returned")

    failed = probe_endpoint("https://example.test/v1", transport=failing_transport)
    assert failed.reachable is False
    assert "bearer" not in failed.detail.lower()
