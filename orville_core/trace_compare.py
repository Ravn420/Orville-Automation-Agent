"""Deterministic comparison of redacted Orville trace runs."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TraceComparison:
    passed: bool
    missing_events: tuple[str, ...] = ()
    unexpected_events: tuple[str, ...] = ()
    changed_events: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"passed": self.passed, "missing_events": list(self.missing_events), "unexpected_events": list(self.unexpected_events), "changed_events": list(self.changed_events)}


def _read(path: Path) -> list[dict[str, Any]]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def compare_trace_runs(baseline: str | Path, candidate: str | Path) -> TraceComparison:
    base = _read(Path(baseline))
    current = _read(Path(candidate))
    base_names = [str(item.get("event", "")) for item in base]
    current_names = [str(item.get("event", "")) for item in current]
    missing = tuple(sorted(set(base_names) - set(current_names)))
    unexpected = tuple(sorted(set(current_names) - set(base_names)))
    changed: list[str] = []
    for name in sorted(set(base_names) & set(current_names)):
        left = next(item.get("attributes", {}) for item in base if item.get("event") == name)
        right = next(item.get("attributes", {}) for item in current if item.get("event") == name)
        if left != right:
            changed.append(name)
    return TraceComparison(not missing and not unexpected and not changed, missing, unexpected, tuple(changed))
