"""Generate a bounded operational report from Orville JSONL execution logs."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any, Iterable


MAX_EVENTS = 100_000


def load_events(path: Path) -> list[dict[str, Any]]:
    """Load bounded JSON-object events; malformed lines fail closed."""
    events: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line_number > MAX_EVENTS:
                raise ValueError("event log exceeds the maximum supported size")
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"event line {line_number} is not a JSON object")
            events.append(value)
    return events


def build_report(events: Iterable[dict[str, Any]], *, target: str = "local") -> dict[str, Any]:
    """Build a secret-safe summary for local, desktop, hosted, or persistent targets."""
    if target not in {"local", "attached-desktop", "web-hosting", "persistent-computing", "sandbox"}:
        raise ValueError(f"unsupported report target: {target}")
    material = list(events)
    statuses = Counter(str(event.get("status", "unknown")) for event in material)
    failures = sum(1 for event in material if str(event.get("level", "")).lower() in {"error", "critical"} or str(event.get("status", "")).lower() in {"failed", "error"})
    durations = [float(event["duration_seconds"]) for event in material if isinstance(event.get("duration_seconds"), (int, float)) and float(event["duration_seconds"]) >= 0]
    executions = {str(event["execution_id"]) for event in material if event.get("execution_id")}
    return {
        "target": target,
        "event_count": len(material),
        "execution_count": len(executions),
        "failure_count": failures,
        "success_rate": round((len(material) - failures) / len(material), 4) if material else 1.0,
        "duration_seconds": {"count": len(durations), "mean": round(sum(durations) / len(durations), 4) if durations else 0.0, "max": max(durations, default=0.0)},
        "status_counts": dict(sorted(statuses.items())),
        "data_quality": {"bounded": True, "secrets_included": False},
    }


def write_report(report: dict[str, Any], destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a local Orville operational report")
    parser.add_argument("events", type=Path)
    parser.add_argument("--target", default="local", choices=("local", "attached-desktop", "web-hosting", "persistent-computing", "sandbox"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    report = build_report(load_events(args.events), target=args.target)
    if args.output:
        write_report(report, args.output)
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
