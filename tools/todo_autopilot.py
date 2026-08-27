#!/usr/bin/env python3
"""Guarded autonomous TODO completion for standalone Orville repositories.

The worker processes one unchecked TODO item at a time. It creates an isolated
branch, invokes a configured editing agent, runs all configured validation
commands, and only then updates the checkbox and commits the result. Pushes,
pull requests, and other external actions are disabled unless explicitly
approved for the current invocation.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

CHECKBOX = re.compile(r"^(?P<prefix>\s*- \[)(?P<state>[ xX!-])(?P<suffix>\] )(?P<item>.*)$")
DEFAULT_VALIDATION = ("python -m compileall -q orville_core tools", "python -m pytest -q")
STATE_NAME = ".orville_todo_autopilot.json"
LOCK_NAME = ".orville_todo_autopilot.lock"


@dataclass(frozen=True)
class TodoItem:
    path: Path
    line_number: int
    text: str


class AutomationError(RuntimeError):
    """Raised when a guarded automation step cannot proceed safely."""


def run(command: str, cwd: Path, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a shell command with captured output and a bounded text result."""
    result = subprocess.run(command, cwd=cwd, shell=True, text=True, capture_output=True)
    if check and result.returncode != 0:
        detail = (result.stdout + "\n" + result.stderr).strip()[-4000:]
        raise AutomationError(f"command failed ({result.returncode}): {command}\n{detail}")
    return result


