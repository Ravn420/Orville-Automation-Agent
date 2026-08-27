"""Regression tests for the guarded canonical TODO queue builder."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "build_todo_queue.py"
SPEC = importlib.util.spec_from_file_location("build_todo_queue", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _write_template(path: Path) -> None:
    path.write_text(
        json.dumps({"schema_version": 1, "queue_revision": 0, "tasks": [], "audit": []}),
        encoding="utf-8",
    )


def test_parse_todos_recognizes_markers_anywhere_and_skips_completed(tmp_path: Path) -> None:
    todo_path = tmp_path / "TODO.md"
    todo_path.write_text(
        "## Current\n"
        "- [ ] First open task. <!-- task-id:TODO-aaaaaaaaaaaa -->\n"
        "- [!] Blocked task. <!-- task-id:TODO-bbbbbbbbbbbb --> Blocked: awaiting approval.\n"
        "- [-] Active task. <!-- task-id:TODO-cccccccccccc -->\n"
        "- [x] Completed task. <!-- task-id:TODO-dddddddddddd -->\n",
        encoding="utf-8",
    )

    tasks = MODULE.parse_todos(todo_path)

    assert [task["id"] for task in tasks] == [
        "TODO-aaaaaaaaaaaa",
        "TODO-bbbbbbbbbbbb",
        "TODO-cccccccccccc",
    ]
    assert [task["status"] for task in tasks] == ["backlog", "blocked", "review"]
    assert tasks[1]["title"].endswith("Blocked: awaiting approval.")
    assert "task-id" not in tasks[1]["title"]


def test_validate_queue_accepts_guarded_planning_revision(tmp_path: Path) -> None:
    todo_path = tmp_path / "TODO.md"
    todo_path.write_text(
        "## Current\n- [ ] Define a bounded local policy. <!-- task-id:TODO-eeeeeeeeeeee -->\n",
        encoding="utf-8",
    )
    template_path = tmp_path / "template.json"
    _write_template(template_path)
    expected = MODULE.build_queue(template_path, todo_path)
    current = json.loads(json.dumps(expected))
    current["queue_revision"] = 2
    current["tasks"][0]["status"] = "ready"
    current["tasks"][0]["title"] = "Define policy boundaries"
    current["tasks"][0]["priority"] = 900
    current["tasks"][0]["revision"] = 2
    current["audit"].append({"action": "edited", "reason": "Scoped a local task."})

    MODULE.validate_queue(current, expected)


def test_parse_todos_rejects_nonterminal_record_without_one_marker(tmp_path: Path) -> None:
    todo_path = tmp_path / "TODO.md"
    todo_path.write_text("- [ ] Missing identifier.\n", encoding="utf-8")

    try:
        MODULE.parse_todos(todo_path)
    except MODULE.QueueBuildError as exc:
        assert "exactly one stable task ID" in str(exc)
    else:
        raise AssertionError("queue builder accepted a non-terminal TODO without a stable ID")
