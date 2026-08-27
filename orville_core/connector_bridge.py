"""Safe HTTP bridge for invoking configured Manus-compatible connectors.

The standalone executable never executes connector commands locally and never
stores connector secrets. A separately configured bridge owns connector auth,
OAuth sessions, and provider-specific tool dispatch.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class ConnectorBridgeError(RuntimeError):
    """Raised when a connector bridge cannot complete a request safely."""


_UID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,159}$")
_OPERATION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,119}$")


@dataclass(frozen=True)
class ConnectorBridge:
    """Minimal authenticated client for a user-managed connector bridge."""

    base_url: str
    token: str | None = None
    timeout_seconds: float = 10.0
    max_response_bytes: int = 2_000_000

    @classmethod
    def from_environment(cls) -> "ConnectorBridge | None":
        raw = os.getenv("ORVILLE_CONNECTOR_BRIDGE_URL", "").strip().rstrip("/")
        if not raw:
            return None
        parsed = urlparse(raw)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password or parsed.fragment:
            raise ConnectorBridgeError("ORVILLE_CONNECTOR_BRIDGE_URL must be a credential-free HTTP(S) URL")
        try:
            timeout = min(30.0, max(1.0, float(os.getenv("ORVILLE_CONNECTOR_BRIDGE_TIMEOUT", "10"))))
        except ValueError as exc:
            raise ConnectorBridgeError("ORVILLE_CONNECTOR_BRIDGE_TIMEOUT must be numeric") from exc
        return cls(raw, os.getenv("ORVILLE_CONNECTOR_BRIDGE_TOKEN") or None, timeout)

    @property
    def configured(self) -> bool:
        return bool(self.base_url)

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = {"Accept": "application/json", "User-Agent": "Orville-Connector-Bridge/1"}
        body: bytes | None = None
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(url, data=body, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read(self.max_response_bytes + 1)
        except HTTPError as exc:
            detail = exc.read(512).decode("utf-8", "replace")
            raise ConnectorBridgeError(f"connector bridge returned HTTP {exc.code}: {detail[:240]}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise ConnectorBridgeError(f"connector bridge unavailable: {exc}") from exc
        if len(raw) > self.max_response_bytes:
            raise ConnectorBridgeError("connector bridge response exceeded the safety limit")
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ConnectorBridgeError("connector bridge returned invalid JSON") from exc
        if not isinstance(value, dict):
            raise ConnectorBridgeError("connector bridge response must be a JSON object")
        return value

    def health(self) -> dict[str, Any]:
        result = self._request("GET", "/health")
        return {"ok": bool(result.get("ok", True)), "status": result.get("status", "unknown"), "bridge": self.base_url}

    def invoke(self, connector_uid: str, operation: str, arguments: dict[str, Any], *, run_id: str | None = None) -> dict[str, Any]:
        if not _UID_RE.fullmatch(connector_uid):
            raise ConnectorBridgeError("invalid connector UID")
        if not _OPERATION_RE.fullmatch(operation):
            raise ConnectorBridgeError("invalid connector operation")
        if len(json.dumps(arguments, ensure_ascii=False, default=str)) > 200_000:
            raise ConnectorBridgeError("connector arguments exceed the safety limit")
        return self._request("POST", "/invoke", {"connector_uid": connector_uid, "operation": operation, "arguments": arguments, "run_id": run_id})


def connector_uid_is_valid(value: str) -> bool:
    return bool(_UID_RE.fullmatch(value))
