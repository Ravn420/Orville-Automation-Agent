"""Explicit confirmation gates for high-impact Orville operations.

The module is standalone and side-effect free: callers create a request before
an operation, present its stable summary to a user, and consume a matching
single-use receipt immediately before execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import secrets


SENSITIVE_OPERATION_KINDS = frozenset(
    {
        "payment",
        "purchase",
        "publish",
        "delete",
        "account_change",
        "permission_change",
        "credential_entry",
        "external_send",
        "connector_mutation",
        "destructive_file_action",
    }
)


class ConfirmationRequired(PermissionError):
    """Raised when a sensitive operation lacks a valid explicit confirmation."""


@dataclass(frozen=True)
class ConfirmationRequest:
    """Safe-to-display operation summary; never include credentials or payloads."""

    operation: str
    target: str
    scope: str
    requester: str
    created_at: datetime
    expires_at: datetime
    fingerprint: str

    @classmethod
    def create(
        cls,
        operation: str,
        target: str,
        scope: str,
        requester: str,
        *,
        ttl_seconds: int = 300,
        now: datetime | None = None,
    ) -> "ConfirmationRequest":
        if operation not in SENSITIVE_OPERATION_KINDS:
            raise ValueError(f"unsupported sensitive operation: {operation}")
        if not all(value.strip() for value in (target, scope, requester)):
            raise ValueError("target, scope, and requester are required")
        if not 1 <= ttl_seconds <= 900:
            raise ValueError("confirmation TTL must be between 1 and 900 seconds")
        created = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        expires = created + timedelta(seconds=ttl_seconds)
        material = "\x1f".join((operation, target, scope, requester, created.isoformat()))
        return cls(operation, target, scope, requester, created, expires, sha256(material.encode()).hexdigest())


@dataclass(frozen=True)
class ConfirmationReceipt:
    """Single-use proof of explicit user confirmation for one request."""

    fingerprint: str
    confirmer: str
    confirmed_at: datetime
    nonce: str


class ConfirmationGate:
    """Issue and consume explicit confirmations; fail closed on mismatch or reuse."""

    def __init__(self) -> None:
        self._consumed: set[str] = set()

    def confirm(self, request: ConfirmationRequest, *, confirmer: str, now: datetime | None = None) -> ConfirmationReceipt:
        if not confirmer.strip():
            raise ValueError("confirmer is required")
        confirmed = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        if confirmed > request.expires_at:
            raise ConfirmationRequired("confirmation has expired")
        return ConfirmationReceipt(request.fingerprint, confirmer, confirmed, secrets.token_urlsafe(16))

    def require(self, request: ConfirmationRequest, receipt: ConfirmationReceipt | None, *, now: datetime | None = None) -> None:
        current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        if current > request.expires_at:
            raise ConfirmationRequired("confirmation has expired")
        if receipt is None or receipt.fingerprint != request.fingerprint:
            raise ConfirmationRequired("explicit confirmation is required")
        if not receipt.confirmer.strip() or receipt.confirmed_at > request.expires_at:
            raise ConfirmationRequired("confirmation receipt is invalid")
        if receipt.nonce in self._consumed:
            raise ConfirmationRequired("confirmation receipt has already been used")
        self._consumed.add(receipt.nonce)
