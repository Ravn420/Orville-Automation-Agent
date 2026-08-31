"""Explicit policy and bounded storage for sensitive execution payload capture."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Mapping

from .security import SecretRedactor, SecurityViolation

_CAPTURE_KINDS = frozenset({"prompt", "completion", "tool_arguments", "tool_result"})


@dataclass(frozen=True)
class CapturePolicy:
    """Opt-in policy for capturing sensitive payloads."""

    enabled: bool = False
    allowed_readers: frozenset[str] = frozenset()
    retention_seconds: int = 0
    max_payload_chars: int = 8_000

    def validate(self) -> None:
        if self.retention_seconds < 0:
            raise ValueError("retention_seconds must be non-negative")
        if self.max_payload_chars < 1:
            raise ValueError("max_payload_chars must be positive")
        if self.enabled and self.retention_seconds < 1:
            raise ValueError("enabled capture requires a positive retention_seconds")
        if self.enabled and not self.allowed_readers:
            raise ValueError("enabled capture requires explicit allowed_readers")


@dataclass(frozen=True)
class CapturedPayload:
    """Redacted payload retained until its explicit expiry time."""

    run_id: str
    kind: str
    captured_by: str
    captured_at: str
    expires_at: str
    payload: Any

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CaptureStore:
    """In-memory, bounded capture store that fails closed by default."""

    def __init__(self, policy: CapturePolicy, redactor: type[SecretRedactor] = SecretRedactor) -> None:
        policy.validate()
        self.policy = policy
        self.redactor = redactor
        self._records: list[CapturedPayload] = []

    def capture(
        self,
        run_id: str,
        kind: str,
        payload: Any,
        *,
        actor: str,
        now: datetime | None = None,
    ) -> CapturedPayload | None:
        """Capture a redacted payload only when policy and actor checks pass."""
        if not self.policy.enabled:
            return None
        self._require_reader(actor)
        if kind not in _CAPTURE_KINDS:
            raise ValueError(f"unsupported capture kind: {kind}")
        if not run_id.strip():
            raise ValueError("run_id must not be blank")
        timestamp = now or datetime.now(UTC)
        if timestamp.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        redacted = self.redactor.redact(payload)
        bounded = _bound_payload(redacted, self.policy.max_payload_chars)
        record = CapturedPayload(
            run_id=run_id,
            kind=kind,
            captured_by=actor,
            captured_at=timestamp.isoformat(),
            expires_at=(timestamp + timedelta(seconds=self.policy.retention_seconds)).isoformat(),
            payload=bounded,
        )
        self._records.append(record)
        self.purge(now=timestamp)
        return record

    def read(self, *, actor: str, now: datetime | None = None) -> tuple[CapturedPayload, ...]:
        """Return unexpired captures only to an allow-listed reader."""
        self._require_reader(actor)
        self.purge(now=now)
        return tuple(self._records)

    def purge(self, *, now: datetime | None = None) -> int:
        """Remove expired records and return the number removed."""
        timestamp = now or datetime.now(UTC)
        if timestamp.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        before = len(self._records)
        self._records = [record for record in self._records if datetime.fromisoformat(record.expires_at) > timestamp]
        return before - len(self._records)

    def _require_reader(self, actor: str) -> None:
        if not actor.strip() or actor not in self.policy.allowed_readers:
            raise SecurityViolation("capture access is not authorized")


def _bound_payload(payload: Any, limit: int) -> Any:
    if isinstance(payload, str):
        return payload if len(payload) <= limit else payload[:limit] + "...[truncated]"
    if isinstance(payload, Mapping):
        return {str(key): _bound_payload(value, limit) for key, value in payload.items()}
    if isinstance(payload, (list, tuple)):
        return [_bound_payload(value, limit) for value in payload]
    return payload


__all__ = ["CapturePolicy", "CapturedPayload", "CaptureStore"]
