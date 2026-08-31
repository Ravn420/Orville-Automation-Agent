from pathlib import Path
import subprocess
import sys

from orville_core.behavioral_evaluation import CodingEvaluationSpec, evaluate_coding_change


def test_repository_coding_evaluation_runs_full_workflow(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "base"], cwd=repo, check=True)
    patch = tmp_path / "change.patch"
    patch.write_text("""diff --git a/app.py b/app.py\nindex 7d8f6f1..f7a8e6f 100644\n--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-VALUE = 1\n+VALUE = 2\n""", encoding="utf-8")
    spec = CodingEvaluationSpec(
        issue_id="ISSUE-1",
        patch_path=patch,
        dependency_command=(sys.executable, "-c", "open('deps.ok', 'w').write('ok')"),
        focused_test_command=(sys.executable, "-c", "from app import VALUE; assert VALUE == 2"),
        regression_command=(sys.executable, "-c", "from app import VALUE; assert VALUE in (1, 2)"),
    )
    result = evaluate_coding_change(repo, spec)
    assert result.passed
    assert result.metadata["evaluation_type"] == "repository-coding-change"
    assert result.metadata["dependency_installation"] is True


def test_repository_coding_evaluation_rejects_missing_patch(tmp_path: Path):
    spec = CodingEvaluationSpec("ISSUE-2", tmp_path / "missing.patch", ("true",), ("true",))
    try:
        evaluate_coding_change(tmp_path, spec)
    except ValueError as error:
        assert "patch_path" in str(error)
    else:
        raise AssertionError("missing patch should be rejected")
