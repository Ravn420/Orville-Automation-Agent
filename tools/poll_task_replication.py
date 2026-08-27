#!/usr/bin/env python3
"""Poll a newly created Manus task until it becomes readable or times out.

The script is intentionally read-only: it calls task.detail and never creates,
updates, stops, or sends messages to a task. Credentials are read from the
named environment variable and are never printed or persisted.
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
from dataclasses import dataclass
from typing import Callable

DETAIL_URL = "https://api.manus.ai/v2/task.detail"
TASK_ID_PATTERN = re.compile(r"^[A-Za-z0-9]{22}$")
DEFAULT_INTERVAL_SECONDS = 5.0
DEFAULT_TIMEOUT_SECONDS = 300.0
RETRYABLE_HTTP_CODES = frozenset({404, 408, 425, 429, 500, 502, 503, 504})


@dataclass(frozen=True)
class PollResult:
    """Outcome of a bounded task visibility poll."""

    task_id: str
    outcome: str
    attempts: int
    elapsed_seconds: float
    http_status: int | None = None
    task_status: str | None = None
    error_code: str | None = None


def validate_task_id(task_id: str) -> None:
    """Reject malformed IDs before making a network request."""
    if not TASK_ID_PATTERN.fullmatch(task_id):
        raise ValueError("task_id must be a 22-character alphanumeric Manus task ID")


def detail_request(task_id: str, api_key: str) -> tuple[int, dict[str, object]]:
    """Read task.detail and return its HTTP status and parsed JSON payload."""
    query = urllib.parse.urlencode({"task_id": task_id})
    request = urllib.request.Request(
        f"{DETAIL_URL}?{query}",
        headers={"x-manus-api-key": api_key},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return response.status, payload
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"error": {"code": "http_error", "message": "non-JSON response"}}
        return exc.code, payload if isinstance(payload, dict) else {}


def poll_until_visible(
    task_id: str,
    api_key: str,
    *,
    interval_seconds: float = DEFAULT_INTERVAL_SECONDS,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    request_fn: Callable[[str, str], tuple[int, dict[str, object]]] = detail_request,
    sleep_fn: Callable[[float], None] = time.sleep,
    monotonic_fn: Callable[[], float] = time.monotonic,
) -> PollResult:
    """Poll task.detail until readable, terminal-error, or bounded timeout."""
    validate_task_id(task_id)
    if interval_seconds < 0:
        raise ValueError("interval_seconds must be non-negative")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero")

    started = monotonic_fn()
    attempts = 0
    while True:
        attempts += 1
        status, payload = request_fn(task_id, api_key)
        elapsed = max(0.0, monotonic_fn() - started)
        if status == 200 and payload.get("ok"):
            task = payload.get("task")
            task_status = task.get("status") if isinstance(task, dict) else None
            return PollResult(task_id, "visible", attempts, elapsed, status, task_status)

        error = payload.get("error") if isinstance(payload, dict) else None
        error_code = error.get("code") if isinstance(error, dict) else None
        if status not in RETRYABLE_HTTP_CODES:
            return PollResult(task_id, "terminal_error", attempts, elapsed, status, error_code=error_code)
        if elapsed >= timeout_seconds:
            return PollResult(task_id, "timeout", attempts, elapsed, status, error_code=error_code)
        remaining = timeout_seconds - elapsed
        sleep_fn(min(interval_seconds, remaining))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Poll a newly created Manus task until task.detail stops returning 404."
    )
    parser.add_argument("task_id", help="22-character alphanumeric Manus task ID")
    parser.add_argument(
        "--interval", type=float, default=DEFAULT_INTERVAL_SECONDS,
        help="seconds between attempts (default: 5)",
    )
    parser.add_argument(
        "--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS,
        help="maximum total wait in seconds (default: 300)",
    )
    parser.add_argument(
        "--api-key-env", default="MANUS_API_KEY",
        help="environment variable containing the API key (default: MANUS_API_KEY)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        validate_task_id(args.task_id)
        api_key = os.environ.get(args.api_key_env, "")
        if not api_key:
            print(f"credential_missing environment={args.api_key_env}", file=sys.stderr)
            return 2
        result = poll_until_visible(
            args.task_id,
            api_key,
            interval_seconds=args.interval,
            timeout_seconds=args.timeout,
        )
    except (ValueError, OSError, urllib.error.URLError) as exc:
        print(f"poll_error type={type(exc).__name__} message={exc}", file=sys.stderr)
        return 2

    fields = {
        "task_id": result.task_id,
        "outcome": result.outcome,
        "attempts": result.attempts,
        "elapsed_seconds": round(result.elapsed_seconds, 3),
        "http_status": result.http_status,
    }
    if result.task_status:
        fields["task_status"] = result.task_status
    if result.error_code:
        fields["error_code"] = result.error_code
    print(json.dumps(fields, sort_keys=True))
    return 0 if result.outcome == "visible" else 1


if __name__ == "__main__":
    raise SystemExit(main())
