"""Cloud relay contracts for managed and user-connected Blackbox access.

This module deliberately contains no provider secret.  The managed Blackbox
credential belongs on the relay server, while a desktop client receives only a
short-lived Orville session token or a redacted status response.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import monotonic
from typing import Any, Mapping
from urllib.parse import urlparse


class RelayError(RuntimeError):
    """Raised when a relay request cannot be admitted safely."""


class AccessMode(str, Enum):
    MANAGED = "managed"
    USER_CONNECTED = "user_connected"


class RelayStatus(str, Enum):
    READY = "ready"
    NOT_CONNECTED = "not_connected"
    CONNECTING = "connecting"
    EXPIRED = "expired"
    INVALID = "invalid"
    RATE_LIMITED = "rate_limited"
    UNAVAILABLE = "unavailable"
    DISABLED = "disabled"


@dataclass(frozen=True)
class RelayConfig:
    """Public relay configuration; never place provider credentials here."""

    relay_url: str
    provider: str = "blackbox"
    model: str = "blackboxai/openai/gpt-5.5"
    timeout_seconds: float = 60.0
    allowed_hosts: frozenset[str] = field(default_factory=frozenset)
    supported_capabilities: tuple[str, ...] = ("text", "code", "streaming", "structured_output", "tool_calling")
    unsupported_capabilities: tuple[str, ...] = ("image_generation", "video_generation", "audio_generation")
    service_limits: Mapping[str, int] = field(default_factory=lambda: {"managed_units": 100, "user_connected_units": 1000})
    privacy_terms_url: str = "https://www.blackbox.ai/terms-of-service"
    tenant_authorization_required: bool = True

    def __post_init__(self) -> None:
        parsed = urlparse(self.relay_url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("relay_url must be an HTTPS URL with a hostname")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.allowed_hosts and parsed.hostname.lower() not in {host.lower() for host in self.allowed_hosts}:
            raise ValueError("relay_url host is not allowlisted")
        if set(self.supported_capabilities) & set(self.unsupported_capabilities):
            raise ValueError("a capability cannot be both supported and unsupported")
        if any(int(limit) < 0 for limit in self.service_limits.values()):
            raise ValueError("service limits must not be negative")
        terms = urlparse(self.privacy_terms_url)
        if terms.scheme != "https" or not terms.hostname:
            raise ValueError("privacy_terms_url must be HTTPS")

    def redacted(self) -> dict[str, Any]:
        return {
            "relay_url": self.relay_url,
            "provider": self.provider,
            "model": self.model,
            "timeout_seconds": self.timeout_seconds,
            "credential_configured": False,
            "supported_capabilities": list(self.supported_capabilities),
            "unsupported_capabilities": list(self.unsupported_capabilities),
            "service_limits": dict(self.service_limits),
            "privacy_terms_url": self.privacy_terms_url,
            "tenant_authorization_required": self.tenant_authorization_required,
        }


@dataclass(frozen=True)
class AccessRecord:
    """Non-secret access state shown to the client and UI."""

    mode: AccessMode
    status: RelayStatus
    subject: str | None = None
    plan: str | None = None
    expires_at: float | None = None
    remaining_units: int | None = None
    last_error_code: str | None = None

    def public(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "status": self.status.value,
            "subject": self.subject,
            "plan": self.plan,
            "expires_at": self.expires_at,
            "remaining_units": self.remaining_units,
            "last_error_code": self.last_error_code,
        }


@dataclass(frozen=True)
class RelayRequest:
    """Admission metadata supplied by the Orville client, not provider auth."""

    subject: str
    mode: AccessMode = AccessMode.MANAGED
    privacy_class: str = "cloud_approved"
    estimated_units: int = 1
    workspace_id: str | None = None
    approved_remote: bool = False

    def __post_init__(self) -> None:
        if not self.subject.strip():
            raise ValueError("subject must not be empty")
        if self.privacy_class not in {"local_only", "cloud_approved", "restricted"}:
            raise ValueError("unsupported privacy_class")
        if self.estimated_units < 1:
            raise ValueError("estimated_units must be positive")
        if self.privacy_class != "cloud_approved" and not self.approved_remote:
            raise RelayError("remote execution requires explicit approval for this privacy class")
        if self.workspace_id and not self.approved_remote:
            raise RelayError("sending workspace or tool data remotely requires explicit user confirmation")


@dataclass(frozen=True)
class FallbackDecision:
    """Safe local fallback decision that never contains provider credentials."""

    primary_status: RelayStatus
    fallback_provider_id: str | None
    available: bool
    reason: str

    def public(self) -> dict[str, Any]:
        return {
            "primary_status": self.primary_status.value,
            "fallback_provider_id": self.fallback_provider_id,
            "available": self.available,
            "reason": self.reason,
        }


class BlackboxFallbackPolicy:
    """Choose a configured local provider or expose an actionable unavailable state."""

    _FALLBACK_STATUSES = frozenset({RelayStatus.NOT_CONNECTED, RelayStatus.EXPIRED, RelayStatus.INVALID, RelayStatus.RATE_LIMITED, RelayStatus.UNAVAILABLE, RelayStatus.DISABLED})

    def decide(self, status: RelayStatus, local_provider_ids: list[str] | tuple[str, ...]) -> FallbackDecision:
        candidates = tuple(provider_id.strip() for provider_id in local_provider_ids if provider_id.strip())
        if status is RelayStatus.READY:
            return FallbackDecision(status, None, True, "Blackbox relay is ready")
        if status in self._FALLBACK_STATUSES and candidates:
            return FallbackDecision(status, candidates[0], True, f"Blackbox relay is {status.value}; use configured local provider")
        if status in self._FALLBACK_STATUSES:
            return FallbackDecision(status, None, False, f"Blackbox relay is {status.value}; configure a local provider or repair the relay")
        return FallbackDecision(status, None, False, f"Blackbox relay state {status.value} is not eligible for fallback")


class QuotaLedger:
    """Small in-process quota ledger used by the relay boundary and tests.

    Production deployments should replace this with a durable, atomic store.
    """

    def __init__(self, limits: Mapping[str, int] | None = None) -> None:
        self._limits = dict(limits or {AccessMode.MANAGED.value: 100, AccessMode.USER_CONNECTED.value: 1000})
        self._used: dict[tuple[str, str], int] = {}

    def admit(self, subject: str, mode: AccessMode, units: int) -> int:
        key = (mode.value, subject)
        limit = self._limits.get(mode.value)
        if limit is None:
            raise RelayError(f"no quota policy configured for access mode {mode.value}")
        used = self._used.get(key, 0)
        if used + units > limit:
            raise RelayError(f"quota exceeded for access mode {mode.value}")
        self._used[key] = used + units
        return max(0, limit - self._used[key])

    def remaining(self, subject: str, mode: AccessMode) -> int:
        limit = self._limits.get(mode.value, 0)
        return max(0, limit - self._used.get((mode.value, subject), 0))


class CloudRelayBoundary:
    """Admits cloud work while keeping provider credentials server-side."""

    def __init__(self, config: RelayConfig, *, quota: QuotaLedger | None = None) -> None:
        self.config = config
        self.quota = quota or QuotaLedger()
        self._records: dict[tuple[AccessMode, str], AccessRecord] = {}
        self._started = monotonic()

    def set_access(self, record: AccessRecord) -> None:
        if record.mode is AccessMode.MANAGED and record.subject is None:
            raise ValueError("managed access must have a relay subject")
        self._records[(record.mode, record.subject or "")] = record

    def status(self, mode: AccessMode, subject: str) -> AccessRecord:
        return self._records.get(
            (mode, subject),
            AccessRecord(mode=mode, status=RelayStatus.NOT_CONNECTED, subject=subject),
        )

    def admit(self, request: RelayRequest) -> dict[str, Any]:
        record = self.status(request.mode, request.subject)
        if record.status is not RelayStatus.READY:
            raise RelayError(f"cloud access is {record.status.value}")
        if request.mode is AccessMode.MANAGED and record.subject != request.subject:
            raise RelayError("managed relay subject mismatch")
        remaining = self.quota.admit(request.subject, request.mode, request.estimated_units)
        endpoint_host = (urlparse(self.config.relay_url).hostname or "").lower()
        endpoint_family = "enterprise" if endpoint_host.startswith("enterprise.") else "standard"
        return {
            "provider": self.config.provider,
            "model": self.config.model,
            "relay_url": self.config.relay_url,
            "endpoint_family": endpoint_family,
            "access_mode": request.mode.value,
            "execution_location": "remote",
            "privacy_mode": request.privacy_class,
            "subject": request.subject,
            "privacy_class": request.privacy_class,
            "workspace_id": request.workspace_id,
            "confirmation_required": bool(request.workspace_id),
            "confirmation_scope": ["workspace_files", "repository_content", "images", "audio", "video", "tool_results"] if request.workspace_id else [],
            "remaining_units": remaining,
            "provider_credential_in_client": False,
            "supported_capabilities": list(self.config.supported_capabilities),
            "unsupported_capabilities": list(self.config.unsupported_capabilities),
            "service_limits": dict(self.config.service_limits),
            "privacy_terms_url": self.config.privacy_terms_url,
            "tenant_authorization_required": self.config.tenant_authorization_required,
        }

    def fallback_status(self, subject: str, local_provider_ids: list[str] | tuple[str, ...] = ()) -> FallbackDecision:
        return BlackboxFallbackPolicy().decide(self.status(AccessMode.MANAGED, subject).status, local_provider_ids)

    def public_status(self, subject: str, local_provider_ids: list[str] | tuple[str, ...] = ()) -> dict[str, Any]:
        managed = self.status(AccessMode.MANAGED, subject)
        user = self.status(AccessMode.USER_CONNECTED, subject)
        return {
            "relay": self.config.redacted(),
            "uptime_seconds": round(monotonic() - self._started, 3),
            "managed": managed.public(),
            "user_connected": user.public(),
            "fallback": self.fallback_status(subject, local_provider_ids).public(),
            "provider_credential_in_client": False,
        }
