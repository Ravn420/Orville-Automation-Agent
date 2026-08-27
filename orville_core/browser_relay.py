"""Fail-closed local Browser Operator relay policy.

This module does not store passwords or cookies and does not implement Cloud
Browser. It authenticates an explicitly paired browser extension, validates
allowed domains, and dispatches only approved action types to a local browser
adapter supplied by the caller.
"""
from __future__ import annotations
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse
from typing import Any, Callable

@dataclass(frozen=True)
class RelaySession:
    session_id: str
    client_label: str
    allowed_domains: tuple[str, ...]
    expires_at: str
    active: bool = True

class BrowserRelayError(PermissionError):
    pass

class LocalBrowserRelay:
    def __init__(self, *, ttl_seconds: int = 900, max_sessions: int = 8) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_sessions = max_sessions
        self._sessions: dict[str, tuple[RelaySession, str]] = {}
        self._queues: dict[str, list[dict[str, Any]]] = {}

    @staticmethod
    def _domain_allowed(host: str, domains: tuple[str, ...]) -> bool:
        host = host.lower().rstrip(".")
        return any(host == domain or host.endswith("." + domain) for domain in domains)

    def pair(self, client_label: str, allowed_domains: list[str] | tuple[str, ...]) -> tuple[RelaySession, str]:
        if len(self._sessions) >= self.max_sessions:
            raise BrowserRelayError("browser relay session limit reached")
        domains = tuple(sorted({item.strip().lower().rstrip(".") for item in allowed_domains if item.strip()}))
        if not domains or any("/" in item or ":" in item for item in domains):
            raise BrowserRelayError("allowed domains must contain hostnames only")
        session_id = "relay-" + secrets.token_urlsafe(12)
        secret = secrets.token_urlsafe(32)
        session = RelaySession(session_id, client_label[:120], domains, (datetime.now(UTC) + timedelta(seconds=self.ttl_seconds)).isoformat())
        self._sessions[session_id] = (session, hashlib.sha256(secret.encode()).hexdigest())
        return session, secret

    def _authorize(self, session_id: str, secret: str) -> RelaySession:
        try:
            session, secret_hash = self._sessions[session_id]
        except KeyError as exc:
            raise BrowserRelayError("browser relay session not found") from exc
        if not session.active or datetime.fromisoformat(session.expires_at) <= datetime.now(UTC):
            raise BrowserRelayError("browser relay session expired or inactive")
        if not hmac.compare_digest(secret_hash, hashlib.sha256(secret.encode()).hexdigest()):
            raise BrowserRelayError("invalid browser relay secret")
        return session

    def validate_navigation(self, session_id: str, secret: str, url: str) -> RelaySession:
        session = self._authorize(session_id, secret)
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or not self._domain_allowed(parsed.hostname, session.allowed_domains):
            raise BrowserRelayError("browser URL is outside the session allowlist")
        return session

    def dispatch(self, session_id: str, secret: str, action: str, payload: dict[str, Any], handler: Callable[[str, dict[str, Any]], Any]) -> Any:
        session = self._authorize(session_id, secret)
        if action not in {"navigate", "extract", "screenshot", "takeover_request", "release"}:
            raise BrowserRelayError("browser action is not allowlisted")
        if action == "navigate":
            self.validate_navigation(session_id, secret, str(payload.get("url", "")))
        if action in {"takeover_request", "release"} and not bool(payload.get("approved", False)):
            raise BrowserRelayError("browser takeover actions require explicit approval")
        return handler(action, dict(payload))

    def queue_action(self, session_id: str, secret: str, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        session = self._authorize(session_id, secret)
        if action not in {"navigate", "extract", "screenshot", "takeover_request", "release"}:
            raise BrowserRelayError("browser action is not allowlisted")
        if action == "navigate":
            self.validate_navigation(session_id, secret, str(payload.get("url", "")))
        if action in {"takeover_request", "release"} and not bool(payload.get("approved", False)):
            raise BrowserRelayError("browser takeover actions require explicit approval")
        item = {"action_id": secrets.token_urlsafe(10), "action": action, "payload": dict(payload), "session_id": session.session_id}
        self._queues.setdefault(session.session_id, []).append(item)
        return item

    def poll_actions(self, session_id: str, secret: str, *, limit: int = 20) -> list[dict[str, Any]]:
        self._authorize(session_id, secret)
        queue = self._queues.setdefault(session_id, [])
        items, self._queues[session_id] = queue[:max(1, min(limit, 100))], queue[max(1, min(limit, 100)):]
        return items

    def revoke(self, session_id: str, secret: str) -> RelaySession:
        session = self._authorize(session_id, secret)
        revoked = RelaySession(session.session_id, session.client_label, session.allowed_domains, session.expires_at, False)
        self._sessions[session_id] = (revoked, self._sessions[session_id][1])
        return revoked

    def list_sessions(self) -> tuple[RelaySession, ...]:
        return tuple(item[0] for item in self._sessions.values())
