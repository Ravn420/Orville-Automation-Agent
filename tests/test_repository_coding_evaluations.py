"""Contract tests for repository-level coding evaluations."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]
CONFIG = ROOT / "config" / "repository-coding-evaluations.json"
DOC = ROOT / "docs" / "REPOSITORY_CODING_EVALUATIONS.md"
RUNNER = ROOT / "tools" / "run_repository_coding_evaluations.py"


def test_manifest_defines_realistic_cases_and_required_gates() -> None:
    manifest = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert manifest["execution_policy"]["network"] == "disabled"
    assert manifest["execution_policy"]["external_side_effects"] == "forbidden"
    assert manifest["execution_policy"]["baseline_failure_required"] is True
    assert {case["id"] for case in manifest["cases"]} == {"cache-key-bug", "path-boundary"}
    for case in manifest["cases"]:
        assert case["issue"]
        assert case["patch_path"] == "golden.patch"
        assert case["dependency_manifest"] == "requirements.txt"
        assert case["focused_test_command"]
        assert case["compile_command"]
        assert case["regression_command"]
        assert len(case["acceptance"]) >= 5


def test_document_describes_issue_patch_dependency_and_regression_lifecycle() -> None:
    documentation = DOC.read_text(encoding="utf-8")
    for phrase in ("known failing issue", "dependency manifest", "golden patch", "focused tests", "regression command", "Network access"):
        assert phrase in documentation


def test_runner_passes_all_registered_cases_in_disposable_workspaces() -> None:
    completed = subprocess.run(
        [sys.executable, str(RUNNER)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    result = json.loads(completed.stdout)
    assert result["passed"] is True
    assert {case["id"] for case in result["cases"]} == {"cache-key-bug", "path-boundary"}
    assert all(case["passed"] for case in result["cases"])
    for case in result["cases"]:
        assert case["steps"]["baseline"]["returncode"] != 0
        assert case["steps"]["install"]["returncode"] == 0
        assert case["steps"]["patch_check"]["returncode"] == 0
        assert case["steps"]["focused"]["returncode"] == 0
        assert case["steps"]["compile"]["returncode"] == 0
        assert case["steps"]["regression"]["returncode"] == 0
