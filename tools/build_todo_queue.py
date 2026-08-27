#!/usr/bin/env python3
"""Build a guarded automation queue from non-terminal repository TODO records.

This utility only translates checked-state and task identifiers into the queue
schema. It does not dispatch tasks, modify TODO.md, access credentials, or
perform external actions.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

CHECKBOX = re.compile(r"^\s*- \[(?P<state>[ xX!-])\] (?P<item>.*)$")
TASK_ID = re.compile(r"<!-- task-id:(TODO-[a-f0-9]+) -->")


class QueueBuildError(RuntimeError):
    """Raised when the canonical TODO cannot be translated safely."""


def normalize_item(item: str) -> str:
    """Remove the stable marker from the human-readable TODO text."""
    return TASK_ID.sub("", item).strip()


def priority_for(line_number: int, state: str, heading: str) -> int:
    """Assign deterministic conservative priority; eligibility remains status-gated."""
    if state == "-":
        return 950
    if state == "!":
        return 100
    if "M14" in heading:
        return 900
    if "M13" in heading:
        return 850
    if "Current security milestone" in heading:
        return 800
    return max(200, 700 - min(line_number, 450))


def queue_status(state: str, item: str) -> str:
    """Map canonical TODO states to editable pre-dispatch queue states."""
    if state == "!":
        return "blocked"
    if state == "-":
        return "review"
    if "reusable verification-template placeholder" in item:
        return "blocked"
    return "backlog"


def queue_dependencies(state: str, item: str) -> list[str]:
    """Return only stable task IDs; external conditions belong in the queue status."""
    del state, item
    return []


def queue_acceptance(item: str) -> list[str]:
    """Generate generic, verifiable acceptance requirements from canonical text."""
    return [
        f"Implement the canonical TODO outcome: {normalize_item(item)}",
        "Run focused validation appropriate to the changed paths and retain sanitized evidence.",
        "Update control files and mark the canonical TODO complete only after verification succeeds.",
    ]


def parse_todos(todo_path: Path) -> list[dict[str, Any]]:
    """Return every non-terminal TODO record with a stable task identifier."""
    tasks: list[dict[str, Any]] = []
    heading = "Repository backlog"
    seen_ids: set[str] = set()
    for line_number, line in enumerate(todo_path.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("##"):
            heading = line.lstrip("#").strip()
        match = CHECKBOX.match(line)
        if not match:
            continue
        state = match.group("state")
        if state in {"x", "X"}:
            continue
        item = match.group("item").strip()
        markers = TASK_ID.findall(item)
        if len(markers) != 1:
            raise QueueBuildError(
                f"non-terminal TODO at line {line_number} must have exactly one stable task ID"
            )
        task_id = markers[0]
        if task_id in seen_ids:
            raise QueueBuildError(f"duplicate non-terminal TODO task ID: {task_id}")
        seen_ids.add(task_id)
        status = queue_status(state, item)
        tasks.append(
            {
                "id": task_id,
                "status": status,
                "title": normalize_item(item),
                "priority": priority_for(line_number, state, heading),
                "dependencies": queue_dependencies(state, item),
                "acceptance_criteria": queue_acceptance(item),
                "execution": {
                    "allowed_actions": ["edit_files", "run_tests"],
                    "timeout_minutes": 30,
                },
                "revision": 0,
                "source": {"todo_path": str(todo_path), "line": line_number, "heading": heading},
            }
        )
    return tasks


def build_queue(template_path: Path, todo_path: Path) -> dict[str, Any]:
    """Build a schema-v1 queue based on the approved template shell."""
    try:
        template = json.loads(template_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise QueueBuildError(f"unable to read queue template: {exc}") from exc
    if template.get("schema_version") != 1 or not isinstance(template.get("audit"), list):
        raise QueueBuildError("queue template does not match the supported schema")
    tasks = parse_todos(todo_path)
    status_counts = {state: sum(1 for task in tasks if task["status"] == state) for state in ("backlog", "review", "blocked")}
    return {
        "schema_version": 1,
        "queue_revision": 0,
        "tasks": tasks,
        "audit": [
            {
                "at": datetime.now(timezone.utc).isoformat(),
                "actor": "todo-queue-builder",
                "action": "initialized",
                "reason": "Translated all non-terminal canonical TODO records without dispatching work.",
                "source": str(todo_path),
                "task_count": len(tasks),
                "status_counts": status_counts,
            }
        ],
    }


def validate_queue(current: dict[str, Any], expected: dict[str, Any]) -> None:
    """Validate immutable queue identity while allowing guarded planning revisions."""
    if current.get("schema_version") != 1:
        raise QueueBuildError("queue check failed: unsupported schema version")
    if not isinstance(current.get("queue_revision"), int) or current["queue_revision"] < 0:
        raise QueueBuildError("queue check failed: invalid queue revision")
    if not isinstance(current.get("audit"), list):
        raise QueueBuildError("queue check failed: missing audit history")
    tasks = current.get("tasks")
    if not isinstance(tasks, list):
        raise QueueBuildError("queue check failed: missing task list")
    expected_by_id = {task["id"]: task for task in expected["tasks"]}
    current_by_id: dict[str, dict[str, Any]] = {}
    for task in tasks:
        if not isinstance(task, dict) or not isinstance(task.get("id"), str):
            raise QueueBuildError("queue check failed: invalid task record")
        task_id = task["id"]
        if task_id in current_by_id:
            raise QueueBuildError(f"queue check failed: duplicate task ID {task_id}")
        current_by_id[task_id] = task
        required = ("status", "title", "priority", "dependencies", "acceptance_criteria", "execution", "revision", "source")
        if any(field not in task for field in required):
            raise QueueBuildError(f"queue check failed: incomplete task record {task_id}")
        if task["status"] not in {"backlog", "ready", "blocked", "review", "in_progress", "done", "failed"}:
            raise QueueBuildError(f"queue check failed: invalid status for {task_id}")
        if not isinstance(task["priority"], int) or not isinstance(task["revision"], int) or task["revision"] < 0:
            raise QueueBuildError(f"queue check failed: invalid revision or priority for {task_id}")
    if set(current_by_id) != set(expected_by_id):
        missing = sorted(set(expected_by_id) - set(current_by_id))
        unexpected = sorted(set(current_by_id) - set(expected_by_id))
        raise QueueBuildError(f"queue check failed: canonical task IDs differ; missing={missing[:3]} unexpected={unexpected[:3]}")
    for task_id, source_task in expected_by_id.items():
        task = current_by_id[task_id]
        if task.get("source") != source_task["source"]:
            raise QueueBuildError(f"queue check failed: source mapping changed for {task_id}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--todo", type=Path, default=Path("TODO.md"))
    parser.add_argument(
        "--template",
        type=Path,
        default=Path("/home/ubuntu/skills/automation-task-edit/templates/task-queue.json"),
    )
    parser.add_argument("--output", type=Path, default=Path("config/todo-task-queue.json"))
    parser.add_argument("--check", action="store_true", help="validate that an existing queue matches the canonical TODO")
    args = parser.parse_args(argv)
    todo_path = args.todo.resolve()
    expected = build_queue(args.template.resolve(), todo_path)
    output_path = args.output.resolve()
    if args.check:
        try:
            current = json.loads(output_path.read_text(encoding="utf-8"))
            if not isinstance(current, dict):
                raise QueueBuildError("queue root must be an object")
            validate_queue(current, expected)
        except (OSError, json.JSONDecodeError, QueueBuildError) as exc:
            raise SystemExit(f"queue check failed: {exc}")
        print(json.dumps({"status": "valid", "task_count": len(expected["tasks"]), "queue_revision": current["queue_revision"], "output": str(output_path)}))
        return 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(json.dumps(expected, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(output_path)
    print(json.dumps({"status": "built", "task_count": len(expected["tasks"]), "output": str(output_path)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
