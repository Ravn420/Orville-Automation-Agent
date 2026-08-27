"""Safe capability-call auditing for concrete connector requirements.

The audit never guesses a connector requirement and never invokes write, sensitive,
or critical operations. Callers must provide the concrete project requirement list.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .connector_adapters import AdapterResult, ConnectorAdapterError, ConnectorAdapterRegistry, OperationSpec


@dataclass(frozen=True)
class CapabilityCallResult:
    connector_id: str
    operation_id: str
    invoked: bool
    success: bool
    status_code: int | None
    error: str | None = None


class ConnectorCapabilityAudit:
    """Select and optionally execute one harmless read-only operation per requirement."""

    def __init__(self, registry: ConnectorAdapterRegistry) -> None:
        self.registry = registry

    def select(self, required_connector_ids: list[str] | tuple[str, ...]) -> tuple[tuple[str, OperationSpec], ...]:
        selected: list[tuple[str, OperationSpec]] = []
        for connector_id in required_connector_ids:
            manifest = self.registry.get(connector_id)
            operation = next((item for item in manifest.operations if item.enabled and item.risk_class == "read"), None)
            if operation is None:
                raise ConnectorAdapterError(f"no harmless read-only capability is declared: {connector_id}")
            selected.append((connector_id, operation))
        return tuple(selected)

    def verify(self, required_connector_ids: list[str] | tuple[str, ...], *, invoke: bool = False, arguments: dict[str, Any] | None = None) -> tuple[CapabilityCallResult, ...]:
        results: list[CapabilityCallResult] = []
        for connector_id, operation in self.select(required_connector_ids):
            if not invoke:
                results.append(CapabilityCallResult(connector_id, operation.operation_id, False, True, None, "dry-run: invocation not requested"))
                continue
            result: AdapterResult = self.registry.invoke(connector_id, operation.operation_id, arguments or {}, approved=False)
            results.append(CapabilityCallResult(connector_id, operation.operation_id, True, result.success, result.status_code, result.error))
        return tuple(results)
