"""Small dependency-free observability primitives for Orville executions."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .security import SecretRedactor


@dataclass(frozen=True)
class TraceRecord:
    trace_id: str
    timestamp: str
    event: str
    attributes: dict[str, Any]


class JsonlTraceRecorder:
    def __init__(self, path: str | Path, redactor: SecretRedactor | None = None) -> None:
        self.path = Path(path)
        self.redactor = redactor or SecretRedactor()

    def record(self, trace_id: str, event: str, attributes: dict[str, Any] | None = None) -> TraceRecord:
        record = TraceRecord(trace_id, datetime.now(UTC).isoformat(), event, self.redactor.redact(attributes or {}))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(asdict(record), sort_keys=True, default=str) + "\n")
        return record

    def read(self) -> list[TraceRecord]:
        if not self.path.exists():
            return []
        records: list[TraceRecord] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                payload = json.loads(line)
                records.append(TraceRecord(**payload))
        return records


@dataclass(frozen=True)
class RunMetadata:
    """Privacy-aware metadata for one model-backed execution.

    Prompt content is never stored. Callers may provide a SHA-256 prompt hash;
    raw prompt capture is intentionally outside this contract.
    """

    run_id: str
    model_provider: str | None = None
    model_version: str | None = None
    prompt_hash: str | None = None
    tool_calls: tuple[dict[str, Any], ...] = ()
    agent_handoffs: tuple[dict[str, Any], ...] = ()
    retries: int = 0
    approvals: tuple[dict[str, Any], ...] = ()
    artifacts: tuple[dict[str, Any], ...] = ()
    latency_ms: float | None = None
    token_usage: dict[str, int] | None = None
    finish_reason: str | None = None
    cache_hit: bool | None = None
    cost_metadata: dict[str, Any] | None = None
    failure: dict[str, Any] | None = None

    def validate(self) -> None:
        if not self.run_id.strip():
            raise ValueError("run_id must not be blank")
        if self.retries < 0:
            raise ValueError("retries must be non-negative")
        if self.latency_ms is not None and self.latency_ms < 0:
            raise ValueError("latency_ms must be non-negative")
        if self.prompt_hash is not None and len(self.prompt_hash) != 64:
            raise ValueError("prompt_hash must be a SHA-256 hex digest")
        if self.token_usage is not None and any(value < 0 for value in self.token_usage.values()):
            raise ValueError("token usage values must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


def hash_prompt(prompt: str) -> str:
    """Return a stable prompt digest without retaining prompt content."""
    import hashlib

    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


class RunMetadataRecorder:
    """Persist redacted per-run metadata through the existing trace recorder."""

    def __init__(self, path: str | Path, redactor: SecretRedactor | None = None) -> None:
        self.trace_recorder = JsonlTraceRecorder(path, redactor)

    def record_run(self, metadata: RunMetadata) -> TraceRecord:
        metadata.validate()
        return self.trace_recorder.record(metadata.run_id, "run.metadata", metadata.to_dict())

    def read(self) -> list[TraceRecord]:
        return self.trace_recorder.read()
