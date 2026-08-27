from __future__ import annotations

import pytest

from orville_core.blackbox_model_discovery import BlackboxModelDiscovery, BlackboxModelDiscoveryError


def test_discovery_normalizes_models_and_selects_active_model() -> None:
    result = BlackboxModelDiscovery().discover(
        base_url="https://api.blackbox.ai/",
        model="missing-model",
        response_payload={"data": [{"id": "alpha"}, {"id": "alpha"}, {"id": "beta"}]},
    )
    assert result.models == ("alpha", "beta")
    assert result.active_model == "alpha"
    assert result.discovery_supported is True
    assert result.public()["credential_returned"] is False


def test_discovery_falls_back_to_manual_model_when_endpoint_has_no_discovery() -> None:
    result = BlackboxModelDiscovery().discover(
        base_url="https://enterprise.blackbox.ai",
        model="tenant-model",
        discovery_supported=False,
    )
    assert result.status == "manual_required"
    assert result.models == ("tenant-model",)
    assert result.manual_model_entry is True
    assert "manual model entry" in (result.reason or "")


def test_empty_or_malformed_catalog_uses_manual_fallback() -> None:
    result = BlackboxModelDiscovery().discover(
        base_url="https://api.blackbox.ai",
        model="manual-model",
        response_payload={"data": [{"name": "not-an-id"}]},
    )
    assert result.status == "manual_required"
    assert result.active_model == "manual-model"


def test_discovery_rejects_credentials_in_endpoint() -> None:
    with pytest.raises(BlackboxModelDiscoveryError):
        BlackboxModelDiscovery().discover(
            base_url="https://user:pass@api.blackbox.ai",
            model="manual-model",
            discovery_supported=False,
        )
