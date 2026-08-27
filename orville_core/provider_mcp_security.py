from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import os
import secrets
import time
from dataclasses import dataclass, field
from typing import Any, Callable
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, build_opener

from .security import SecretRedactor, SecurityViolation


PROMPT_BOUNDARY_START = "[BEGIN UNTRUSTED CONTENT]"
PROMPT_BOUNDARY_END = "[END UNTRUSTED CONTENT]"
OUTPUT_BOUNDARY_START = "[BEGIN TOOL OUTPUT]"
OUTPUT_BOUNDARY_END = "[END TOOL OUTPUT]"
DEFAULT_ALLOWED_PORTS = frozenset({80, 443})


class ProviderMcpSecurityError(SecurityViolation):
    """Raised when a provider or MCP security boundary is violated."""


@dataclass(frozen=True)
class InvocationSecurityContext:
    """Least-privilege binding for one provider/MCP invocation."""

    user_id: str = "local"
    task_id: str | None = None
    provider_id: str | None = None
    credential_reference: str | None = None
    scopes: frozenset[str] = frozenset()
    allowed_tools: frozenset[str] = frozenset()
    allowed_hosts: frozenset[str] = frozenset()
    filesystem_roots: tuple[str, ...] = ()
    dry_run: bool = True
    approved: bool = False
    approval_reference: str | None = None

    def __post_init__(self) -> None:
        if not self.user_id.strip() or len(self.user_id) > 200:
            raise ProviderMcpSecurityError("security context requires a bounded user ID")
        if self.task_id is not None and (not self.task_id.strip() or len(self.task_id) > 200):
            raise ProviderMcpSecurityError("security context task ID is invalid")
        if self.provider_id is not None and (not self.provider_id.strip() or len(self.provider_id) > 200):
            raise ProviderMcpSecurityError("security context provider ID is invalid")
        if self.approved and not self.approval_reference:
            raise ProviderMcpSecurityError("approved external actions require an approval reference")

    def check_tool(self, tool_name: str) -> None:
        if tool_name not in self.allowed_tools:
            raise ProviderMcpSecurityError(f"tool is not allowlisted: {tool_name}")

    def require_external_action(self, tool_name: str) -> None:
        self.check_tool(tool_name)
        if self.dry_run:
            raise ProviderMcpSecurityError("external side effects are disabled in dry-run mode")
        if not self.approved:
            raise ProviderMcpSecurityError("external action requires explicit approval")

    def check_provider(self, provider_id: str, required_scopes: set[str] | frozenset[str] = frozenset()) -> None:
        if self.provider_id != provider_id:
            raise ProviderMcpSecurityError("provider does not match the invocation security context")
        missing = set(required_scopes) - set(self.scopes)
        if missing:
            raise ProviderMcpSecurityError(f"provider scopes are insufficient: {sorted(missing)}")


def mark_untrusted_content(value: str, *, source: str = "retrieved data") -> str:
    """Make retrieved/provider text visibly distinct from executable instructions."""
    if not isinstance(value, str):
        raise ProviderMcpSecurityError("untrusted content must be text")
    safe_source = " ".join(source.split())[:80] or "retrieved data"
    return f"{PROMPT_BOUNDARY_START}\nSOURCE: {safe_source}\n{value}\n{PROMPT_BOUNDARY_END}"


def reject_credential_values(value: Any) -> None:
    """Reject credential-shaped fields from untrusted tool arguments."""
    if isinstance(value, dict):
        for key, item in value.items():
            if any(marker in str(key).lower() for marker in ("token", "secret", "password", "api_key", "authorization", "credential")):
                raise ProviderMcpSecurityError("credential values must remain in the protected connector store")
            reject_credential_values(item)
    elif isinstance(value, list):
        for item in value:
            reject_credential_values(item)


def mark_tool_output(value: Any, *, tool_name: str) -> dict[str, Any]:
    """Return tool results as typed, explicitly bounded output rather than instructions."""
    return {
        "type": "tool_output",
        "tool": tool_name,
        "boundary": {"start": OUTPUT_BOUNDARY_START, "end": OUTPUT_BOUNDARY_END},
        "untrusted": True,
        "data": SecretRedactor.redact(value),
    }


