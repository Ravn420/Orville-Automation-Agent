"""Contract tests for the task-specific evaluation dataset registry."""
from __future__ import annotations

import json
from pathlib import Path


REGISTRY = Path(__file__).parents[1] / "config" / "evaluation-datasets.json"
DOC = Path(__file__).parents[1] / "docs" / "EVALUATION_DATASETS_AND_GOLDEN_CASES.md"
EXPECTED_SUITES = {
    "planning",
    "code-generation",
    "debugging",
    "refactoring",
    "research",
    "gui-workflows",
    "model-import",
}


def load_registry() -> dict[str, object]:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def test_registry_has_all_task_specific_suites_and_two_cases_each() -> None:
    registry = load_registry()
    suites = registry["suites"]
    assert isinstance(suites, list)
    assert {suite["id"] for suite in suites} == EXPECTED_SUITES
    for suite in suites:
        cases = suite["golden_cases"]
        assert len(cases) == 2
        assert all(case["id"] for case in cases)
        assert all(case["must_include"] for case in cases)
        assert all(case["must_not_include"] for case in cases)
        assert suite["acceptance"]


def test_registry_case_ids_are_unique_and_execution_is_safe_by_default() -> None:
    registry = load_registry()
    cases = [case["id"] for suite in registry["suites"] for case in suite["golden_cases"]]
    assert len(cases) == len(set(cases))
    defaults = registry["execution_defaults"]
    assert defaults["deterministic"] is True
    assert defaults["seed_required"] is True
    assert defaults["external_side_effects"] == "forbidden"
    assert defaults["approval_required_for_high_impact_actions"] is True


def test_registry_is_synthetic_local_and_documented() -> None:
    registry = load_registry()
    privacy = registry["privacy"]
    assert privacy["data_classification"] == "synthetic-local"
    assert privacy["external_credentials"] is False
    assert privacy["customer_data"] is False
    documentation = DOC.read_text(encoding="utf-8")
    documented_labels = {
        "planning": "Planning",
        "code-generation": "Code generation",
        "debugging": "Debugging",
        "refactoring": "Refactoring",
        "research": "Research",
        "gui-workflows": "GUI workflows",
        "model-import": "Model import",
    }
    for label in documented_labels.values():
        assert label in documentation
    assert "behavioral acceptance" in documentation
    assert "must-not-include" in documentation
    assert "must not be used to authorize a real deployment" in documentation
