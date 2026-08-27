"""Sandbox-backed local model execution service boundary."""
from __future__ import annotations

import tempfile
import uuid
from pathlib import Path
from typing import Any, Mapping

from .local_models import LocalModelCatalog
from .sandbox import SandboxExecutor, SandboxPlan, SandboxPolicy, SandboxResult, SandboxUnavailable
from .sandbox_adapters import discover_sandbox_adapters


class LocalModelExecutionError(RuntimeError):
    """Raised when a local model cannot be executed under the active policy."""


class LocalModelExecutionService:
    """Route every local model-file operation through an approved sandbox."""

    def __init__(self, catalog: LocalModelCatalog, adapters: Mapping[str, SandboxExecutor] | None = None, *, workspace: str | Path | None = None) -> None:
        self.catalog = catalog
        self.adapters = dict(adapters or discover_sandbox_adapters())
        self.workspace = Path(workspace or tempfile.gettempdir()).expanduser().resolve()

    def execute_local_model(
        self,
        model_id: str,
        *,
        command: tuple[str, ...] | list[str],
        operation: str = "infer",
        adapter: str = "auto",
        policy: SandboxPolicy | None = None,
        policy_id: str = "local-default",
        input_ref: str | None = None,
        output_ref: str | None = None,
        parameters: Mapping[str, Any] | None = None,
        request_id: str | None = None,
    ) -> SandboxResult:
        record = self.catalog.get(model_id)
        if record.status != "active":
            raise LocalModelExecutionError("local model must be active before execution")
        evidence = record.activation_evidence or {}
        if evidence.get("verification_status") not in {"verified", "optional"}:
            raise LocalModelExecutionError("local model activation evidence is missing or stale")
        model_path = Path(record.source_path).expanduser().resolve()
        checksum = self.catalog.verify_checksum(model_id)
        if not checksum["matches"]:
            raise LocalModelExecutionError("local model checksum changed after activation")
        selected = self._select_adapter(adapter)
        if not selected.available():
            raise SandboxUnavailable(f"sandbox adapter is unavailable: {adapter}")
        run_id = request_id or f"local-model:{uuid.uuid4().hex}"
        root = self.workspace / "orville-local-execution" / run_id.replace(":", "_")
        scratch = root / "scratch"
        output = Path(output_ref).expanduser().resolve() if output_ref else root / "output"
        plan = SandboxPlan(run_id=run_id, command=tuple(command), model_path=model_path, scratch_path=scratch, output_path=output, policy=policy or SandboxPolicy(), model_checksum=f"sha256:{record.checksum_sha256}", environment={}, audit_id=f"audit:{run_id}")
        plan.validate()
        return selected.run(plan)

    def _select_adapter(self, requested: str) -> SandboxExecutor:
        if requested != "auto":
            selected = self.adapters.get(requested)
            if selected is None:
                raise LocalModelExecutionError(f"unknown sandbox adapter: {requested}")
            return selected
        for candidate in self.adapters.values():
            if candidate.available():
                return candidate
        return self.adapters.get("unavailable") or _UnavailableAdapter()


def execute_local_model(catalog: LocalModelCatalog, model_id: str, **kwargs: Any) -> SandboxResult:
    """Convenience function for the canonical local execution boundary."""
    return LocalModelExecutionService(catalog).execute_local_model(model_id, **kwargs)


class _UnavailableAdapter:
    def available(self) -> bool:
        return False

    def run(self, plan: SandboxPlan) -> SandboxResult:
        raise SandboxUnavailable("no approved sandbox adapter is available")

    def terminate(self, run_id: str) -> None:
        return None