def safe_authorization_record(*, outcome: str, action: str, context: InvocationSecurityContext, reason: str | None = None) -> dict[str, Any]:
    """Create a secret-free decision record suitable for audit storage."""
    result: dict[str, Any] = {
        "outcome": outcome,
        "action": action,
        "user_id": context.user_id,
        "task_id": context.task_id,
        "provider_id": context.provider_id,
        "credential_reference": context.credential_reference,
        "approval_reference": context.approval_reference,
        "dry_run": context.dry_run,
        "approved": context.approved,
    }
    if reason:
        result["reason"] = SecretRedactor.redact(str(reason))[:500]
    return result


def _host_is_private(host: str) -> bool:
    normalized = host.strip("[]").lower().rstrip(".")
    if normalized in {"localhost", "localhost.localdomain", "0.0.0.0"}:
        return True
    try:
        address = ipaddress.ip_address(normalized)
    except ValueError:
        return False
    return address.is_private or address.is_loopback or address.is_link_local or address.is_reserved or address.is_multicast


def validate_remote_endpoint(value: str, *, allowed_hosts: frozenset[str] = frozenset(), allow_private: bool = False, allowed_ports: frozenset[int] = DEFAULT_ALLOWED_PORTS) -> str:
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise ProviderMcpSecurityError("remote endpoint must be credential-free HTTP(S) with a hostname and no fragment")
    host = parsed.hostname.lower().rstrip(".")
    if not allow_private and _host_is_private(host):
        raise ProviderMcpSecurityError("private or local remote endpoint is not allowed")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if port not in allowed_ports:
        raise ProviderMcpSecurityError("remote endpoint port is not allowlisted")
    if allowed_hosts and host not in {item.lower().rstrip(".") for item in allowed_hosts}:
        raise ProviderMcpSecurityError("remote endpoint host is not allowlisted")
    return value.strip().rstrip("/")


class NoRedirectHandler(HTTPRedirectHandler):
    """Prevent urllib from silently changing the validated authorization target."""

    def redirect_request(self, request, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        raise ProviderMcpSecurityError("redirects are not allowed for provider authorization or token requests")


def no_redirect_opener():
    return build_opener(NoRedirectHandler)


@dataclass
class McpStateHandleStore:
    """Single-use, signed MCP/OAuth state handles bound to a user/task/provider."""

    secret: bytes
    ttl_seconds: int = 600
    _consumed: set[str] = field(default_factory=set)

    @classmethod
    def from_environment(cls) -> "McpStateHandleStore":
        raw = os.getenv("ORVILLE_MCP_STATE_SECRET", "")
        if not raw:
            raise ProviderMcpSecurityError("ORVILLE_MCP_STATE_SECRET is required for MCP state handles")
        return cls(hashlib.sha256(raw.encode("utf-8")).digest())

    def issue(self, *, user_id: str, task_id: str | None, provider_id: str | None) -> str:
        nonce = secrets.token_urlsafe(32)
        payload = {"nonce": nonce, "user_id": user_id, "task_id": task_id, "provider_id": provider_id, "exp": int(time.time()) + self.ttl_seconds}
        encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        signature = hmac.new(self.secret, encoded, hashlib.sha256).hexdigest()
        return secrets.token_urlsafe(8) + "." + encoded.hex() + "." + signature

    def consume(self, handle: str, *, user_id: str, task_id: str | None, provider_id: str | None) -> dict[str, Any]:
        try:
            _prefix, encoded_hex, signature = handle.split(".", 2)
            encoded = bytes.fromhex(encoded_hex)
            payload = json.loads(encoded.decode("utf-8"))
        except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProviderMcpSecurityError("MCP state handle is malformed") from exc
        expected = hmac.new(self.secret, encoded, hashlib.sha256).hexdigest()
        nonce = str(payload.get("nonce", ""))
        if not nonce or not hmac.compare_digest(expected, signature):
            raise ProviderMcpSecurityError("MCP state handle signature validation failed")
        if nonce in self._consumed:
            raise ProviderMcpSecurityError("MCP state handle was already consumed")
        if int(payload.get("exp", 0)) < int(time.time()):
            raise ProviderMcpSecurityError("MCP state handle expired")
        if payload.get("user_id") != user_id or payload.get("task_id") != task_id or payload.get("provider_id") != provider_id:
            raise ProviderMcpSecurityError("MCP state handle context mismatch")
        self._consumed.add(nonce)
        return payload
