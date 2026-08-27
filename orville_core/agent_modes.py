"""Agent-mode and model-selection contracts for plan execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AgentMode:
    mode_id: str
    label: str
    system_instruction: str
    allowed_tools: frozenset[str] = frozenset()
    required_capabilities: frozenset[str] = frozenset()
    requires_approval: bool = False


@dataclass(frozen=True)
class ModelOption:
    provider_id: str
    model: str
    capabilities: frozenset[str]
    local: bool = False
    available: bool = True


class AgentModeRegistry:
    def __init__(self, modes: list[AgentMode] | None = None) -> None:
        self._modes = {mode.mode_id: mode for mode in modes or default_modes()}

    def get(self, mode_id: str) -> AgentMode:
        try:
            return self._modes[mode_id]
        except KeyError as exc:
            raise KeyError(f"agent mode not found: {mode_id}") from exc

    def list(self) -> tuple[AgentMode, ...]:
        return tuple(self._modes.values())


class ModelSelector:
    def __init__(self, models: list[ModelOption] | None = None) -> None:
        self.models = list(models or [])

    def select(self, required_capabilities: set[str] | frozenset[str], *, preferred_provider: str | None = None, local_only: bool = False) -> ModelOption:
        candidates = [model for model in self.models if model.available and required_capabilities <= model.capabilities and (not local_only or model.local)]
        if preferred_provider:
            preferred = [model for model in candidates if model.provider_id == preferred_provider]
            if preferred:
                return preferred[0]
        if not candidates:
            raise LookupError(f"no model satisfies capabilities: {sorted(required_capabilities)}")
        return candidates[0]


def default_modes() -> list[AgentMode]:
    return [
        AgentMode("planning", "Plan Mode", "Analyze the request and return an editable implementation plan without modifying files.", frozenset({"inspect_project", "read_file", "search_code"})),
        AgentMode("implementation", "Implementation", "Apply approved structured changes and preserve revision safety.", frozenset({"read_file", "apply_patch", "run_tests"}), frozenset({"code"})),
        AgentMode("testing", "Testing", "Run validation and produce reproducible evidence without hiding failures.", frozenset({"run_tests", "capture_screenshot"}), frozenset({"testing"})),
        AgentMode("security", "Security Review", "Find security defects and recommend bounded remediations.", frozenset({"search_code", "run_security_scan"}), frozenset({"security"}), True),
        AgentMode("deployment", "Deployment", "Prepare a release handoff; never deploy without release approval.", frozenset({"compare_revisions", "request_approval"}), frozenset({"deployment"}), True),
    ]
