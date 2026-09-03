"""Approval records for browser actions that may submit or download data."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any, Mapping


@dataclass
class BrowserApproval:
    approval_id: str
    session_id: str
    action: str
    target: str
    field_names: tuple[str, ...]
    requested_at: str
    expires_at: str
    status: str = "pending"
    decision_reason: str = ""

    def validate(self, now: datetime | None = None) -> None:
        if self.action not in {"form_submission", "download"}:
            raise ValueError("unsupported browser approval action")
        if self.status not in {"pending", "approved", "rejected", "expired"}:
            raise ValueError("invalid browser approval status")
        if not self.session_id.strip() or not self.target.strip():
            raise ValueError("session_id and target are required")
        current = now or datetime.now(UTC)
        if current >= datetime.fromisoformat(self.expires_at):
            self.status = "expired"

    def decide(self, approved: bool, reason: str = "") -> None:
        self.validate()
        if self.status != "pending":
            raise ValueError("browser approval is no longer pending")
        self.status = "approved" if approved else "rejected"
        self.decision_reason = reason[:500]

    def to_dict(self) -> dict[str, Any]:
        return {"approval_id": self.approval_id, "session_id": self.session_id, "action": self.action, "target": self.target, "field_names": list(self.field_names), "requested_at": self.requested_at, "expires_at": self.expires_at, "status": self.status, "decision_reason": self.decision_reason}


def create_browser_approval(approval_id: str, session_id: str, action: str, target: str, fields: Mapping[str, object] | None = None, *, ttl_seconds: int = 300, now: datetime | None = None) -> BrowserApproval:
    if ttl_seconds < 1 or ttl_seconds > 3600:
        raise ValueError("approval TTL must be between 1 and 3600 seconds")
    current = now or datetime.now(UTC)
    safe_target = target[:1000]
    record = BrowserApproval(approval_id, session_id, action, safe_target, tuple(sorted(str(key)[:200] for key in (fields or {}).keys())), current.isoformat(), (current + timedelta(seconds=ttl_seconds)).isoformat())
    record.validate(current)
    return record


def approval_scope_digest(record: BrowserApproval) -> str:
    """Return a stable digest of approval scope without retaining field values."""
    payload = f"{record.session_id}|{record.action}|{record.target}|{','.join(record.field_names)}"
    return sha256(payload.encode("utf-8")).hexdigest()
