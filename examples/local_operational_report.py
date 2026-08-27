"""Generate an operational report from deterministic local events."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile

from tools.operational_report import build_report, load_events


def main() -> None:
    events = [
        {"execution_id": "standalone-demo", "status": "completed", "duration_seconds": 0.25},
        {"execution_id": "standalone-demo", "status": "completed", "duration_seconds": 0.50},
    ]
    with tempfile.TemporaryDirectory(prefix="orville-example-") as directory:
        path = Path(directory) / "events.jsonl"
        path.write_text("\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8")
        report = build_report(load_events(path), target="local")
        print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
