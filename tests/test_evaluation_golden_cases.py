"""Regression checks for the deterministic evaluation golden-case dataset."""
from __future__ import annotations

import json
from pathlib import Path

from orville_core.evaluation import evaluate_output


DATASET = Path(__file__).parents[1] / "config" / "evaluation-golden-cases.json"
EXPECTED_DOMAINS = {
    "planning",
    "code_generation",
    "debugging",
    "refactoring",
    "research",
    "gui_workflows",
    "model_import",
}


def load_dataset() -> dict:
    return json.loads(DATASET.read_text(encoding="utf-8"))


def test_golden_dataset_has_required_domains_and_unique_ids() -> None:
    dataset = load_dataset()
    cases = dataset["cases"]
    assert dataset["schema_version"] == 1
    assert dataset["privacy"] == {
        "contains_secrets": False,
        "capture_policy": "fixture_inputs_and_expected_outputs_only",
        "retention": "repository-controlled",
    }
    assert {case["domain"] for case in cases} == EXPECTED_DOMAINS
    assert len({case["id"] for case in cases}) == len(cases)
    for case in cases:
        assert case["prompt"]
        assert case["required_criteria"]
        assert case["expected"]["must_pass"] is True
        assert case["expected"]["failure_mode"]


def test_each_golden_case_passes_with_required_criteria() -> None:
    for case in load_dataset()["cases"]:
        output = " ".join(case["required_criteria"])
        result = evaluate_output(output, case["required_criteria"])
        assert result.passed, case["id"]


def test_missing_golden_criterion_fails_deterministically() -> None:
    case = load_dataset()["cases"][0]
    result = evaluate_output(case["required_criteria"][0], case["required_criteria"])
    assert result.passed is False
    assert any(not check.passed for check in result.checks)
