"""In-process ASGI client for the Orville API.

This lets the desktop GUI call the FastAPI application directly, in the same
process, without binding a TCP socket, running uvicorn, or requiring the
operator to configure ORVILLE_API_TOKEN for loopback use.

A token is still generated and enforced internally so the application's auth
contract is unchanged; it simply never needs to come from the environment when
the GUI owns the app instance.

The public entry point is :func:`request`, a synchronous helper safe to call
from GUI worker threads. Each call runs the async ASGI exchange on a fresh
event loop, which is required because tkinter owns the main thread.
"""

from __future__ import annotations

import asyncio
import json
import secrets
from typing import Any

# Resolved lazily so importing this module never pulls in FastAPI/httpx unless
# the in-process path is actually used.
_app: Any = None
_transport: Any = None
_token: str | None = None


def _build() -> tuple[Any, Any, str]:
    """Create the app, an ASGI transport bound to it, and an internal token."""
    import httpx  # local import: optional dependency, only needed on this path

    from .api import create_app

    token = secrets.token_urlsafe(32)
    app = create_app(api_token=token)
    transport = httpx.ASGITransport(app=app)
    return app, transport, token


def ensure_started() -> str:
    """Create the in-process app if needed and return its internal token.

    Idempotent and safe to call from the GUI startup path. Raises if the API
    dependencies (fastapi/httpx) are unavailable, in which case the caller
    should fall back to the HTTP server path.
    """
    global _app, _transport, _token
    if _app is None:
        _app, _transport, _token = _build()
    return _token or ""


def is_running() -> bool:
    """Return True if the in-process app has been created."""
    return _app is not None


def request(
    method: str,
    path: str,
    *,
    payload: dict | None = None,
    timeout: float = 30.0,
) -> tuple[int, bytes]:
    """Perform a request against the in-process app.

    Args:
        method: HTTP method (GET, POST, DELETE, ...).
        path: URL path beginning with '/' (e.g. '/api/v1/health').
        payload: Optional JSON-serialisable body.
        timeout: Reserved for API parity; ASGI calls run to completion.

    Returns:
        A ``(status_code, body_bytes)`` tuple, mirroring what the GUI's HTTP
        helpers previously read off ``urllib`` responses.

    Raises:
        RuntimeError: if the in-process app has not been started.
    """
    if _transport is None or _token is None:
        raise RuntimeError("in-process API app is not started")

    import httpx

    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {
        "Authorization": f"Bearer {_token}",
        "Content-Type": "application/json",
    }

    async def _exchange() -> tuple[int, bytes]:
        req = httpx.Request(
            method,
            f"http://orville.inprocess{path}",
            content=body,
            headers=headers,
        )
        resp = await _transport.handle_async_request(req)
        chunks = [chunk async for chunk in resp.stream]
        return resp.status_code, b"".join(chunks)

    return asyncio.run(_exchange())
