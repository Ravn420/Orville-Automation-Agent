from __future__ import annotations

from pathlib import Path

from orville_core.repository_evaluation import RepositoryEvaluationRequest, evaluate_repository
from orville_core.sandbox import SandboxResult


class FakeExecutor:
    def __init__(self, available: bool = True, stdout: str = "status=ok behavioral acceptance") -> None:
        self._available = available
        self.stdout = stdout
        self.plan = None

    def available(self) -> bool:
        return self._available

    def run(self, plan):
        self.plan = plan
        return SandboxResult(plan.run_id, "completed", 0, self.stdout)

    def terminate(self, run_id: str) -> None:
        return None


def test_repository_evaluation_hashes_and_checks_behavior(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("print('status=ok behavioral acceptance')\n", encoding="utf-8")
    executor = FakeExecutor()
    result = evaluate_repository(
        RepositoryEvaluationRequest(tmp_path, ("python", "app.py"), ("status=ok", "behavioral acceptance"), "run-1"),
        executor,
    )
    assert result.status == "passed"
    assert len(result.project_checksum) == 64
    assert executor.plan is not None
    assert executor.plan.policy.network is False
    assert executor.plan.policy.require_isolation is True


def test_repository_evaluation_fails_closed_without_adapter(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("print('ok')\n", encoding="utf-8")
    result = evaluate_repository(RepositoryEvaluationRequest(tmp_path, ("python", "app.py")), FakeExecutor(False))
    assert result.status == "blocked"
    assert result.sandbox is None
    assert "isolation adapter" in result.reason


def test_repository_evaluation_reports_behavioral_failure(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("print('wrong')\n", encoding="utf-8")
    result = evaluate_repository(
        RepositoryEvaluationRequest(tmp_path, ("python", "app.py"), ("expected marker",)),
        FakeExecutor(stdout="wrong"),
    )
    assert result.status == "failed"
    assert result.behavioral is not None
    assert result.behavioral.passed is False
