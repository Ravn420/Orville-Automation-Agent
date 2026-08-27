"""Safe endpoint validation and health probing with injectable transport."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import URLError
from urllib.request import Request, urlopen
from urllib.parse import urlparse

from .provider_mcp_security import ProviderMcpSecurityError, no_redirect_opener, validate_remote_endpoint


@dataclass(frozen=True)
class EndpointProbeResult:
    endpoint_url: str
    reachable: bool
    status_code: int | None = None
    detail: str = ""

    def redacted(self) -> dict[str, Any]:
        return {"endpoint_url": self.endpoint_url, "reachable": self.reachable, "status_code": self.status_code, "detail": self.detail}


def validate_endpoint_url(endpoint_url: str, *, allowed_hosts: frozenset[str] = frozenset(), allow_private: bool = False, allowed_ports: frozenset[int] | None = None) -> str:
    parsed = urlparse(endpoint_url)
    if parsed.username or parsed.password:
        raise ValueError("endpoint must not contain embedded credentials")
    if parsed.fragment:
        raise ValueError("endpoint must not contain a fragment")
    try:
        return validate_remote_endpoint(endpoint_url, allowed_hosts=allowed_hosts, allow_private=allow_private, allowed_ports=allowed_ports or frozenset({80, 443}))
    except (ProviderMcpSecurityError, ValueError) as exc:
        raise ValueError(str(exc)) from exc


def probe_endpoint(endpoint_url: str, *, timeout_seconds: float = 5.0, transport: Callable[..., Any] | None = None) -> EndpointProbeResult:
    endpoint = validate_endpoint_url(endpoint_url)
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    request = Request(endpoint, method="HEAD")
    opener = transport or no_redirect_opener().open
    try:
        response = opener(request, timeout=timeout_seconds)
        return EndpointProbeResult(endpoint, True, getattr(response, "status", None), "endpoint reachable")
    except (OSError, URLError, TimeoutError) as exc:
        return EndpointProbeResult(endpoint, False, getattr(exc, "code", None), "endpoint unreachable")
