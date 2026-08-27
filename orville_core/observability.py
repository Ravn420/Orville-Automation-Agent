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
