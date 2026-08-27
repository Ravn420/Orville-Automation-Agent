"""Fail-closed contracts for isolated local-model execution.

The default executor never falls back to host-process execution. Platform
adapters can implement :class:`SandboxExecutor` once their isolation boundary
has been configured and tested.
"""

from __future__ import annotations

import os
import shlex
from dataclasses import dataclass, field
from pathlib import Path, PureWindowsPath
from typing import Any, Mapping, Protocol


class SandboxError(RuntimeError):
    """Base class for sandbox policy and execution failures."""


class SandboxUnavailable(SandboxError):
    """Raised when no approved platform isolation adapter is available."""


@dataclass(frozen=True)
class SandboxPolicy:
    """Explicit execution limits and boundary permissions."""

    network: bool = False
    max_cpu_seconds: int = 300
    max_memory_bytes: int = 4 * 1024 * 1024 * 1024
    max_disk_bytes: int = 8 * 1024 * 1024 * 1024
    max_processes: int = 32
    max_output_bytes: int = 16 * 1024 * 1024
    timeout_seconds: int = 300
    allow_gpu: bool = False
    allowed_environment: frozenset[str] = frozenset()
    require_isolation: bool = True

    def validate(self) -> None:
        for name, value in (("max_cpu_seconds", self.max_cpu_seconds), ("max_memory_bytes", self.max_memory_bytes), ("max_disk_bytes", self.max_disk_bytes), ("max_processes", self.max_processes), ("max_output_bytes", self.max_output_bytes), ("timeout_seconds", self.timeout_seconds)):
            if value <= 0:
                raise ValueError(f"{name} must be positive")
        if self.require_isolation and self.allow_gpu and self.network:
            raise ValueError("GPU and network access cannot both be enabled by the default isolation policy")


@dataclass(frozen=True)
class SandboxPlan:
    """Validated, immutable description of a worker launch."""

    run_id: str
    command: tuple[str, ...]
    model_path: Path
    scratch_path: Path
    output_path: Path
    policy: SandboxPolicy
    model_checksum: str
    environment: Mapping[str, str] = field(default_factory=dict)
    audit_id: str = ""

    def validate(self) -> None:
        self.policy.validate()
        if not self.run_id or not self.model_checksum:
            raise ValueError("run_id and model_checksum are required")
        if not self.command or any(not part or "\x00" in part for part in self.command):
            raise ValueError("command must be a non-empty argv sequence without NUL bytes")
        if any(char in self.command[0] for char in "&|;<>`\n"):
            raise ValueError("shell syntax is not allowed in sandbox argv")
        for path_name, path in (("model_path", self.model_path), ("scratch_path", self.scratch_path), ("output_path", self.output_path)):
            if not path.is_absolute() and not PureWindowsPath(str(path)).is_absolute():
                raise ValueError(f"{path_name} must be absolute")
        if set(self.environment) - self.policy.allowed_environment:
            raise ValueError("environment contains variables outside the sandbox allowlist")
        if any(key.upper().endswith(("TOKEN", "KEY", "SECRET", "PASSWORD")) for key in self.environment):
            raise ValueError("credential-like environment variables are not allowed")

    @classmethod
    def from_request(cls, request: Mapping[str, Any], policy: SandboxPolicy) -> "SandboxPlan":
        command = request.get("command")
        if isinstance(command, str):
            raise ValueError("command must be argv, not a shell string")
        plan = cls(
            run_id=str(request.get("run_id", "")),
            command=tuple(str(item) for item in (command or ())),
            model_path=Path(str(request.get("model_path", ""))).expanduser().resolve(),
            scratch_path=Path(str(request.get("scratch_path", ""))).expanduser().resolve(),
            output_path=Path(str(request.get("output_path", ""))).expanduser().resolve(),
            policy=policy,
            model_checksum=str(request.get("model_checksum", "")),
            environment={str(key): str(value) for key, value in dict(request.get("environment", {})).items()},
            audit_id=str(request.get("audit_id", "")),
        )
        plan.validate()
        return plan


@dataclass(frozen=True)
class SandboxResult:
    run_id: str
    status: str
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    diagnostics: tuple[dict[str, Any], ...] = ()
    resource_usage: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"run_id": self.run_id, "status": self.status, "exit_code": self.exit_code, "stdout": self.stdout, "stderr": self.stderr, "diagnostics": list(self.diagnostics), "resource_usage": dict(self.resource_usage)}


class SandboxExecutor(Protocol):
    """Platform adapter interface for isolated worker execution."""

    def available(self) -> bool: ...

    def run(self, plan: SandboxPlan) -> SandboxResult: ...

    def terminate(self, run_id: str) -> None: ...


class UnavailableSandboxExecutor:
    """Default executor that prevents unsafe host-process fallback."""

    def available(self) -> bool:
        return False

    def run(self, plan: SandboxPlan) -> SandboxResult:
        plan.validate()
        raise SandboxUnavailable("no approved process-level sandbox adapter is configured")

    def terminate(self, run_id: str) -> None:
        return None


def filtered_environment(plan: SandboxPlan) -> dict[str, str]:
    """Return only explicitly allowed, non-secret environment variables."""

    plan.validate()
    return {key: value for key, value in plan.environment.items() if key in plan.policy.allowed_environment}
