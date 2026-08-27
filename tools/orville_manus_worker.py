#!/usr/bin/env python3
"""Persistent Orville roadmap worker for existing Manus task threads.

The worker normally monitors task IDs already recorded in
``.orville_manus_worker_state.json`` and, when a task stops, resumes that same
thread with the next actionable TODO item. The repository passed with ``--repo``
is attached to every continuation prompt and is the worker's only workspace.
Credentials are read from ``MANUS_API_KEY`` at runtime and never written to disk.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ID = "LEXzf7g37cAa2sJHx4PmMm"
CREATE_URL = "https://api.manus.ai/v2/task.create"
SEND_MESSAGE_URL = "https://api.manus.ai/v2/task.sendMessage"
DETAIL_URL = "https://api.manus.ai/v2/task.detail"
LOCK_FILE = ".orville_manus_worker.lock"
STATE_FILE = ".orville_manus_worker_state.json"
LOG_FILE = ".orville_manus_worker.log"
DEFAULT_MAX_ACTIVE_TASKS = 10
WORKER_TASK_NAMES = tuple(f"Worker Task {index}" for index in range(1, 11))


def playbook_for(repo: Path, item: str) -> str:
    """Build a self-contained continuation prompt for one repository TODO item."""
    repo_text = str(repo)
    return (
        f"Operate only on the attached repository directory: {repo_text}. "
        "Use the directory that contains the applicable TODO.md and control files. "
        "This is an existing Orville task thread; continue the current conversation "
        "instead of creating or delegating a new task. Execute exactly the selected "
        "TODO item below, using the repository's AGENTS.md, PROJECT.md, STATE.md, "
        "TASK_GRAPH.md, and TODO.md. Claim the item as in progress before substantial "
        "work, implement it, validate it with focused tests or documented checks, "
        "update project state and changelog when materially required, and mark it "
        "complete only after validation. After the selected item is implemented and validated, "
        "finish this task turn so the next worker cycle can automatically select the next "
        "eligible unchecked roadmap item. Do not duplicate work on items already marked "
        "[-] unless explicitly resuming an existing task. If the item is blocked or "
        "requires a user decision, leave it [!] with a concise blocker note and stop. "
        "Keep changes scoped to this one TODO item. When the repository is a Git worktree, "
        "create a focused branch before editing, commit only the item changes, run focused "
        "tests followed by compilation and broader regression checks when feasible, and open "
        "a pull request only after all required checks pass. If Git metadata or a remote is "
        "unavailable, do not fabricate a branch or pull request; record the blocker and still "
        "validate local changes. Mark TODO.md [x] only after code, tests, required state files, "
        "and changelog evidence are synchronized. External changes require the applicable "
        "explicit approval gate; never silently publish, delete, purchase, change accounts, "
        "or deploy. Report changed paths, validation, assumptions, and unresolved risks. Do "
        "not use external credentials, post content, make purchases, or perform destructive "
        "actions.\n\n"
        f"Selected TODO.md item: {item}"
    )


def log(repo: Path, message: str) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    with (repo / LOG_FILE).open("a", encoding="utf-8") as handle:
        handle.write(f"{timestamp} {message}\n")


def first_actionable_todo(project: Path, reserved: set[tuple[str, int]]) -> tuple[Path, int, str] | None:
    pattern = re.compile(r"^(\s*- \[ \] )(.*)$")
    todo_path = project / "TODO.md"
    if not todo_path.exists():
        return None
    for number, line in enumerate(todo_path.read_text(encoding="utf-8").splitlines(), 1):
        match = pattern.match(line)
        if match and (str(project), number) not in reserved:
            return project, number, match.group(2).strip()
    return None


def acquire_lock(repo: Path) -> bool:
    try:
        fd = os.open(repo / LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(f"pid={os.getpid()}\n")
        return True
    except FileExistsError:
        return False


def release_lock(repo: Path) -> None:
    try:
        (repo / LOCK_FILE).unlink()
    except FileNotFoundError:
        pass


def load_state(repo: Path) -> dict[str, Any]:
    path = repo / STATE_FILE
    if not path.exists():
        return {"active_tasks": []}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            return {"active_tasks": []}
        active = value.get("active_tasks", [])
        if not isinstance(active, list):
            active = []
        value["active_tasks"] = [item for item in active if isinstance(item, dict) and item.get("task_id")]
        # Backward-compatible migration: persisted threads are assigned to the
        # explicit Worker Task 1–10 slots. Additional task records are ignored.
        for index, record in enumerate(value["active_tasks"][: len(WORKER_TASK_NAMES)]):
            record.setdefault("worker_name", WORKER_TASK_NAMES[index])
        unfiltered_count = len(value["active_tasks"])
        value["active_tasks"] = [
            record for record in value["active_tasks"]
            if record.get("worker_name") in WORKER_TASK_NAMES
        ]
        value["_state_needs_save"] = len(value["active_tasks"]) != unfiltered_count
        legacy_id = value.get("active_task_id")
        if legacy_id and not any(str(item.get("task_id")) == str(legacy_id) for item in value["active_tasks"]):
            value["active_tasks"].insert(0, {
                "task_id": str(legacy_id),
                "todo_project": value.get("todo_project", str(repo)),
                "todo_line": value.get("todo_line"),
                "todo_item": value.get("todo_item", ""),
                "created_at": value.get("created_at", "legacy-state"),
            })
            log(repo, "migrated: legacy active_task_id into active_tasks")
        return value
    except (OSError, json.JSONDecodeError):
        log(repo, "warning: invalid state file; treating worker as uninitialized")
        return {"active_tasks": []}


def save_state(repo: Path, state: dict[str, Any]) -> None:
    path = repo / STATE_FILE
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def api_request(url: str, api_key: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"x-manus-api-key": api_key}, method="GET")
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))
    if not result.get("ok"):
        raise RuntimeError(f"Manus API returned an error: {result.get('error', 'unknown error')}")
    return result


def create_validation_task(repo: Path, api_key: str) -> str:
    """Create one harmless private task for the startup visibility gate."""
    payload = {
        "message": {
            "content": (
                "Startup validation only. Do not modify files, use connectors, or perform external side effects. "
                "Return a short acknowledgement and stop."
            )
        },
        "project_id": PROJECT_ID,
        "title": "Orville worker startup visibility validation",
        "interactive_mode": False,
        "share_visibility": "private",
    }
    request = urllib.request.Request(
        CREATE_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-manus-api-key": api_key},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))
    if not result.get("ok") or not isinstance(result.get("task_id"), str):
        raise RuntimeError(f"task creation validation failed: {result.get('error', 'missing task_id')}")
    return result["task_id"]


def validate_create_readability(
    repo: Path,
    api_key: str,
    *,
    retries: int = 3,
    interval_seconds: float = 5.0,
    create_fn: Any = create_validation_task,
    status_fn: Any = None,
    sleep_fn: Any = time.sleep,
) -> tuple[bool, str]:
    """Require a newly created task to become readable before scaling above three."""
    if retries < 1:
        raise ValueError("validation retries must be at least 1")
    if interval_seconds < 0:
        raise ValueError("validation interval must be non-negative")
    task_id = create_fn(repo, api_key)
    status_fn = status_fn or task_status
    for attempt in range(1, retries + 1):
        try:
            status = status_fn(task_id, api_key)
            return True, f"task_id={task_id} status={status or 'unknown'} attempts={attempt}"
        except urllib.error.HTTPError as exc:
            if exc.code != 404 or attempt == retries:
                return False, f"task_id={task_id} http_status={exc.code} attempts={attempt}"
            sleep_fn(interval_seconds)
        except (urllib.error.URLError, RuntimeError) as exc:
            if attempt == retries:
                return False, f"task_id={task_id} error={type(exc).__name__} attempts={attempt}"
            sleep_fn(interval_seconds)
    return False, f"task_id={task_id} attempts={retries}"


def resume_task(repo: Path, task_id: str, item: str, api_key: str) -> dict[str, Any]:
    """Resume an existing task thread with the next repository TODO item."""
    payload = {
        "task_id": task_id,
        "message": {"content": playbook_for(repo, item)},
    }
    request = urllib.request.Request(
        SEND_MESSAGE_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-manus-api-key": api_key},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))
    if not result.get("ok"):
        raise RuntimeError(f"Manus API returned an error: {result.get('error', 'unknown error')}")
    return result


def find_agent_status(value: Any) -> str | None:
    if isinstance(value, dict):
        if value.get("type") == "status_update" and isinstance(value.get("status_update"), dict):
            status = value["status_update"].get("agent_status")
            if isinstance(status, str):
                return status
        for child in value.values():
            status = find_agent_status(child)
            if status:
                return status
    elif isinstance(value, list):
        for child in value:
            status = find_agent_status(child)
            if status:
                return status
    return None


def task_status_url(task_id: str) -> str:
    """Return the exact status URL used for a task ID."""
    query = urllib.parse.urlencode({"task_id": task_id})
    return f"{DETAIL_URL}?{query}"


def task_status(task_id: str, api_key: str) -> str | None:
    """Return the current task status using the documented task.detail API."""
    result = api_request(task_status_url(task_id), api_key)
    task = result.get("task")
    if isinstance(task, dict) and isinstance(task.get("status"), str):
        return task["status"]
    raise RuntimeError("Manus task.detail response did not include task.status")


def run_once(
    repo: Path,
    dry_run: bool = False,
    max_active_tasks: int = DEFAULT_MAX_ACTIVE_TASKS,
    validate_create_readability: bool = False,
    validation_retries: int = 3,
    validation_interval_seconds: float = 5.0,
    enforce_validation_gate: bool = False,
) -> int:
    """Poll existing task threads, optionally validating scaled concurrency first."""
    if not 1 <= max_active_tasks <= 10:
        raise ValueError("max_active_tasks must be between 1 and 10")
    if not acquire_lock(repo):
        log(repo, "skip: another worker invocation holds the lock")
        return 0
    try:
        state = load_state(repo)
        state_needs_save = bool(state.pop("_state_needs_save", False))
        persisted_tasks = state["active_tasks"]
        active = [
            record for record in persisted_tasks
            if record.get("worker_name") in WORKER_TASK_NAMES
        ][:max_active_tasks]
        state_was_trimmed = state_needs_save or len(active) < len(persisted_tasks)
        if state_was_trimmed:
            log(repo, f"warning: limiting persisted active tasks to {max_active_tasks}")
        if dry_run:
            print(json.dumps({"action": "check_existing_tasks", "active_tasks": active, "max_active_tasks": max_active_tasks}, ensure_ascii=False))
            return 0
        if not active:
            log(repo, "idle: no existing task threads are configured; no new task created")
            return 0
        api_key = os.environ.get("MANUS_API_KEY", "")
        if not api_key:
            log(repo, "blocked: MANUS_API_KEY is not configured")
            return 2
        if max_active_tasks > 3 and enforce_validation_gate:
            if not validate_create_readability:
                log(repo, "blocked: concurrency above 3 requires --validate-create-readability")
                return 2
            valid, detail = validate_create_readability_gate(
                repo,
                api_key,
                retries=validation_retries,
                interval_seconds=validation_interval_seconds,
            )
            if not valid:
                log(repo, f"blocked: create-readability validation failed {detail}")
                return 2
            log(repo, f"create-readability validation passed {detail}")

        reserved = {(str(record.get("todo_project")), int(record["todo_line"])) for record in active if record.get("todo_project") and record.get("todo_line")}
        updated = False
        for record in active:
            task_id = str(record["task_id"])
            try:
                status = task_status(task_id, api_key)
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    log(repo, f"error: task status not found task_id={task_id} url={task_status_url(task_id)} http_status=404; continuing other slots")
                    continue
                raise
            if status != "stopped":
                log(repo, f"wait: existing_task_id={task_id} status={status or 'unknown'}")
                continue
            project = Path(str(record.get("todo_project") or repo))
            selected = first_actionable_todo(project, reserved)
            if selected is None:
                log(repo, f"idle: existing_task_id={task_id} has no unchecked actionable TODO item")
                continue
            todo_project, line_number, item = selected
            resume_task(repo, task_id, item, api_key)
            record.update({
                "worker_name": record.get("worker_name", WORKER_TASK_NAMES[active.index(record)]),
                "todo_project": str(todo_project),
                "todo_line": line_number,
                "todo_item": item,
                "resumed_at": datetime.now(timezone.utc).isoformat(),
            })
            reserved.add((str(todo_project), line_number))
            updated = True
            log(repo, f"resumed: existing_task_id={task_id} line={line_number}")
        if updated or state_was_trimmed:
            state["active_tasks"] = active
            save_state(repo, state)
        return 0
    except (OSError, UnicodeError, urllib.error.URLError, json.JSONDecodeError, RuntimeError, ValueError) as exc:
        log(repo, f"error: {type(exc).__name__}: {exc}")
        return 1
    finally:
        release_lock(repo)


def validate_create_readability_gate(
    repo: Path,
    api_key: str,
    *,
    retries: int = 3,
    interval_seconds: float = 5.0,
) -> tuple[bool, str]:
    """Run the creation/readability gate using the production API functions."""
    return validate_create_readability(
        repo,
        api_key,
        retries=retries,
        interval_seconds=interval_seconds,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Resume existing Orville Manus task threads for TODO work.")
    parser.add_argument("--repo", type=Path, default=Path(os.environ.get("ORVILLE_REPO", Path(__file__).resolve().parents[1])), help="Orville repository root; scheduled invocations should pass the absolute repo path")
    parser.add_argument("--max-active", type=int, default=DEFAULT_MAX_ACTIVE_TASKS, choices=range(1, 11), help="maximum existing task threads to monitor (1-10)")
    parser.add_argument("--validate-create-readability", action="store_true", help="before max-active above 3, create a harmless private validation task and require task.detail readability")
    parser.add_argument("--validation-retries", type=int, default=3, help="creation-readability validation attempts (default: 3)")
    parser.add_argument("--validation-interval", type=float, default=5.0, help="seconds between creation-readability attempts (default: 5)")
    parser.add_argument("--dry-run", action="store_true", help="inspect existing task state without network calls")
    args = parser.parse_args()
    repo = args.repo.expanduser().resolve()
    if not (repo / "TODO.md").is_file():
        parser.error(f"TODO.md not found under repository path: {repo}")
    return run_once(
        repo,
        dry_run=args.dry_run,
        max_active_tasks=args.max_active,
        validate_create_readability=args.validate_create_readability,
        validation_retries=args.validation_retries,
        validation_interval_seconds=args.validation_interval,
        enforce_validation_gate=args.max_active > 3 and not args.dry_run,
    )


if __name__ == "__main__":
    raise SystemExit(main())
