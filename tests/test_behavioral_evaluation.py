from pathlib import Path
import sys

import pytest

from orville_core.behavioral_evaluation import (
    BehavioralAcceptanceCase,
    evaluate_generated_software,
)


def _candidate(tmp_path: Path) -> Path:
    root = tmp_path / "candidate"
    root.mkdir()
    (root / "app.py").write_text("from pathlib import Path\nPath('created.txt').write_text('ok')\n", encoding="utf-8")
    return root


def test_behavioral_evaluation_runs_in_temporary_copy_and_checks_files(tmp_path):
    result = evaluate_generated_software(
        _candidate(tmp_path),
        [BehavioralAcceptanceCase("run", (sys.executable, "app.py"), required_paths=("created.txt",), forbidden_paths=("secret.txt",))],
    )
    assert result.passed
    assert result.metadata["isolation"] == "temporary-copy"
    assert not (tmp_path / "candidate" / "created.txt").exists()
    assert len(result.candidate_sha256) == 64


def test_behavioral_evaluation_fails_on_exit_code(tmp_path):
    root = _candidate(tmp_path)
    result = evaluate_generated_software(root, [BehavioralAcceptanceCase("fail", (sys.executable, "-c", "raise SystemExit(3)"))])
    assert not result.passed
    assert any(not check.passed for check in result.cases)


def test_behavioral_evaluation_rejects_traversal_and_empty_cases(tmp_path):
    with pytest.raises(ValueError):
        evaluate_generated_software(tmp_path, [])
    with pytest.raises(ValueError):
        BehavioralAcceptanceCase("unsafe", ("echo", "ok"), required_paths=("../outside",)).validate()
