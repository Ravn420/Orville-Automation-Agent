"""Privacy-safe per-run observability records and JSONL persistence."""
from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from .security import SecretRedactor


@dataclass
class RunObservabilityRecord:
    """Bounded metadata for one agent/model run; raw prompts and secrets are never stored."""

    run_id: str
    task_id: str | None = None
    agent_id: str | None = None
    provider: str | None = None
    model: str | None = None
    model_version: str | None = None
    prompt_hash: str | None = None
    prompt_capture: str = "hash-only"
    started_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    finished_at: str | None = None
    latency_ms: float | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    agent_handoffs: list[dict[str, Any]] = field(default_factory=list)
    retries: list[dict[str, Any]] = field(default_factory=list)
    approvals: list[dict[str, Any]] = field(default_factory=list)
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    token_usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str | None = None
    cache: dict[str, Any] = field(default_factory=dict)
    cost_metadata: dict[str, Any] = field(default_factory=dict)
    failure: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.run_id.strip():
            raise ValueError("run_id is required")
        for field_name in ("task_id", "agent_id", "provider", "model", "model_version"):
            value = getattr(self, field_name)
            if value is not None and not str(value).strip():
                raise ValueError(f"{field_name} must be non-empty when provided")
        self._normalize_token_usage()

    @staticmethod
    def hash_prompt(prompt: str) -> str:
        """Return a stable SHA-256 prompt digest without retaining prompt contents."""
        if not isinstance(prompt, str):
            raise TypeError("prompt must be text")
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    @classmethod
    def start(cls, run_id: str, *, prompt: str | None = None, **metadata: Any) -> "RunObservabilityRecord":
        record = cls(run_id=run_id, **metadata)
        if prompt is not None:
            record.prompt_hash = cls.hash_prompt(prompt)
        return record

    def _normalize_token_usage(self) -> None:
        normalized: dict[str, int] = {}
        for key, value in self.token_usage.items():
            if key not in {"input", "output", "total", "cached_input"}:
                raise ValueError(f"unsupported token usage field: {key}")
            integer = int(value)
            if integer < 0:
                raise ValueError("token usage must not be negative")
            normalized[key] = integer
        if "total" not in normalized and ("input" in normalized or "output" in normalized):
            normalized["total"] = normalized.get("input", 0) + normalized.get("output", 0)
        self.token_usage = normalized

    def record_tool_call(self, name: str, *, outcome: str, latency_ms: float | None = None, approved: bool = False, error_class: str | None = None) -> None:
        self.tool_calls.append(self._bounded_event({"name": name, "outcome": outcome, "latency_ms": latency_ms, "approved": approved, "error_class": error_class}))

    def record_handoff(self, from_agent: str, to_agent: str, *, reason: str, outcome: str = "requested") -> None:
        self.agent_handoffs.append(self._bounded_event({"from_agent": from_agent, "to_agent": to_agent, "reason": reason, "outcome": outcome}))

    def record_retry(self, *, attempt: int, reason: str, backoff_ms: float | None = None) -> None:
        if attempt < 1:
            raise ValueError("retry attempt must be positive")
        self.retries.append(self._bounded_event({"attempt": attempt, "reason": reason, "backoff_ms": backoff_ms}))

    def record_approval(self, *, approval_id: str, action: str, scope: str, outcome: str, reviewer: str | None = None) -> None:
        self.approvals.append(self._bounded_event({"approval_id": approval_id, "action": action, "scope": scope, "outcome": outcome, "reviewer": reviewer}))

    def record_artifact(self, *, artifact_id: str, media_type: str, checksum: str | None = None, size_bytes: int | None = None) -> None:
        if size_bytes is not None and size_bytes < 0:
            raise ValueError("artifact size must not be negative")
        self.artifacts.append(self._bounded_event({"artifact_id": artifact_id, "media_type": media_type, "checksum": checksum, "size_bytes": size_bytes}))

    def record_cache(self, *, hit: bool, key_hash: str | None = None, source: str | None = None) -> None:
        self.cache = self._bounded_event({"hit": hit, "key_hash": key_hash, "source": source})

    def record_failure(self, *, error_class: str, message: str, retryable: bool = False) -> None:
        self.failure = self._bounded_event({"error_class": error_class, "message": message, "retryable": retryable})

    def finish(self, *, finish_reason: str, latency_ms: float | None = None, token_usage: Mapping[str, int] | None = None, cost_metadata: Mapping[str, Any] | None = None) -> None:
        if not finish_reason.strip():
            raise ValueError("finish_reason is required")
        if latency_ms is not None and latency_ms < 0:
            raise ValueError("latency_ms must not be negative")
        self.finished_at = datetime.now(UTC).isoformat()
        self.finish_reason = finish_reason[:128]
        self.latency_ms = latency_ms
        if token_usage is not None:
            self.token_usage = dict(token_usage)
            self._normalize_token_usage()
        if cost_metadata is not None:
            self.cost_metadata = self._bounded_event(dict(cost_metadata))

    @staticmethod
    def _bounded_event(payload: Mapping[str, Any]) -> dict[str, Any]:
        safe = SecretRedactor.redact(dict(payload))
        return {str(key): value for key, value in safe.items()}

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        # Redact scalar identity fields individually. Redacting the whole mapping
        # would incorrectly replace safe structured fields such as token_usage.
        for key in ("run_id", "task_id", "agent_id", "provider", "model", "model_version", "prompt_hash", "prompt_capture", "started_at", "finished_at", "finish_reason"):
            if payload.get(key) is not None:
                payload[key] = SecretRedactor.redact(str(payload[key]))
        return payload


class RunObservabilityRecorder:
    """Append-only JSONL recorder for completed or intermediate run records."""

    def __init__(self, path: str | Path, redactor: SecretRedactor | None = None) -> None:
        self.path = Path(path)
        self.redactor = redactor or SecretRedactor()
        self._lock = threading.RLock()

    def write(self, record: RunObservabilityRecord) -> dict[str, Any]:
        payload = record.to_dict()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with self.path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(payload, sort_keys=True, default=str) + "\n")
        return payload

    def read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        with self._lock:
            return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]


def elapsed_ms(started: float, ended: float | None = None) -> float:
    """Calculate a non-negative monotonic latency measurement."""
    value = (ended if ended is not None else time.perf_counter()) - started
    if value < 0:
        raise ValueError("elapsed time must not be negative")
    return round(value * 1000, 3)
