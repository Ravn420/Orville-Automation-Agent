"""Safe endpoint validation and health probing with injectable transport."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import URLError
from urllib.request import Request, urlopen
from urllib.parse import urlparse


@dataclass(frozen=True)
class EndpointProbeResult:
    endpoint_url: str
    reachable: bool
    status_code: int | None = None
    detail: str = ""

    def redacted(self) -> dict[str, Any]:
        return {"endpoint_url": self.endpoint_url, "reachable": self.reachable, "status_code": self.status_code, "detail": self.detail}


def validate_endpoint_url(endpoint_url: str) -> str:
    parsed = urlparse(endpoint_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.fragment:
        raise ValueError("endpoint must be an HTTP(S) URL with a host and no fragment")
    if parsed.username or parsed.password:
        raise ValueError("endpoint must not contain embedded credentials")
    return endpoint_url.rstrip("/")


def probe_endpoint(endpoint_url: str, *, timeout_seconds: float = 5.0, transport: Callable[..., Any] | None = None) -> EndpointProbeResult:
    endpoint = validate_endpoint_url(endpoint_url)
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    request = Request(endpoint, method="HEAD")
    opener = transport or urlopen
    try:
        response = opener(request, timeout=timeout_seconds)
        return EndpointProbeResult(endpoint, True, getattr(response, "status", None), "endpoint reachable")
    except (OSError, URLError, TimeoutError) as exc:
        return EndpointProbeResult(endpoint, False, getattr(exc, "code", None), "endpoint unreachable")
