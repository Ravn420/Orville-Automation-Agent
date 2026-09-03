"""Reproducible, isolated evaluation for generated repositories.

This module deliberately refuses host-process fallback. A caller must provide an
approved :class:`SandboxExecutor`; the default discovery result is unavailable
on hosts without a configured isolation adapter.
"""
from __future__ import annotations

import hashlib
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .evaluation import EvaluationResult, evaluate_output
from .sandbox import SandboxExecutor, SandboxPlan, SandboxPolicy, SandboxResult, SandboxUnavailable


@dataclass(frozen=True)
class RepositoryEvaluationRequest:
    project_path: Path
    command: tuple[str, ...]
    acceptance_criteria: tuple[str, ...] = ()
    run_id: str = "repository-evaluation"
    timeout_seconds: int = 60


@dataclass(frozen=True)
class RepositoryEvaluationResult:
    status: str
    project_checksum: str
    sandbox: SandboxResult | None = None
    behavioral: EvaluationResult | None = None
    reason: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "project_checksum": self.project_checksum,
            "sandbox": self.sandbox.to_dict() if self.sandbox else None,
            "behavioral": self.behavioral.to_dict() if self.behavioral else None,
            "reason": self.reason,
        }


def _project_checksum(project_path: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in project_path.rglob("*") if item.is_file()):
        relative = path.relative_to(project_path).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def evaluate_repository(request: RepositoryEvaluationRequest, executor: SandboxExecutor) -> RepositoryEvaluationResult:
    project_path = request.project_path.expanduser().resolve()
    if not project_path.is_dir():
        return RepositoryEvaluationResult("blocked", "", reason="project_path is not a directory")
    if not request.command or any(not part or "\x00" in part for part in request.command):
        return RepositoryEvaluationResult("blocked", _project_checksum(project_path), reason="command must be a non-empty argv sequence")
    if isinstance(request.command, str):
        return RepositoryEvaluationResult("blocked", _project_checksum(project_path), reason="shell command strings are not accepted")
    if request.timeout_seconds <= 0:
        return RepositoryEvaluationResult("blocked", _project_checksum(project_path), reason="timeout_seconds must be positive")

    checksum = _project_checksum(project_path)
    if not executor.available():
        return RepositoryEvaluationResult("blocked", checksum, reason="no approved isolation adapter is available")

    policy = SandboxPolicy(network=False, timeout_seconds=request.timeout_seconds, max_output_bytes=1_048_576)
    with tempfile.TemporaryDirectory(prefix="orville-evaluation-") as temporary:
        root = Path(temporary)
        plan = SandboxPlan(
            run_id=request.run_id,
            command=tuple(request.command),
            model_path=project_path,
            scratch_path=root / "scratch",
            output_path=root / "output",
            policy=policy,
            model_checksum=checksum,
        )
        try:
            sandbox_result = executor.run(plan)
        except SandboxUnavailable as exc:
            return RepositoryEvaluationResult("blocked", checksum, reason=str(exc))
        if sandbox_result.status != "completed" or sandbox_result.exit_code != 0:
            return RepositoryEvaluationResult("failed", checksum, sandbox=sandbox_result, reason="isolated command did not complete successfully")
        behavioral = evaluate_output(sandbox_result.stdout, request.acceptance_criteria)
        return RepositoryEvaluationResult("passed" if behavioral.passed else "failed", checksum, sandbox=sandbox_result, behavioral=behavioral, reason="behavioral acceptance evaluated")
