from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from tools.todo_autopilot import AutomationError, editing_prompt, find_todos, mark_complete, preview, process_one, select_item


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def make_repo(tmp_path: Path, todo: str = "- [ ] Add the feature\n") -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "TODO.md").write_text(todo, encoding="utf-8")
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "Orville Test")
    git(repo, "add", "TODO.md")
    git(repo, "commit", "-qm", "test: baseline")
    return repo


def test_dry_run_preview_is_read_only(tmp_path: Path) -> None:
    todo = make_repo(tmp_path)
    args = type("Args", (), {"todo_line": None, "branch": None, "agent": None, "validate": None, "push": False, "pr": False, "allow_all_edits": False})()
    result = preview(todo, args)
    assert result["status"] == "preview"
    assert result["todo_item"] == "Add the feature"
    assert result["changes_executed"] is False
    assert "- [ ]" in (todo / "TODO.md").read_text(encoding="utf-8")


def test_all_edits_policy_is_explicit_and_keeps_todo_worker_owned() -> None:
    prompt = editing_prompt(Path("repo"), "Update the release controls", allow_all_edits=True)
    assert "edit any repository file" in prompt
    assert "do not edit TODO.md" in prompt
    assert "external side effects" in prompt


def test_mark_complete_changes_only_unchecked_checkbox(tmp_path: Path) -> None:
    todo = make_repo(tmp_path)
    item = select_item(todo)
    assert item is not None
    mark_complete(item)
    assert (todo / "TODO.md").read_text(encoding="utf-8") == "- [x] Add the feature\n"
    assert find_todos(todo) == []


def test_mark_complete_fails_if_line_moved(tmp_path: Path) -> None:
    todo = make_repo(tmp_path)
    item = select_item(todo)
    assert item is not None
    (todo / "TODO.md").write_text("- [x] Already done\n- [ ] Add the feature\n", encoding="utf-8")
    with pytest.raises(AutomationError, match="state changed"):
        mark_complete(item)


def test_process_one_does_not_mark_or_commit_when_validation_fails(tmp_path: Path) -> None:
    todo = make_repo(tmp_path)
    args = type("Args", (), {
        "todo_line": None,
        "branch": None,
        "agent": "python -c \"open('feature.py','w').write('value = 1\\n')\"",
        "validate": ["python -c \"raise SystemExit(3)\""],
        "push": False,
        "pr": False,
        "approve": False,
    })()
    with pytest.raises(AutomationError, match="command failed"):
        process_one(todo, args)
    assert "- [ ]" in (todo / "TODO.md").read_text(encoding="utf-8")
    assert subprocess.run(["git", "log", "-1", "--format=%s"], cwd=todo, capture_output=True, text=True).stdout.startswith("test: baseline")
    assert (todo / "feature.py").exists()
    assert json.loads((todo / ".orville_todo_autopilot.json").read_text(encoding="utf-8"))["runs"][0]["status"] == "failed"


def test_process_one_marks_only_after_validation_and_commits(tmp_path: Path) -> None:
    todo = make_repo(tmp_path)
    args = type("Args", (), {
        "todo_line": None,
        "branch": None,
        "agent": "python -c \"open('feature.py','w').write('value = 1\\n')\"",
        "validate": ["python -m py_compile feature.py"],
        "push": False,
        "pr": False,
        "approve": False,
    })()
    result = process_one(todo, args)
    assert result["status"] == "completed"
    completed_todo = subprocess.run(["git", "show", f"{result['branch']}:TODO.md"], cwd=todo, capture_output=True, text=True, check=True).stdout
    assert "- [x]" in completed_todo
    assert "todo: complete" in subprocess.run(["git", "log", result["branch"], "-1", "--format=%s"], cwd=todo, capture_output=True, text=True).stdout
    assert subprocess.run(["git", "branch", "--show-current"], cwd=todo, capture_output=True, text=True).stdout.strip() == "master"
