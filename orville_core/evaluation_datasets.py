"""Load and validate credential-free task evaluation datasets.

The catalog is intentionally data-only: it describes prompts, required and
prohibited observable behaviors, and a small oracle contract. This module
validates the structure before callers use a case in an evaluator; it never
executes prompts, contacts providers, or treats catalog text as instructions.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping


EXPECTED_TASK_TYPES = frozenset(
    {"planning", "code_generation", "debugging", "refactoring", "research", "gui_workflows", "model_import"}
)


class EvaluationDatasetError(ValueError):
    """Raised when an evaluation catalog violates the data contract."""


@dataclass(frozen=True)
class GoldenCase:
    """One validated, credential-free behavioral evaluation case."""

    id: str
    prompt: str
    required_behaviors: tuple[str, ...]
    prohibited_behaviors: tuple[str, ...]
    oracle_artifact: str
    oracle_must_include: tuple[str, ...]


@dataclass(frozen=True)
class EvaluationDataset:
    """A validated dataset grouped by one supported task type."""

    id: str
    task_type: str
    description: str
    golden_cases: tuple[GoldenCase, ...]


def _non_empty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvaluationDatasetError(f"{field} must be a non-empty string")
    return value.strip()


def _string_tuple(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise EvaluationDatasetError(f"{field} must be a non-empty list")
    result = tuple(_non_empty_string(item, f"{field}[]") for item in value)
    if len(set(result)) != len(result):
        raise EvaluationDatasetError(f"{field} must not contain duplicates")
    return result


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise EvaluationDatasetError(f"{field} must be an object")
    return value


def parse_evaluation_catalog(document: Mapping[str, Any]) -> tuple[EvaluationDataset, ...]:
    """Validate and parse a catalog document without executing its content."""
    if not isinstance(document, dict):
        raise EvaluationDatasetError("catalog must be an object")
    if _non_empty_string(document.get("schema_version"), "schema_version") != "1.0":
        raise EvaluationDatasetError("schema_version must be '1.0'")
    _non_empty_string(document.get("catalog_id"), "catalog_id")
    governance = _mapping(document.get("governance"), "governance")
    for field in ("source_policy", "execution_policy", "scoring_policy"):
        _non_empty_string(governance.get(field), f"governance.{field}")
    raw_datasets = document.get("datasets")
    if not isinstance(raw_datasets, list) or not raw_datasets:
        raise EvaluationDatasetError("datasets must be a non-empty list")

    datasets: list[EvaluationDataset] = []
    seen_dataset_ids: set[str] = set()
    seen_case_ids: set[str] = set()
    for index, raw_dataset in enumerate(raw_datasets):
        dataset = _mapping(raw_dataset, f"datasets[{index}]")
        dataset_id = _non_empty_string(dataset.get("id"), f"datasets[{index}].id")
        task_type = _non_empty_string(dataset.get("task_type"), f"datasets[{index}].task_type")
        if dataset_id in seen_dataset_ids:
            raise EvaluationDatasetError(f"duplicate dataset id: {dataset_id}")
        if task_type not in EXPECTED_TASK_TYPES:
            raise EvaluationDatasetError(f"unsupported task_type: {task_type}")
        seen_dataset_ids.add(dataset_id)
        description = _non_empty_string(dataset.get("description"), f"datasets[{index}].description")
        raw_cases = dataset.get("golden_cases")
        if not isinstance(raw_cases, list) or not raw_cases:
            raise EvaluationDatasetError(f"datasets[{index}].golden_cases must be a non-empty list")
        cases: list[GoldenCase] = []
        for case_index, raw_case in enumerate(raw_cases):
            case = _mapping(raw_case, f"datasets[{index}].golden_cases[{case_index}]")
            case_id = _non_empty_string(case.get("id"), "case.id")
            if case_id in seen_case_ids:
                raise EvaluationDatasetError(f"duplicate golden case id: {case_id}")
            seen_case_ids.add(case_id)
            oracle = _mapping(case.get("oracle"), f"case[{case_id}].oracle")
            cases.append(
                GoldenCase(
                    id=case_id,
                    prompt=_non_empty_string(case.get("prompt"), f"case[{case_id}].prompt"),
                    required_behaviors=_string_tuple(case.get("required_behaviors"), f"case[{case_id}].required_behaviors"),
                    prohibited_behaviors=_string_tuple(case.get("prohibited_behaviors"), f"case[{case_id}].prohibited_behaviors"),
                    oracle_artifact=_non_empty_string(oracle.get("artifact"), f"case[{case_id}].oracle.artifact"),
                    oracle_must_include=_string_tuple(oracle.get("must_include"), f"case[{case_id}].oracle.must_include"),
                )
            )
        datasets.append(EvaluationDataset(dataset_id, task_type, description, tuple(cases)))

    actual_types = {dataset.task_type for dataset in datasets}
    missing = EXPECTED_TASK_TYPES - actual_types
    if missing:
        raise EvaluationDatasetError(f"catalog is missing task types: {', '.join(sorted(missing))}")
    return tuple(datasets)


def load_evaluation_catalog(path: str | Path) -> tuple[EvaluationDataset, ...]:
    """Load a UTF-8 JSON catalog and validate its complete data contract."""
    catalog_path = Path(path)
    try:
        document = json.loads(catalog_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise EvaluationDatasetError(f"catalog not found: {catalog_path}") from exc
    except json.JSONDecodeError as exc:
        raise EvaluationDatasetError(f"catalog is not valid JSON: {catalog_path}") from exc
    return parse_evaluation_catalog(document)


__all__ = ["EXPECTED_TASK_TYPES", "EvaluationDataset", "EvaluationDatasetError", "GoldenCase", "load_evaluation_catalog", "parse_evaluation_catalog"]
