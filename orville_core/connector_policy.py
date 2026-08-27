"""Provider-neutral connector authentication and failure policy."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ConnectorPolicyError(ValueError):
    pass


@dataclass(frozen=True)
class ConnectorAuthPolicy:
    connector_id: str
    auth_method: str
    required_scopes: tuple[str, ...] = ()
    max_retries: int = 0
    retryable_statuses: tuple[int, ...] = (408, 409, 429, 500, 502, 503, 504)
    timeout_seconds: float = 30.0
    approval_required: bool = False

    def __post_init__(self) -> None:
        if not self.connector_id.strip():
            raise ConnectorPolicyError("connector_id must be non-empty")
        if self.auth_method not in {"none", "api_key", "oauth", "device_code", "session"}:
            raise ConnectorPolicyError("unsupported connector authentication method")
        if self.max_retries < 0 or self.timeout_seconds <= 0:
            raise ConnectorPolicyError("retry and timeout limits are invalid")
        if any(status < 400 or status > 599 for status in self.retryable_statuses):
            raise ConnectorPolicyError("retryable statuses must be HTTP error statuses")
        if self.auth_method == "none" and self.required_scopes:
            raise ConnectorPolicyError("unauthenticated connectors cannot require scopes")

    def classify_failure(self, status_code: int | None, *, message: str = "") -> dict[str, Any]:
        if status_code in {401, 403}:
            category = "authentication" if status_code == 401 else "authorization"
            action = "Reconnect the connector or grant the required scopes."
        elif status_code == 429:
            category, action = "rate_limit", "Wait for the retry window or reduce request frequency."
        elif status_code is not None and status_code in self.retryable_statuses:
            category, action = "transient", "Retry with bounded backoff."
        elif status_code is not None and status_code >= 400:
            category, action = "provider", "Inspect the connector configuration and provider response."
        else:
            category, action = "transport", "Check endpoint reachability and connector health."
        safe_message = message
        lowered = safe_message.lower()
        if any(secret in lowered for secret in ("api key", "authorization", "bearer", "password", "token")):
            safe_message = "Provider returned a credential-related error; raw details were redacted."
        return {"category": category, "status_code": status_code, "action": action, "message": safe_message, "retryable": status_code in self.retryable_statuses}

    def to_dict(self) -> dict[str, Any]:
        return {"connector_id": self.connector_id, "auth_method": self.auth_method, "required_scopes": list(self.required_scopes), "max_retries": self.max_retries, "retryable_statuses": list(self.retryable_statuses), "timeout_seconds": self.timeout_seconds, "approval_required": self.approval_required}
