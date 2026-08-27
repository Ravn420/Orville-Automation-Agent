"""Isolated, reproducible behavioral evaluation for generated software.

The evaluator copies a candidate into a temporary directory and runs declared
commands without a shell. Acceptance is based on exit status and filesystem
postconditions, not source-text similarity. It records hashes and bounded
outputs so results can be reproduced without retaining candidate source.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from time import monotonic
from typing import Iterable, Sequence


_MAX_TIMEOUT_SECONDS = 300.0
_DEFAULT_OUTPUT_LIMIT = 8_000


@dataclass(frozen=True)
class BehavioralAcceptanceCase:
    """One executable acceptance case and its observable postconditions."""

    name: str
    command: tuple[str, ...]
    expected_exit_code: int = 0
    required_paths: tuple[str, ...] = ()
    forbidden_paths: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("case name must not be blank")
        if not self.command or any(not part for part in self.command):
            raise ValueError("case command must be a non-empty argument list")
        for path in (*self.required_paths, *self.forbidden_paths):
            candidate = Path(path)
            if candidate.is_absolute() or ".." in candidate.parts:
                raise ValueError(f"acceptance path must be relative: {path!r}")


@dataclass(frozen=True)
class BehavioralEvaluationCheck:
    """Serializable result for one behavioral acceptance assertion."""

    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class BehavioralEvaluationResult:
    """Complete reproducibility metadata and acceptance outcome."""

    passed: bool
    candidate_sha256: str
    cases: tuple[BehavioralEvaluationCheck, ...]
    metadata: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "candidate_sha256": self.candidate_sha256,
            "cases": [asdict(case) for case in self.cases],
            "metadata": dict(self.metadata),
        }


def _candidate_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _bounded_output(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[:limit] + "...[truncated]"


def evaluate_generated_software(
    source_directory: str | os.PathLike[str],
    acceptance_cases: Iterable[BehavioralAcceptanceCase],
    *,
    timeout_seconds: float = 30.0,
    output_limit: int = _DEFAULT_OUTPUT_LIMIT,
) -> BehavioralEvaluationResult:
    """Evaluate a candidate in a temporary copy using behavioral checks.

    Commands are argument sequences and are never passed through a shell.
    Environment variables are inherited only for locale and Python import
    stability; callers should use synthetic fixtures and local dependencies.
    The temporary copy is removed on return, including on command failure.
    """
    root = Path(source_directory).resolve()
    if not root.is_dir():
        raise ValueError("source_directory must be an existing directory")
    if not 0 < timeout_seconds <= _MAX_TIMEOUT_SECONDS:
        raise ValueError(f"timeout_seconds must be between 0 and {_MAX_TIMEOUT_SECONDS}")
    if output_limit < 1:
        raise ValueError("output_limit must be positive")
    cases = tuple(acceptance_cases)
    if not cases:
        raise ValueError("at least one behavioral acceptance case is required")
    for case in cases:
        case.validate()

    candidate_sha256 = _candidate_hash(root)
    checks: list[BehavioralEvaluationCheck] = []
    with tempfile.TemporaryDirectory(prefix="orville-eval-") as temporary:
        isolated = Path(temporary) / "candidate"
        shutil.copytree(root, isolated)
        for case in cases:
            started = monotonic()
            try:
                completed = subprocess.run(
                    list(case.command),
                    cwd=isolated,
                    env={"LC_ALL": "C", "LANG": "C", "PYTHONHASHSEED": "0", "PATH": os.environ.get("PATH", "")},
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    check=False,
                    shell=False,
                )
                elapsed_ms = round((monotonic() - started) * 1000, 3)
                passed_exit = completed.returncode == case.expected_exit_code
                checks.append(
                    BehavioralEvaluationCheck(
                        f"{case.name}:exit_code",
                        passed_exit,
                        f"expected {case.expected_exit_code}, got {completed.returncode}; "
                        f"stdout={_bounded_output(completed.stdout, output_limit)!r}; "
                        f"stderr={_bounded_output(completed.stderr, output_limit)!r}; elapsed_ms={elapsed_ms}",
                    )
                )
            except subprocess.TimeoutExpired as error:
                checks.append(
                    BehavioralEvaluationCheck(
                        f"{case.name}:exit_code",
                        False,
                        f"timed out after {timeout_seconds}s; output={_bounded_output(str(error), output_limit)!r}",
                    )
                )
                continue

            for relative in case.required_paths:
                checks.append(
                    BehavioralEvaluationCheck(
                        f"{case.name}:required_path:{relative}",
                        (isolated / relative).exists(),
                        "required path exists" if (isolated / relative).exists() else "required path missing",
                    )
                )
            for relative in case.forbidden_paths:
                checks.append(
                    BehavioralEvaluationCheck(
                        f"{case.name}:forbidden_path:{relative}",
                        not (isolated / relative).exists(),
                        "forbidden path absent" if not (isolated / relative).exists() else "forbidden path exists",
                    )
                )

    return BehavioralEvaluationResult(
        passed=all(check.passed for check in checks),
        candidate_sha256=candidate_sha256,
        cases=tuple(checks),
        metadata={
            "isolation": "temporary-copy",
            "shell": False,
            "network": "not requested; process-level network isolation is deployment-owned",
            "python": sys.version.split()[0],
            "timeout_seconds": timeout_seconds,
            "output_limit": output_limit,
            "commands": [list(case.command) for case in cases],
        },
    )


@dataclass(frozen=True)
class CodingEvaluationSpec:
    """Reproducible repository-level coding task definition."""

    issue_id: str
    patch_path: str | os.PathLike[str]
    focused_test_command: tuple[str, ...]
    regression_command: tuple[str, ...]
    dependency_command: tuple[str, ...] | None = None

    def validate(self) -> None:
        if not self.issue_id.strip():
            raise ValueError("issue_id must not be blank")
        if not self.focused_test_command or not self.regression_command:
            raise ValueError("focused and regression commands are required")
        if self.dependency_command is not None and not self.dependency_command:
            raise ValueError("dependency_command must be non-empty when provided")


def _run_coding_command(command: Sequence[str], cwd: Path, timeout_seconds: float, output_limit: int) -> BehavioralEvaluationCheck:
    started = monotonic()
    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            env={"LC_ALL": "C", "LANG": "C", "PYTHONHASHSEED": "0", "PATH": os.environ.get("PATH", "")},
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return BehavioralEvaluationCheck(
            "command:timeout",
            False,
            f"timed out after {timeout_seconds}s; command={list(command)!r}",
        )
    elapsed_ms = round((monotonic() - started) * 1000, 3)
    return BehavioralEvaluationCheck(
        "command:exit_code",
        completed.returncode == 0,
        f"command={list(command)!r}; exit_code={completed.returncode}; elapsed_ms={elapsed_ms}; "
        f"stdout={_bounded_output(completed.stdout, output_limit)!r}; stderr={_bounded_output(completed.stderr, output_limit)!r}",
    )


def evaluate_coding_change(
    repository_directory: str | os.PathLike[str],
    specification: CodingEvaluationSpec,
    *,
    timeout_seconds: float = 120.0,
    output_limit: int = _DEFAULT_OUTPUT_LIMIT,
) -> BehavioralEvaluationResult:
    """Apply a coding-task patch in isolation and run install, focused, and regression checks.

    The repository and patch are copied into a temporary directory. Git applies
    the patch without a shell, then each declared command runs in order. A
    dependency command is optional and should point only to a local lockfile or
    synthetic fixture; no network or credentials are supplied by this helper.
    """
    root = Path(repository_directory).resolve()
    patch = Path(specification.patch_path).resolve()
    if not root.is_dir() or not patch.is_file():
        raise ValueError("repository_directory and patch_path must exist")
    if not 0 < timeout_seconds <= _MAX_TIMEOUT_SECONDS:
        raise ValueError(f"timeout_seconds must be between 0 and {_MAX_TIMEOUT_SECONDS}")
    if output_limit < 1:
        raise ValueError("output_limit must be positive")
    specification.validate()
    patch_sha256 = hashlib.sha256(patch.read_bytes()).hexdigest()
    checks: list[BehavioralEvaluationCheck] = []
    with tempfile.TemporaryDirectory(prefix="orville-coding-eval-") as temporary:
        isolated = Path(temporary) / "repository"
        shutil.copytree(root, isolated)
        isolated_patch = Path(temporary) / "change.patch"
        shutil.copyfile(patch, isolated_patch)
        apply_result = _run_coding_command(("git", "apply", "--whitespace=error", str(isolated_patch)), Path(isolated), timeout_seconds, output_limit)
        apply_result = BehavioralEvaluationCheck("patch:applied", apply_result.passed, apply_result.detail)
        checks.append(apply_result)
        if apply_result.passed and specification.dependency_command is not None:
            dependency_result = _run_coding_command(specification.dependency_command, isolated, timeout_seconds, output_limit)
            checks.append(BehavioralEvaluationCheck("dependencies:installed", dependency_result.passed, dependency_result.detail))
        if all(check.passed for check in checks):
            focused = _run_coding_command(specification.focused_test_command, isolated, timeout_seconds, output_limit)
            checks.append(BehavioralEvaluationCheck("focused_tests:passed", focused.passed, focused.detail))
        if all(check.passed for check in checks):
            regression = _run_coding_command(specification.regression_command, isolated, timeout_seconds, output_limit)
            checks.append(BehavioralEvaluationCheck("regression:passed", regression.passed, regression.detail))
    return BehavioralEvaluationResult(
        passed=all(check.passed for check in checks),
        candidate_sha256=_candidate_hash(root),
        cases=tuple(checks),
        metadata={
            "evaluation_type": "repository-coding-change",
            "issue_id": specification.issue_id,
            "patch_sha256": patch_sha256,
            "dependency_installation": specification.dependency_command is not None,
            "commands": {
                "dependency": list(specification.dependency_command) if specification.dependency_command else None,
                "focused_tests": list(specification.focused_test_command),
                "regression": list(specification.regression_command),
            },
            "isolation": "temporary-copy",
            "shell": False,
            "network": "not requested; dependency source policy is caller-owned",
            "timeout_seconds": timeout_seconds,
            "output_limit": output_limit,
        },
    )
