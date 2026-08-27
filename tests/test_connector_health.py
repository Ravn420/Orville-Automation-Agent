import pytest

from orville_core import ConnectorHealth, ConnectorHealthError, ConnectorInventory


def test_connector_health_is_secret_safe_and_inventory_is_deterministic():
    inventory = ConnectorInventory()
    inventory.record(ConnectorHealth("zapier", "Zapier", "enabled", True, authenticated=True, capabilities=("search",), rate_limit_remaining=10, secret_configured=True))
    inventory.record(ConnectorHealth("browser", "Browser", "degraded", True, error_code="timeout", error_message="request timed out"))
    statuses = inventory.redacted()
    assert [item["connector_id"] for item in statuses] == ["browser", "zapier"]
    assert statuses[1]["secret_configured"] is True


def test_connector_health_requires_configuration_inspection_for_unavailable_state():
    with pytest.raises(ConnectorHealthError, match="configuration inspection"):
        ConnectorHealth("x", "X", "unavailable", False)
    health = ConnectorHealth("x", "X", "unavailable", False, configuration_inspected=True, error_code="not_configured")
    assert health.redacted()["configuration_inspected"] is True


def test_connector_health_rejects_inconsistent_or_secret_exposing_state():
    with pytest.raises(ConnectorHealthError, match="enabled status"):
        ConnectorHealth("x", "X", "enabled", False)
    with pytest.raises(ConnectorHealthError, match="credential"):
        ConnectorHealth("x", "X", "degraded", True, error_message="invalid bearer token")
    with pytest.raises(ConnectorHealthError, match="negative"):
        ConnectorHealth("x", "X", "degraded", True, rate_limit_remaining=-1)
