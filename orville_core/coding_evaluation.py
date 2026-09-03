"""Validation contracts for repository-level coding evaluation cases."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


REQUIRED_STAGES = ("issue", "patch", "dependencies", "tests", "regression")


@dataclass(frozen=True)
class CodingEvaluationCase:
    case_id: str
    issue: str
    patch: str
    dependencies: tuple[str, ...]
    test_command: tuple[str, ...]
    regression_command: tuple[str, ...]

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "CodingEvaluationCase":
        required = {"id", "issue", "patch", "dependencies", "test_command", "regression_command"}
        missing = sorted(required - set(raw))
        if missing:
            raise ValueError(f"missing coding-evaluation fields: {', '.join(missing)}")
        values = {key: raw[key] for key in required}
        if not isinstance(values["issue"], str) or not values["issue"].strip():
            raise ValueError("issue must be non-empty")
        if not isinstance(values["patch"], str) or not values["patch"].strip():
            raise ValueError("patch must be a non-empty unified-diff reference")
        dependencies = values["dependencies"]
        if not isinstance(dependencies, list) or any(not isinstance(item, str) or not item.strip() for item in dependencies):
            raise ValueError("dependencies must be a list of non-empty strings")
        for name in ("test_command", "regression_command"):
            command = values[name]
            if not isinstance(command, list) or not command or any(not isinstance(item, str) or not item for item in command):
                raise ValueError(f"{name} must be a non-empty argv list")
        return cls(str(values["id"]), values["issue"], values["patch"], tuple(dependencies), tuple(values["test_command"]), tuple(values["regression_command"]))


def validate_coding_evaluation_manifest(manifest: Mapping[str, Any]) -> tuple[CodingEvaluationCase, ...]:
    if manifest.get("schema_version") != 1:
        raise ValueError("unsupported coding-evaluation schema")
    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("manifest requires at least one case")
    parsed = tuple(CodingEvaluationCase.from_mapping(case) for case in cases)
    ids = [case.case_id for case in parsed]
    if len(set(ids)) != len(ids):
        raise ValueError("coding-evaluation case IDs must be unique")
    return parsed


def required_stages() -> tuple[str, ...]:
    return REQUIRED_STAGES
