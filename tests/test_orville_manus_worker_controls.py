import importlib.util
import json
import os
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


MODULE_PATH = Path(__file__).parents[1] / "tools" / "orville_manus_worker.py"
SPEC = importlib.util.spec_from_file_location("orville_manus_worker_controls", MODULE_PATH)
assert SPEC and SPEC.loader
worker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(worker)


def make_repo(todo: str = "- [ ] one\n") -> tuple[TemporaryDirectory, Path]:
    directory = TemporaryDirectory()
    repo = Path(directory.name)
    (repo / "TODO.md").write_text(todo, encoding="utf-8")
    return directory, repo


def test_pause_and_resume_are_atomic_and_block_dispatch() -> None:
    directory, repo = make_repo()
    try:
        worker.save_state(repo, {"active_tasks": [{"task_id": "task-1"}]})
        worker.set_paused(repo, True)
        with patch.dict("os.environ", {"MANUS_API_KEY": "synthetic"}), patch.object(worker, "task_status") as status:
            assert worker.run_once(repo, max_active_tasks=3) == 0
        status.assert_not_called()
        assert json.loads((repo / worker.STATE_FILE).read_text()) ["paused"] is True
        worker.set_paused(repo, False)
        assert json.loads((repo / worker.STATE_FILE).read_text())["paused"] is False
    finally:
        directory.cleanup()


def test_retry_budget_records_review_after_exhaustion() -> None:
    directory, repo = make_repo()
    try:
        worker.save_state(repo, {"active_tasks": [{"worker_name": "Worker Task 1", "task_id": "task-1", "todo_project": str(repo)}]})
        failure = RuntimeError("transport failed")
        with patch.dict("os.environ", {"MANUS_API_KEY": "synthetic"}), patch.object(worker, "task_status", return_value="stopped"), patch.object(worker, "resume_task", side_effect=failure):
            assert worker.run_once(repo, max_active_tasks=1, max_retries=0) == 0
        saved = json.loads((repo / worker.STATE_FILE).read_text())
        record = saved["active_tasks"][0]
        assert record["retry_count"] == 1
        assert record["status"] == "review"
    finally:
        directory.cleanup()


def test_lock_records_heartbeat_and_recovers_dead_stale_owner() -> None:
    directory, repo = make_repo()
    try:
        lock = repo / worker.LOCK_FILE
        lock.write_text("pid=999999\nrun_id=old\nacquired_at=1\nheartbeat=1\nlease_seconds=1\n", encoding="utf-8")
        with patch.object(worker, "_pid_alive", return_value=False):
            assert worker.acquire_lock(repo, lease_seconds=1) is True
        text = lock.read_text(encoding="utf-8")
        assert "pid=" in text
        assert "heartbeat=" in text
        assert "run_id=" in text
        worker.touch_lock(repo)
        assert "heartbeat=" in lock.read_text(encoding="utf-8")
        worker.release_lock(repo)
    finally:
        directory.cleanup()


def test_status_is_redacted_and_does_not_require_network() -> None:
    directory, repo = make_repo()
    try:
        worker.save_state(repo, {"paused": True, "active_tasks": [{"worker_name": "Worker Task 1", "task_id": "task-1", "retry_count": 1, "last_heartbeat": "now", "credential": "secret"}]})
        status = worker.worker_status(repo)
        assert status["paused"] is True
        assert status["active_task_count"] == 1
        assert "credential" not in json.dumps(status)
    finally:
        directory.cleanup()
