"""Measure bounded local GUI-related performance workloads.

The harness uses a fixed, deterministic workload and reports measurements rather
than claiming production performance. It does not start a GUI window or contact
external services.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from windows_gui import classify_dependency_state, classify_workflow_state, dependency_state_message


DEFAULT_TASKS = 1000
DEFAULT_ARTIFACTS = 500


def _startup_ms() -> float:
    start = time.perf_counter()
    completed = subprocess.run(
        [sys.executable, "-c", "import windows_gui"],
        check=True,
        capture_output=True,
        text=True,
    )
    if completed.stderr:
        raise RuntimeError("GUI import emitted stderr")
    return (time.perf_counter() - start) * 1000


def _workload(tasks: int, artifacts: int) -> dict[str, Any]:
    return {
        "graph": {
            "tasks": [
                {"task_id": f"task-{index:04d}", "status": "ready" if index % 3 else "completed"}
                for index in range(tasks)
            ]
        },
        "artifacts": [
            {"artifact_id": f"artifact-{index:04d}", "kind": "document", "status": "ready"}
            for index in range(artifacts)
        ],
    }


def measure(tasks: int = DEFAULT_TASKS, artifacts: int = DEFAULT_ARTIFACTS) -> dict[str, Any]:
    """Return measured milliseconds, peak bytes, workload sizes, and thresholds."""
    workload = _workload(tasks, artifacts)
    tracemalloc.start()
    start = time.perf_counter()
    for _ in range(20):
        classify_workflow_state(workload)
        classify_dependency_state({"dependency": "local_endpoint"})
        dependency_state_message("local_endpoint_unavailable")
    encoded = json.dumps(workload, separators=(",", ":"))
    interaction_ms = (time.perf_counter() - start) * 1000 / 20
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "workload": {"tasks": tasks, "artifacts": artifacts},
        "measurements": {
            "startup_ms": round(startup_ms := _startup_ms(), 3),
            "interaction_ms": round(interaction_ms, 3),
            "peak_memory_bytes": peak_bytes,
            "serialized_bytes": len(encoded.encode("utf-8")),
        },
        "thresholds": {
            "startup_ms_max": 2500,
            "interaction_ms_max": 200,
            "peak_memory_bytes_max": 64 * 1024 * 1024,
        },
        "pass": {
            "startup": startup_ms <= 2500,
            "interaction": interaction_ms <= 200,
            "memory": peak_bytes <= 64 * 1024 * 1024,
        },
        "notes": [
            "Fixed local workload; repeat on the slowest supported target before release.",
            "No GUI window, external service, credential, or provider call is used.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=int, default=DEFAULT_TASKS)
    parser.add_argument("--artifacts", type=int, default=DEFAULT_ARTIFACTS)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not 1 <= args.tasks <= 10000 or not 1 <= args.artifacts <= 10000:
        parser.error("tasks and artifacts must be between 1 and 10000")
    result = measure(args.tasks, args.artifacts)
    output = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0 if all(result["pass"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
