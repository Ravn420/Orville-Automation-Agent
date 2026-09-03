"""Opt-in, redacted, access-controlled sensitive execution capture."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Mapping

from .observability import JsonlTraceRecorder
from .security import SecretRedactor


CAPTURE_KINDS = {"prompt", "completion", "tool_arguments", "tool_result"}


@dataclass(frozen=True)
class CapturePolicy:
    enabled: bool = False
    allowed_roles: frozenset[str] = frozenset()
    retention_seconds: int = 0
    max_payload_bytes: int = 16_384

    def validate(self) -> None:
        if self.retention_seconds < 0:
            raise ValueError("retention_seconds must not be negative")
        if self.max_payload_bytes <= 0:
            raise ValueError("max_payload_bytes must be positive")
        if self.enabled and (not self.allowed_roles or self.retention_seconds <= 0):
            raise ValueError("enabled capture requires allowed_roles and positive retention_seconds")


class SensitiveCapture:
    def __init__(self, policy: CapturePolicy, recorder: JsonlTraceRecorder) -> None:
        policy.validate()
        self.policy = policy
        self.recorder = recorder

    def record(self, trace_id: str, kind: str, payload: Any, *, role: str) -> bool:
        if kind not in CAPTURE_KINDS:
            raise ValueError(f"unsupported capture kind: {kind}")
        if not self.policy.enabled:
            return False
        if role not in self.policy.allowed_roles:
            raise PermissionError("capture role is not allowlisted")
        redacted = SecretRedactor.redact(payload)
        serialized = str(redacted).encode("utf-8")
        if len(serialized) > self.policy.max_payload_bytes:
            redacted = {"truncated": True, "sha256": __import__("hashlib").sha256(serialized).hexdigest()}
        expires_at = datetime.now(UTC) + timedelta(seconds=self.policy.retention_seconds)
        self.recorder.record(trace_id, "sensitive.capture", {"kind": kind, "payload": redacted, "expires_at": expires_at.isoformat(), "role": role})
        return True
