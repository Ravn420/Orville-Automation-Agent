"""Secret-safe connector inventory and health contracts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class ConnectorHealthError(ValueError):
    pass


@dataclass(frozen=True)
class ConnectorHealth:
    connector_id: str
    display_name: str
    status: str
    enabled: bool
    authenticated: bool = False
    capabilities: tuple[str, ...] = ()
    rate_limit_remaining: int | None = None
    last_checked_at: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    secret_configured: bool = False
    configuration_inspected: bool = False

    def __post_init__(self) -> None:
        if not self.connector_id.strip() or not self.display_name.strip():
            raise ConnectorHealthError("connector identity must be non-empty")
        if self.status not in {"enabled", "disabled", "degraded", "unavailable", "unknown"}:
            raise ConnectorHealthError("unsupported connector status")
        if self.status == "enabled" and not self.enabled:
            raise ConnectorHealthError("enabled status requires enabled=True")
        if self.status == "unavailable" and not self.configuration_inspected:
            raise ConnectorHealthError("unavailable status requires configuration inspection")
        if self.rate_limit_remaining is not None and self.rate_limit_remaining < 0:
            raise ConnectorHealthError("rate_limit_remaining cannot be negative")
        if self.error_message and any(secret in self.error_message.lower() for secret in ("api key", "authorization", "bearer", "password", "token")):
            raise ConnectorHealthError("connector error message must not expose credential details")

    def redacted(self) -> dict[str, Any]:
        return {
            "connector_id": self.connector_id,
            "display_name": self.display_name,
            "status": self.status,
            "enabled": self.enabled,
            "authenticated": self.authenticated,
            "capabilities": list(self.capabilities),
            "rate_limit_remaining": self.rate_limit_remaining,
            "last_checked_at": self.last_checked_at,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "secret_configured": self.secret_configured,
            "configuration_inspected": self.configuration_inspected,
        }


@dataclass
class ConnectorInventory:
    connectors: dict[str, ConnectorHealth] = field(default_factory=dict)

    def record(self, health: ConnectorHealth) -> None:
        self.connectors[health.connector_id] = health

    def get(self, connector_id: str) -> ConnectorHealth:
        try:
            return self.connectors[connector_id]
        except KeyError as exc:
            raise ConnectorHealthError(f"connector not found: {connector_id}") from exc

    def redacted(self) -> list[dict[str, Any]]:
        return [self.connectors[key].redacted() for key in sorted(self.connectors)]
