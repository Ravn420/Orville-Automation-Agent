"""Small, dependency-free security policy primitives for Orville tool execution."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any


class SecurityViolation(PermissionError):
    """Raised when a requested operation violates an active security policy."""


class CredentialStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass(frozen=True)
class CredentialReference:
    """Value-free reference to a protected provider credential."""

    reference_id: str
    provider: str
    auth_method: str
    scopes: tuple[str, ...] = ()
    expires_at: datetime | None = None
    status: CredentialStatus = CredentialStatus.ACTIVE

    def __post_init__(self) -> None:
        if not self.reference_id.strip() or not self.provider.strip():
            raise ValueError("credential reference ID and provider are required")
        if self.auth_method not in {"api_key", "bearer", "oauth2"}:
            raise ValueError("unsupported credential authentication method")
        object.__setattr__(self, "scopes", tuple(sorted({scope.strip() for scope in self.scopes if scope.strip()})))

    def lifecycle_status(self, *, now: datetime | None = None) -> CredentialStatus:
        if self.status is CredentialStatus.REVOKED:
            return self.status
        if self.expires_at is not None and self.expires_at <= (now or datetime.now(UTC)):
            return CredentialStatus.EXPIRED
        return CredentialStatus.ACTIVE

    def require_active(self, *, now: datetime | None = None) -> None:
        status = self.lifecycle_status(now=now)
        if status is not CredentialStatus.ACTIVE:
            raise SecurityViolation(f"credential reference is {status.value}")


@dataclass(frozen=True)
class ProviderPermissionPolicy:
    """Provider-specific allowlist for scopes and sensitive operations."""

    provider: str
    allowed_scopes: frozenset[str] = frozenset()
    allowed_actions: frozenset[str] = frozenset({"health", "models", "chat"})

    def check(self, reference: CredentialReference, action: str, *, required_scopes: set[str] | frozenset[str] = frozenset()) -> None:
        if reference.provider != self.provider:
            raise SecurityViolation("credential provider does not match permission policy")
        reference.require_active()
        if action not in self.allowed_actions:
            raise SecurityViolation(f"provider action is not allowlisted: {action}")
        missing = set(required_scopes) - set(reference.scopes) - set(self.allowed_scopes)
        if missing:
            raise SecurityViolation(f"provider scopes are insufficient: {sorted(missing)}")


@dataclass
class ToolPolicy:
    """Allowlist-based policy for agent-proposed tool calls."""

    allowed_tools: set[str] = field(default_factory=set)
    approved_tools: set[str] = field(default_factory=set)
    dry_run: bool = True
    require_approval: bool = True

    def check(self, tool_name: str, *, approved: bool = False) -> None:
        if tool_name not in self.allowed_tools:
            raise SecurityViolation(f"tool is not allowlisted: {tool_name}")
        if self.require_approval and not (approved or tool_name in self.approved_tools):
            raise SecurityViolation(f"tool requires approval: {tool_name}")

    def authorize(self, tool_name: str) -> None:
        if tool_name not in self.allowed_tools:
            raise SecurityViolation(f"cannot authorize non-allowlisted tool: {tool_name}")
        self.approved_tools.add(tool_name)


@dataclass(frozen=True)
class FilesystemPolicy:
    """Restrict file access to explicit roots and reject traversal."""

    allowed_roots: tuple[Path, ...]
    allow_write: bool = False

    def resolve(self, path: str | Path, *, write: bool = False) -> Path:
        candidate = Path(path).expanduser().resolve()
        roots = tuple(root.expanduser().resolve() for root in self.allowed_roots)
        if not any(candidate == root or root in candidate.parents for root in roots):
            raise SecurityViolation(f"path is outside allowed roots: {candidate}")
        if write and (not self.allow_write):
            raise SecurityViolation("filesystem writes are disabled")
        return candidate


@dataclass(frozen=True)
class NetworkPolicy:
    """Allow only explicitly configured hosts for outbound requests."""

    allowed_hosts: frozenset[str] = frozenset()
    allow_private: bool = False

    def check_host(self, host: str) -> None:
        normalized = host.lower().strip().rstrip(".")
        if normalized not in self.allowed_hosts:
            raise SecurityViolation(f"network host is not allowlisted: {host}")
        if not self.allow_private and (normalized in {"localhost", "127.0.0.1", "::1"} or normalized.startswith("192.168.") or normalized.startswith("10.")):
            raise SecurityViolation(f"private network access is disabled: {host}")


class SecretRedactor:
    """Redact common credential fields and bearer/API-key patterns from logs."""

    _secret_key = re.compile(r"(api[_-]?key|token|secret|password|authorization|credential)", re.I)
    _bearer = re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]+", re.I)
    _token_shaped = re.compile(r"\b(?:sk|bbx|tok|key|secret)[_-][A-Za-z0-9._~+/=-]{8,}\b", re.I)
    _account_value = re.compile(r"\baccount(?:[_ -]?(?:id|identifier|email))?\s*[:=]?\s*[A-Za-z0-9][A-Za-z0-9._-]{7,}", re.I)
    _query_secret = re.compile(r"(api[_-]?key|token|secret|password|access[_-]?token|refresh[_-]?token)\s*=\s*([^&\s]+)", re.I)

    @classmethod
    def redact(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: "[REDACTED]" if cls._secret_key.search(str(key)) else cls.redact(item) for key, item in value.items()}
        if isinstance(value, list):
            return [cls.redact(item) for item in value]
        if isinstance(value, tuple):
            return tuple(cls.redact(item) for item in value)
        if isinstance(value, str):
            output = cls._bearer.sub("Bearer [REDACTED]", value)
            output = cls._account_value.sub("account=[REDACTED]", output)
            output = cls._query_secret.sub(lambda match: f"{match.group(1)}=[REDACTED]", output)
            return cls._token_shaped.sub("[REDACTED]", output)
        return value

    @classmethod
    def redact_exception(cls, error: BaseException) -> str:
        """Return a safe exception message suitable for logs and API diagnostics."""
        return str(cls.redact(str(error)))[:1_000]


def require_dry_run(policy: ToolPolicy) -> None:
    """Fail closed when a caller attempts a side effect in dry-run mode."""

    if policy.dry_run:
        raise SecurityViolation("external side effects are disabled in dry-run mode")


@dataclass(frozen=True)
class LeastPrivilegePolicy:
    """Bound a task or agent to only its declared resources and actions.

    Empty grants deny access. Callers should create the narrowest policy for one
    task or run rather than sharing an administrator-wide policy.
    """

    connector_scopes: dict[str, frozenset[str]] = field(default_factory=dict)
    repository_ids: frozenset[str] = frozenset()
    file_roots: tuple[Path, ...] = ()
    remote_hosts: frozenset[str] = frozenset()
    remote_actions: frozenset[str] = frozenset()
    allow_repository_write: bool = False
    allow_file_write: bool = False

    def check_connector(self, connector_id: str, requested_scopes: set[str] | frozenset[str] = frozenset()) -> None:
        allowed = self.connector_scopes.get(connector_id)
        if allowed is None:
            raise SecurityViolation(f"connector is not allowlisted: {connector_id}")
        missing = set(requested_scopes) - set(allowed)
        if missing:
            raise SecurityViolation(f"connector scopes are insufficient: {sorted(missing)}")

    def check_repository(self, repository_id: str, *, write: bool = False) -> None:
        if repository_id not in self.repository_ids:
            raise SecurityViolation(f"repository is not allowlisted: {repository_id}")
        if write and not self.allow_repository_write:
            raise SecurityViolation("repository writes are disabled")

    def resolve_file(self, path: str | Path, *, write: bool = False) -> Path:
        return FilesystemPolicy(self.file_roots, allow_write=self.allow_file_write).resolve(path, write=write)

    def check_remote(self, host: str, action: str) -> None:
        normalized = host.lower().strip().rstrip(".")
        if normalized not in {item.lower().strip().rstrip(".") for item in self.remote_hosts}:
            raise SecurityViolation(f"remote host is not allowlisted: {host}")
        if action not in self.remote_actions:
            raise SecurityViolation(f"remote action is not allowlisted: {action}")
