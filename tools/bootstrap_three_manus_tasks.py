#!/usr/bin/env python3
"""Create exactly three private Manus tasks and bind them to the Orville worker.

This script is intended to run once on the persistent worker host. It does not
run from the recurring worker service. The API key is read from MANUS_API_KEY
and is never written to state, manifests, logs, or error output.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CREATE_URL = "https://api.manus.ai/v2/task.create"
DETAIL_URL = "https://api.manus.ai/v2/task.detail"
PROJECT_ID = "LEXzf7g37cAa2sJHx4PmMm"
SLOT_NAMES = ("Worker Task 1", "Worker Task 2", "Worker Task 3")
TASK_COUNT = 3

TASK_PROMPTS = (
    (
        "Resolve Orville persistent SQLite provenance",
        """Work only in the attached Orville repository. Determine the actual persistent SQLite deployment path from configuration and runtime evidence; classify /tmp/orville.db and the tracked data/.orville sidecars; and update provenance documentation and tests where appropriate. Do not delete, move, overwrite, checkpoint, archive, upload, publish, deploy, purchase, change accounts, send messages, or modify external systems. If an external or destructive action is proposed, stop and record the exact approval needed. Run focused validation, synchronize repository evidence, and report changed paths, validation, assumptions, and unresolved risks. Continue only the selected TODO item and do not create or delegate additional tasks.""",
    ),
    (
        "Close walkthrough-video archival evidence",
        """Work only in the attached Orville repository and reviewed local artifact locations. Verify the documented walkthrough-video archival claim, locate the source or an archived copy if it exists, and reconcile the compliance note and TODO evidence. If the video is absent, document the evidence searched, impact, owner, and precise closure criteria; do not fabricate, regenerate, upload, publish, or delete any artifact. Do not contact external parties or modify external systems. Run documentation checks, synchronize repository evidence, and report changed paths, validation, assumptions, and unresolved risks. Continue only the selected TODO item and do not create or delegate additional tasks.""",
    ),
    (
        "Review remaining Orville roadmap controls",
        """Work only in the attached Orville repository. Audit the next dependency-ready unchecked roadmap control after the completed regression and Provider/MCP work. Select exactly one repository-scoped control, implement the smallest safe change, and add focused tests. Do not publish, deploy, merge, delete, purchase, change accounts, send messages, or broaden permissions. If prerequisites are missing, mark the item blocked rather than substituting another task. Run focused validation, synchronize repository evidence, and report changed paths, validation, assumptions, and unresolved risks. Continue only the selected TODO item and do not create or delegate additional tasks.""",
    ),
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def die(message: str, code: int = 2) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def api_json(url: str, api_key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    headers = {"x-manus-api-key": api_key, "Accept": "application/json"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
    else:
        request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Do not print response bodies: they may contain sensitive provider data.
        raise RuntimeError(f"Manus API HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Manus API {type(exc).__name__}") from exc
    if body.get("ok") is not True:
        error = body.get("error")
        code = error.get("code", "unknown") if isinstance(error, dict) else "unknown"
        raise RuntimeError(f"Manus API returned {code}")
    return body


def create_task(api_key: str, title: str, content: str) -> str:
    body = api_json(
        CREATE_URL,
        api_key,
        {
            "message": {"content": content},
            "project_id": PROJECT_ID,
            "title": title,
            "interactive_mode": False,
            "share_visibility": "private",
        },
    )
    task_id = body.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        raise RuntimeError("task.create response did not contain task_id")
    return task_id


def verify_task(api_key: str, task_id: str) -> str:
    query = urllib.parse.urlencode({"task_id": task_id})
    body = api_json(f"{DETAIL_URL}?{query}", api_key)
    task = body.get("task")
    if not isinstance(task, dict):
        raise RuntimeError("task.detail response did not contain task")
    status = task.get("status")
    if not isinstance(status, str) or not status:
        raise RuntimeError("task.detail response did not contain task.status")
    return status


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        die(f"Cannot read JSON record {path}: {type(exc).__name__}")
    if not isinstance(value, dict):
        die(f"JSON record is not an object: {path}")
    return value


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def build_state(repo: Path, task_ids: list[str], statuses: list[str]) -> dict[str, Any]:
    verified = now()
    return {
        "active_tasks": [
            {
                "worker_name": slot,
                "task_id": task_id,
                "todo_project": str(repo),
                "todo_line": None,
                "todo_item": "auto-selected from TODO.md",
                "manus_status": status,
                "verified_at": verified,
                "created_by": "bootstrap_three_manus_tasks.py",
            }
            for slot, task_id, status in zip(SLOT_NAMES, task_ids, statuses)
        ],
        "paused": False,
        "bootstrap_verified_at": verified,
        "allowlist_mode": "exactly-three-task-ids",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--state", type=Path, help="worker state path; defaults to <repo>/.orville_manus_worker_state.json")
    parser.add_argument("--manifest", type=Path, default=Path("/var/lib/orville/three_task_bootstrap.json"))
    parser.add_argument("--resume-partial", action="store_true", help="resume a previously recorded partial creation; never creates a fourth task")
    parser.add_argument(
        "--task-id",
        dest="task_ids",
        action="append",
        help="bind an existing Manus task ID; repeat exactly three times to skip task creation",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = args.repo.expanduser().resolve()
    state_path = (args.state or (repo / ".orville_manus_worker_state.json")).expanduser().resolve()
    manifest_path = args.manifest.expanduser().resolve()

    if not (repo / "TODO.md").is_file():
        die(f"TODO.md not found under repository: {repo}")
    api_key = os.environ.get("MANUS_API_KEY", "")
    if not api_key:
        die("MANUS_API_KEY is not available to this process")

    existing_state = read_json(state_path)
    if existing_state and existing_state.get("active_tasks"):
        die(f"worker state already contains active tasks: {state_path}; refusing to create duplicates")

    supplied_task_ids = args.task_ids or []
    if supplied_task_ids:
        if len(supplied_task_ids) != TASK_COUNT:
            die(f"--task-id must be supplied exactly {TASK_COUNT} times")
        if len(set(supplied_task_ids)) != TASK_COUNT:
            die("--task-id values must be unique")

    manifest = read_json(manifest_path)
    task_ids: list[str] = list(supplied_task_ids)
    if task_ids and manifest:
        manifest_ids = manifest.get("task_ids")
        if manifest_ids != task_ids:
            die(f"provided task IDs do not match bootstrap manifest: {manifest_path}")

    if manifest:
        raw_ids = manifest.get("task_ids")
        if not isinstance(raw_ids, list) or not all(isinstance(item, str) and item for item in raw_ids):
            die(f"bootstrap manifest is invalid: {manifest_path}")
        if not task_ids:
            task_ids = list(raw_ids)
        if len(task_ids) == TASK_COUNT:
            print("three task IDs are configured; verifying without creating new tasks")
        elif not args.resume_partial:
            die(f"partial bootstrap exists at {manifest_path}; use --resume-partial after review")
        elif len(task_ids) > TASK_COUNT:
            die("bootstrap manifest contains more than three task IDs")

    try:
        while len(task_ids) < TASK_COUNT:
            index = len(task_ids)
            task_id = create_task(api_key, *TASK_PROMPTS[index])
            task_ids.append(task_id)
            atomic_write(
                manifest_path,
                {
                    "task_ids": task_ids,
                    "created_at": manifest.get("created_at", now()) if manifest else now(),
                    "count": len(task_ids),
                },
            )

            print(f"created task {index + 1}/{TASK_COUNT}: {task_id}")

        statuses = [verify_task(api_key, task_id) for task_id in task_ids]
        atomic_write(
            manifest_path,
            {
                "task_ids": task_ids,
                "statuses": statuses,
                "verified_at": now(),
                "count": TASK_COUNT,
                "source": "provided-existing-task-ids" if supplied_task_ids else "created-by-bootstrap",
            },
        )

        atomic_write(state_path, build_state(repo, task_ids, statuses))
    except RuntimeError as exc:
        die(f"bootstrap stopped safely: {exc}", 3)

    print(f"verified exactly {TASK_COUNT} private tasks and populated {state_path}")
    for slot, task_id, status in zip(SLOT_NAMES, task_ids, statuses):
        print(f"{slot}: {task_id} status={status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
