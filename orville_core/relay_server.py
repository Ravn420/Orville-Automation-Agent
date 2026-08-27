"""Minimal deployable Orville-managed Blackbox cloud relay.

The relay is intentionally separate from the desktop API. It owns the
BLACKBOX_API_KEY environment variable and exposes only an authenticated,
provider-neutral OpenAI-compatible surface to Orville clients.
"""
from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from threading import Lock
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlparse
import json

try:
    from fastapi import FastAPI, Header, HTTPException
except ImportError:  # pragma: no cover
    FastAPI = None


class RelayServiceError(RuntimeError):
    """Raised for safe relay configuration or upstream failures."""


def create_relay_app(*, blackbox_base_url: str | None = None, blackbox_api_key: str | None = None, client_token: str | None = None, requests_per_minute: int = 60) -> Any:
    if FastAPI is None:
        raise RuntimeError("FastAPI is required for the relay service")
    upstream = (blackbox_base_url or os.getenv("BLACKBOX_BASE_URL", "https://api.blackbox.ai")).rstrip("/")
    parsed_upstream = urlparse(upstream)
    if parsed_upstream.scheme != "https" or not parsed_upstream.hostname or parsed_upstream.username or parsed_upstream.password or parsed_upstream.fragment:
        raise RelayServiceError("BLACKBOX_BASE_URL must be a credential-free HTTPS URL")
    provider_key = blackbox_api_key or os.getenv("BLACKBOX_API_KEY")
    expected_client_token = client_token or os.getenv("ORVILLE_RELAY_CLIENT_TOKEN")
    if not provider_key:
        raise RelayServiceError("BLACKBOX_API_KEY must be configured on the relay server")
    if not expected_client_token:
        raise RelayServiceError("ORVILLE_RELAY_CLIENT_TOKEN must be configured on the relay server")
    if requests_per_minute < 1:
        raise ValueError("requests_per_minute must be positive")

    app = FastAPI(title="Orville Blackbox Relay", version="0.1.0")
    buckets: dict[str, deque[float]] = defaultdict(deque)
    lock = Lock()

    def authenticate(authorization: str | None, x_orville_session: str | None) -> str:
        supplied = x_orville_session or (authorization.removeprefix("Bearer ") if authorization else "")
        if supplied != expected_client_token:
            raise HTTPException(status_code=401, detail="invalid Orville relay session")
        now = time.monotonic()
        with lock:
            bucket = buckets[supplied]
            while bucket and now - bucket[0] >= 60:
                bucket.popleft()
            if len(bucket) >= requests_per_minute:
                raise HTTPException(status_code=429, detail="Orville relay rate limit exceeded")
            bucket.append(now)
        return supplied

    def upstream_request(path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(f"{upstream}/{path.lstrip('/')}", data=body, method="POST" if payload is not None else "GET", headers={"Accept": "application/json", "Authorization": f"Bearer {provider_key}", "User-Agent": "Orville-Blackbox-Relay/0.1"})
        if payload is not None:
            request.add_header("Content-Type", "application/json")
        try:
            with urlopen(request, timeout=90) as response:
                raw = response.read(10_000_001)
        except HTTPError as exc:
            detail = exc.read(1_000_001).decode("utf-8", errors="replace")
            raise HTTPException(status_code=502, detail=f"Blackbox upstream HTTP {exc.code}: {detail[:400]}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise HTTPException(status_code=502, detail=f"Blackbox upstream unavailable: {type(exc).__name__}") from exc
        try:
            return json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=502, detail="Blackbox upstream returned invalid JSON") from exc

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {"ok": True, "status": "ready", "provider": "blackbox", "credential_configured": False, "managed_relay": True}

    @app.get("/v1/models")
    def models(authorization: str | None = Header(default=None), x_orville_session: str | None = Header(default=None)) -> dict[str, Any]:
        authenticate(authorization, x_orville_session)
        return upstream_request("models")

    @app.post("/v1/chat/completions")
    def chat_completions(payload: dict[str, Any], authorization: str | None = Header(default=None), x_orville_session: str | None = Header(default=None)) -> dict[str, Any]:
        authenticate(authorization, x_orville_session)
        if not isinstance(payload.get("messages"), list) or not payload["messages"]:
            raise HTTPException(status_code=400, detail="messages must be a non-empty list")
        payload = dict(payload)
        payload["stream"] = False
        return upstream_request("chat/completions", payload)

    return app
