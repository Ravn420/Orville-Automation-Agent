from __future__ import annotations

import json
from pathlib import Path

import pytest

from orville_core.coding_evaluation import required_stages, validate_coding_evaluation_manifest


MANIFEST = Path(__file__).parents[1] / "config" / "repository-coding-evaluations.json"


def test_manifest_covers_all_repository_evaluation_stages() -> None:
    raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cases = validate_coding_evaluation_manifest(raw)
    assert len(cases) == 1
    case = cases[0]
    assert set(required_stages()) == {"issue", "patch", "dependencies", "tests", "regression"}
    assert case.issue and case.patch
    assert case.dependencies == ("requirements.txt",)
    assert case.test_command == ("python", "-m", "pytest", "tests")
    assert case.regression_command[-1] == "-q"
    assert raw["evaluation_policy"]["requires_isolated_execution"] is True
    assert raw["evaluation_policy"]["network_default"] is False


def test_manifest_rejects_shell_string_commands() -> None:
    raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
    raw["cases"][0]["test_command"] = "python -m pytest tests"
    with pytest.raises(ValueError, match="argv"):
        validate_coding_evaluation_manifest(raw)


def test_manifest_rejects_missing_issue_or_patch() -> None:
    raw = json.loads(MANIFEST.read_text(encoding="utf-8"))
    raw["cases"][0].pop("patch")
    with pytest.raises(ValueError, match="missing coding-evaluation fields"):
        validate_coding_evaluation_manifest(raw)
