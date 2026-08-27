"""Provider-neutral adapter capability and health registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Callable


class AdapterStatus(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    MOCK = "mock"
    BLOCKED = "blocked"
    DEGRADED = "degraded"


@dataclass(frozen=True)
class AdapterHealth:
    adapter_id: str
    category: str
    status: AdapterStatus
    capabilities: frozenset[str] = frozenset()
    required_credentials: tuple[str, ...] = ()
    required_permissions: tuple[str, ...] = ()
    message: str = ""


class AdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, AdapterHealth] = {}
        self._checks: dict[str, Callable[[], AdapterHealth]] = {}

    def register(self, health: AdapterHealth, *, health_check: Callable[[], AdapterHealth] | None = None) -> AdapterHealth:
        self._adapters[health.adapter_id] = health
        if health_check:
            self._checks[health.adapter_id] = health_check
        return health

    def refresh(self, adapter_id: str) -> AdapterHealth:
        if adapter_id not in self._adapters:
            raise KeyError(f"adapter not found: {adapter_id}")
        check = self._checks.get(adapter_id)
        if check:
            self._adapters[adapter_id] = check()
        return self._adapters[adapter_id]

    def get(self, adapter_id: str) -> AdapterHealth:
        try:
            return self._adapters[adapter_id]
        except KeyError as exc:
            raise KeyError(f"adapter not found: {adapter_id}") from exc

    def list(self, *, category: str | None = None) -> tuple[AdapterHealth, ...]:
        items = tuple(self._adapters.values())
        return tuple(item for item in items if category is None or item.category == category)

    def require(self, adapter_id: str, capability: str) -> AdapterHealth:
        health = self.refresh(adapter_id)
        if health.status not in {AdapterStatus.AVAILABLE, AdapterStatus.MOCK}:
            raise RuntimeError(f"adapter unavailable: {adapter_id}: {health.message}")
        if capability not in health.capabilities:
            raise RuntimeError(f"adapter lacks capability {capability}: {adapter_id}")
        return health


def default_adapter_registry() -> AdapterRegistry:
    registry = AdapterRegistry()
    registry.register(AdapterHealth("local-workspace", "execution", AdapterStatus.MOCK, frozenset({"read_file", "write_file", "run_command", "revision", "rollback"}), message="Local bounded workspace; hardened sandbox not configured"))
    registry.register(AdapterHealth("browser", "browser", AdapterStatus.BLOCKED, frozenset(), required_permissions=("browser_session", "explicit_user_handoff"), message="Browser runtime and authenticated session are not configured"))
    registry.register(AdapterHealth("git-remote", "source_control", AdapterStatus.BLOCKED, frozenset({"status", "diff", "branch", "pull", "push", "pull_request"}), required_credentials=("GIT_TOKEN",), required_permissions=("repository_write",), message="Remote Git credentials and repository scope are not configured"))
    registry.register(AdapterHealth("deployment", "deployment", AdapterStatus.BLOCKED, frozenset({"preview", "staging", "production", "rollback"}), required_credentials=("DEPLOY_TOKEN",), required_permissions=("release_approval",), message="Deployment provider and release approval are not configured"))
    registry.register(AdapterHealth("identity", "identity", AdapterStatus.MOCK, frozenset({"project_membership", "role_authorization"}), message="Local SQLite membership directory; enterprise identity is not configured"))
    registry.register(AdapterHealth("object-storage", "storage", AdapterStatus.BLOCKED, frozenset({"upload", "download", "retention"}), required_credentials=("OBJECT_STORAGE_CREDENTIALS",), message="Object storage credentials are not configured"))
    return registry
