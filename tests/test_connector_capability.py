from __future__ import annotations

import pytest

from orville_core.connector_adapters import AdapterResult, ConnectorAdapterError, ConnectorAdapterRegistry, ConnectorManifest, OperationSpec
from orville_core.connector_capability import ConnectorCapabilityAudit


def test_capability_audit_selects_and_invokes_only_read_operation() -> None:
    registry = ConnectorAdapterRegistry()
    calls: list[str] = []

    def handler(operation: OperationSpec, arguments: dict) -> AdapterResult:
        calls.append(operation.operation_id)
        return AdapterResult(True, 200, {"ok": True})

    registry.register(ConnectorManifest("fixture", "Fixture", "none", "", (OperationSpec("health", "Health", risk_class="read"), OperationSpec("write", "Write", risk_class="write")), True), handler)
    audit = ConnectorCapabilityAudit(registry)
    dry_run = audit.verify(["fixture"])
    assert dry_run[0].success is True
    assert dry_run[0].invoked is False
    assert calls == []
    result = audit.verify(["fixture"], invoke=True)
    assert result[0].success is True
    assert result[0].invoked is True
    assert calls == ["health"]


def test_capability_audit_rejects_connector_without_harmless_operation() -> None:
    registry = ConnectorAdapterRegistry()
    registry.register(ConnectorManifest("sensitive-only", "Sensitive", "none", "", (OperationSpec("delete", "Delete", risk_class="critical"),), True))
    with pytest.raises(ConnectorAdapterError, match="read-only"):
        ConnectorCapabilityAudit(registry).select(["sensitive-only"])
