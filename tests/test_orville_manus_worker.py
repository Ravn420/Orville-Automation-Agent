from __future__ import annotations

import importlib.util
import json
import urllib.error
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


MODULE_PATH = Path(__file__).parents[1] / "tools" / "orville_manus_worker.py"
SPEC = importlib.util.spec_from_file_location("orville_manus_worker", MODULE_PATH)
assert SPEC and SPEC.loader
worker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(worker)


def make_repo(todo: str) -> tuple[TemporaryDirectory, Path]:
    directory = TemporaryDirectory()
    repo = Path(directory.name)
    (repo / "TODO.md").write_text(todo, encoding="utf-8")
    return directory, repo


def test_playbook_enforces_autonomous_completion_gates() -> None:
    prompt = worker.playbook_for(Path("C:/Orville"), "one item")
    assert "Claim the item as in progress" in prompt
    assert "next worker cycle can automatically select the next" in prompt
    assert "create a focused branch" in prompt
    assert "run focused tests" in prompt
    assert "open a pull request only after all required checks pass" in prompt
    assert "Mark TODO.md [x] only after code, tests, required state files, and changelog evidence are synchronized" in prompt
    assert "explicit approval gate" in prompt


def test_task_status_uses_task_detail_contract() -> None:
    with patch.object(worker, "api_request", return_value={"ok": True, "task": {"status": "running"}}) as request:
        assert worker.task_status("task-123", "synthetic-test-key") == "running"
    request.assert_called_once_with("https://api.manus.ai/v2/task.detail?task_id=task-123", "synthetic-test-key")


def test_resume_task_posts_to_existing_thread_and_binds_repo() -> None:
    class Response:
        def __enter__(self) -> "Response":
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return b'{"ok": true, "task_id": "existing"}'

    with patch.object(worker.urllib.request, "urlopen", return_value=Response()) as urlopen:
        assert worker.resume_task(Path("C:/Orville"), "existing", "one", "synthetic-test-key")["task_id"] == "existing"
    request = urlopen.call_args.args[0]
    assert request.full_url == worker.SEND_MESSAGE_URL
    payload = json.loads(request.data.decode("utf-8"))
    assert payload["task_id"] == "existing"
    assert "Orville" in payload["message"]["content"]
    assert "Selected TODO.md item: one" in payload["message"]["content"]


def test_run_once_logs_404_task_id_and_continues_other_slots() -> None:
    directory, repo = make_repo("- [ ] one\n")
    try:
        worker.save_state(repo, {"active_tasks": [
            {"worker_name": "Worker Task 1", "task_id": "missing", "todo_project": str(repo), "todo_line": 1, "todo_item": "one"},
            {"worker_name": "Worker Task 2", "task_id": "healthy", "todo_project": str(repo), "todo_line": 1, "todo_item": "one"},
        ]})
        missing_url = worker.task_status_url("missing")
        def status(task_id: str, _key: str) -> str:
            if task_id == "missing":
                raise urllib.error.HTTPError(missing_url, 404, "Not Found", None, None)
            return "running"
        with patch.dict("os.environ", {"MANUS_API_KEY": "synthetic-test-key"}), patch.object(worker, "task_status", side_effect=status), patch.object(worker, "log") as log:
            assert worker.run_once(repo, max_active_tasks=3) == 0
        messages = [call.args[1] for call in log.call_args_list]
        assert any("task_id=missing" in message and missing_url in message and "continuing other slots" in message for message in messages)
        assert any("healthy" in message and "status=running" in message for message in messages)
    finally:
        directory.cleanup()


def test_run_once_resumes_stopped_existing_task_without_creating() -> None:
    directory, repo = make_repo("- [ ] one\n- [ ] two\n")
    try:
        resumed: list[tuple[str, str]] = []
        worker.save_state(repo, {"active_tasks": [
            {"task_id": "existing-1", "todo_project": str(repo), "todo_line": 1, "todo_item": "one"},
        ]})
        with patch.dict("os.environ", {"MANUS_API_KEY": "synthetic-test-key"}), patch.object(worker, "task_status", return_value="stopped"), patch.object(worker, "resume_task", side_effect=lambda _repo, task_id, item, _key: resumed.append((task_id, item))):
            assert worker.run_once(repo, max_active_tasks=3) == 0
        saved = json.loads((repo / worker.STATE_FILE).read_text(encoding="utf-8"))
        assert [record["task_id"] for record in saved["active_tasks"]] == ["existing-1"]
        assert resumed == [("existing-1", "two")]
    finally:
        directory.cleanup()


def test_run_once_does_not_create_or_fill_when_no_existing_tasks() -> None:
    directory, repo = make_repo("- [ ] one\n")
    try:
        with patch.dict("os.environ", {"MANUS_API_KEY": "synthetic-test-key"}), patch.object(worker, "resume_task") as resume:
            assert worker.run_once(repo, max_active_tasks=3) == 0
        resume.assert_not_called()
        assert not (repo / worker.STATE_FILE).exists()
    finally:
        directory.cleanup()


def test_running_existing_tasks_are_only_monitored() -> None:
    directory, repo = make_repo("- [ ] one\n")
    try:
        worker.save_state(repo, {"active_tasks": [{"task_id": "existing", "todo_project": str(repo), "todo_line": 1, "todo_item": "one"}]})
        with patch.dict("os.environ", {"MANUS_API_KEY": "synthetic-test-key"}), patch.object(worker, "task_status", return_value="running"), patch.object(worker, "resume_task") as resume:
            assert worker.run_once(repo) == 0
        resume.assert_not_called()
    finally:
        directory.cleanup()


def test_run_once_caps_persisted_state_at_ten() -> None:
    directory, repo = make_repo("- [ ] one\n")
    try:
        worker.save_state(repo, {"active_tasks": [{"task_id": f"task-{number}"} for number in range(11)]})
        with patch.dict("os.environ", {"MANUS_API_KEY": "synthetic-test-key"}), patch.object(worker, "task_status", return_value="running"):
            assert worker.run_once(repo, max_active_tasks=10) == 0
        saved = json.loads((repo / worker.STATE_FILE).read_text(encoding="utf-8"))
        assert len(saved["active_tasks"]) == 10
    finally:
        directory.cleanup()


def test_run_once_rejects_more_than_ten_active_tasks() -> None:
    directory, repo = make_repo("- [ ] one\n")
    try:
        with patch.object(worker, "acquire_lock"):
            try:
                worker.run_once(repo, max_active_tasks=11)
            except ValueError as exc:
                assert str(exc) == "max_active_tasks must be between 1 and 10"
            else:
                raise AssertionError("max_active_tasks=11 must be rejected")
    finally:
        directory.cleanup()


def test_dry_run_reports_existing_tasks_without_network() -> None:
    directory, repo = make_repo("- [ ] one\n")
    try:
        worker.save_state(repo, {"active_tasks": [{"task_id": "task-1"}, {"task_id": "task-2"}]})
        with patch.object(worker, "task_status") as status, patch.object(worker, "resume_task") as resume:
            assert worker.run_once(repo, dry_run=True) == 0
        status.assert_not_called()
        resume.assert_not_called()
    finally:
        directory.cleanup()