def run_argv(command: Sequence[str], cwd: Path, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run an executable without shell quoting, for Git and other trusted commands."""
    result = subprocess.run(list(command), cwd=cwd, text=True, capture_output=True)
    if check and result.returncode != 0:
        detail = (result.stdout + "\n" + result.stderr).strip()[-4000:]
        raise AutomationError(f"command failed ({result.returncode}): {' '.join(command)}\n{detail}")
    return result


def require_git_repo(repo: Path) -> None:
    if run("git rev-parse --show-toplevel", repo, check=False).returncode != 0:
        raise AutomationError(f"repository is not a Git worktree: {repo}")


def find_todos(repo: Path) -> list[TodoItem]:
    """Return unchecked TODO entries, excluding generated and temporary paths."""
    items: list[TodoItem] = []
    for path in sorted(repo.rglob("TODO.md")):
        if any(part in {".git", "tmp", "__pycache__"} for part in path.relative_to(repo).parts):
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            match = CHECKBOX.match(line)
            if match and match.group("state") == " ":
                items.append(TodoItem(path, number, match.group("item").strip()))
    return items


def select_item(repo: Path, requested_line: int | None = None) -> TodoItem | None:
    items = find_todos(repo)
    if requested_line is not None:
        items = [item for item in items if item.path == repo / "TODO.md" and item.line_number == requested_line]
    return items[0] if items else None


def mark_complete(item: TodoItem) -> None:
    lines = item.path.read_text(encoding="utf-8").splitlines(keepends=True)
    if not 1 <= item.line_number <= len(lines):
        raise AutomationError("TODO line moved during automation; refusing to mark complete")
    match = CHECKBOX.match(lines[item.line_number - 1].rstrip("\r\n"))
    if not match or match.group("state") != " ":
        raise AutomationError("TODO state changed during automation; refusing to overwrite it")
    ending = "\r\n" if lines[item.line_number - 1].endswith("\r\n") else "\n"
    lines[item.line_number - 1] = f"{match.group('prefix')}x{match.group('suffix')}{match.group('item')}{ending}"
    temporary = item.path.with_suffix(item.path.suffix + ".tmp")
    temporary.write_text("".join(lines), encoding="utf-8", newline="")
    temporary.replace(item.path)


def load_state(repo: Path) -> dict:
    path = repo / STATE_NAME
    if not path.exists():
        return {"runs": []}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AutomationError(f"invalid state file: {path}: {exc}") from exc
    return value if isinstance(value, dict) else {"runs": []}


def save_state(repo: Path, state: dict) -> None:
    path = repo / STATE_NAME
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def acquire_lock(repo: Path) -> None:
    try:
        fd = os.open(repo / LOCK_NAME, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
    except FileExistsError as exc:
        raise AutomationError(f"another TODO automation run owns {repo / LOCK_NAME}") from exc


def release_lock(repo: Path) -> None:
    try:
        (repo / LOCK_NAME).unlink()
    except FileNotFoundError:
        pass


def safe_branch_name(text: str, line_number: int) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:50]
    return f"automation/todo-{line_number}-{slug or 'item'}"


def approval_granted(args: argparse.Namespace) -> bool:
    return bool(args.approve and os.environ.get("ORVILLE_AUTOMATION_APPROVED") == "1")


def editing_prompt(repo: Path, item: str, *, allow_all_edits: bool) -> str:
    """Build the agent prompt while keeping TODO ownership with this worker."""
    policy = (
        "You may edit any repository file needed to complete the item, including source, tests, configuration, documentation, and control files, "
        "but do not edit TODO.md or credentials, and do not perform external side effects."
        if allow_all_edits
        else "Implement code and tests only; do not edit TODO.md or control files."
    )
    return f"Complete exactly this TODO item in {repo}: {item}. Follow AGENTS.md. {policy}"


def external_action(args: argparse.Namespace, command: str, repo: Path) -> None:
    if not approval_granted(args):
        raise AutomationError("external action blocked: pass --approve and set ORVILLE_AUTOMATION_APPROVED=1")
    run(command, repo)


def process_one(repo: Path, args: argparse.Namespace) -> dict:
    item = select_item(repo, args.todo_line)
    if item is None:
        return {"status": "idle", "message": "no unchecked TODO item"}
    original_branch = run("git branch --show-current", repo).stdout.strip()
    branch = args.branch or safe_branch_name(item.text, item.line_number)
    if run(f"git show-ref --verify --quiet refs/heads/{shlex.quote(branch)}", repo, check=False).returncode == 0:
        raise AutomationError(f"branch already exists; refusing to reuse it: {branch}")
    run(f"git switch -c {shlex.quote(branch)}", repo)
    record = {"started_at": datetime.now(timezone.utc).isoformat(), "todo": item.text, "line": item.line_number, "branch": branch}
    succeeded = False
    try:
        agent = args.agent or os.environ.get("ORVILLE_TODO_AGENT_COMMAND")
        if not agent:
            raise AutomationError("no editor configured; use --agent or ORVILLE_TODO_AGENT_COMMAND")
        allow_all_edits = getattr(args, "allow_all_edits", False) or os.environ.get("ORVILLE_ALLOW_ALL_EDITS") == "1"
        prompt = editing_prompt(repo, item.text, allow_all_edits=allow_all_edits)
        run(agent.replace("{prompt}", shlex.quote(prompt)).replace("{repo}", shlex.quote(str(repo))), repo)
        validations = args.validate or list(DEFAULT_VALIDATION)
        for command in validations:
            run(command, repo)
        mark_complete(item)
        run("git add -A", repo)
        run_argv(["git", "commit", "-m", "todo: complete " + item.text[:60]], repo)
        if args.push:
            external_action(args, f"git push -u origin {shlex.quote(branch)}", repo)
        if args.pr:
            external_action(args, f"gh pr create --fill --head {shlex.quote(branch)}", repo)
        record["status"] = "completed"
        succeeded = True
        return record
    except Exception as exc:
        record.update({"status": "failed", "error": str(exc)})
        raise
    finally:
        state = load_state(repo)
        state.setdefault("runs", []).append(record)
        state["runs"] = state["runs"][-100:]
        save_state(repo, state)
        if succeeded and original_branch:
            run(f"git switch {shlex.quote(original_branch)}", repo, check=False)


def preview(repo: Path, args: argparse.Namespace) -> dict:
    """Return the next TODO action without requiring Git or invoking commands."""
    item = select_item(repo, args.todo_line)
    if item is None:
        return {"status": "idle", "message": "no unchecked TODO item"}
    branch = args.branch or safe_branch_name(item.text, item.line_number)
    return {
        "status": "preview",
        "todo_file": str(item.path),
        "todo_line": item.line_number,
        "todo_item": item.text,
        "would_create_branch": branch,
        "agent_configured": bool(args.agent or os.environ.get("ORVILLE_TODO_AGENT_COMMAND")),
        "allow_all_edits": bool(getattr(args, "allow_all_edits", False) or os.environ.get("ORVILLE_ALLOW_ALL_EDITS") == "1"),
        "validation": args.validate or list(DEFAULT_VALIDATION),
        "external_actions": {"push": bool(args.push), "pull_request": bool(args.pr)},
        "changes_executed": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--dry-run", action="store_true", help="preview the first TODO without requiring Git or making changes")
    parser.add_argument("--agent", help="editing command; use {prompt} and {repo} placeholders")
    parser.add_argument("--allow-all-edits", action="store_true", help="explicitly allow the agent to edit any repository file except TODO.md and credentials")
    parser.add_argument("--validate", action="append", help="validation command; repeat for multiple commands")
    parser.add_argument("--todo-line", type=int)
    parser.add_argument("--branch")
    parser.add_argument("--continuous", action="store_true", help="repeat after success until no unchecked TODO remains")
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--push", action="store_true")
    parser.add_argument("--pr", action="store_true")
    parser.add_argument("--approve", action="store_true", help="acknowledge that configured external actions are intended")
    args = parser.parse_args(argv)
    repo = args.repo.expanduser().resolve()
    if args.dry_run:
        print(json.dumps(preview(repo, args), ensure_ascii=False))
        return 0
    require_git_repo(repo)
    if args.push or args.pr:
        if not approval_granted(args):
            raise SystemExit("external actions require --approve and ORVILLE_AUTOMATION_APPROVED=1")
    acquire_lock(repo)
    try:
        while True:
            result = process_one(repo, args)
            print(json.dumps(result, ensure_ascii=False))
            if result.get("status") != "completed" or not args.continuous:
                return 0 if result.get("status") in {"completed", "idle"} else 1
            time.sleep(max(0.0, args.interval))
    except AutomationError as exc:
        print(f"automation blocked: {exc}", file=sys.stderr)
        return 1
    finally:
        release_lock(repo)


if __name__ == "__main__":
    raise SystemExit(main())


# NOTE: assignment expressions above intentionally cap generated branch/commit slugs.
# They remain Python 3.10-compatible and avoid unbounded branch-name growth.
