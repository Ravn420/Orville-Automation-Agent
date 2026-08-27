"""Permissioned skills, plugins, connectors, hooks, and subagent contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class PermissionSet:
    tools: frozenset[str] = frozenset()
    network_hosts: frozenset[str] = frozenset()
    scopes: frozenset[str] = frozenset()

    def allows(self, requested: "PermissionSet") -> bool:
        return requested.tools <= self.tools and requested.network_hosts <= self.network_hosts and requested.scopes <= self.scopes


@dataclass(frozen=True)
class Skill:
    skill_id: str
    version: str
    instructions: str
    required_tools: tuple[str, ...] = ()
    permissions: PermissionSet = PermissionSet()
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    enabled: bool = False


@dataclass(frozen=True)
class Plugin:
    plugin_id: str
    version: str
    skills: tuple[str, ...] = ()
    hooks: tuple[str, ...] = ()
    connectors: tuple[str, ...] = ()
    permissions: PermissionSet = PermissionSet()
    verified: bool = False


@dataclass(frozen=True)
class Connector:
    connector_id: str
    provider: str
    scopes: tuple[str, ...] = ()
    health: str = "unconfigured"
    enabled: bool = False


@dataclass(frozen=True)
class Hook:
    hook_id: str
    event: str
    handler_name: str
    permissions: PermissionSet = PermissionSet()
    enabled: bool = False


@dataclass(frozen=True)
class Subagent:
    agent_id: str
    role: str
    capabilities: tuple[str, ...]
    permissions: PermissionSet = PermissionSet()


class ExtensionRegistry:
    def __init__(self) -> None:
        self.skills: dict[str, Skill] = {}
        self.plugins: dict[str, Plugin] = {}
        self.connectors: dict[str, Connector] = {}
        self.hooks: dict[str, Hook] = {}
        self.subagents: dict[str, Subagent] = {}

    def install_skill(self, skill: Skill, *, granted: PermissionSet) -> Skill:
        if not granted.allows(skill.permissions):
            raise PermissionError(f"skill permissions exceed grant: {skill.skill_id}")
        self.skills[skill.skill_id] = skill
        return skill

    def install_plugin(self, plugin: Plugin, *, granted: PermissionSet, administrator_approved: bool = False) -> Plugin:
        if not plugin.verified or not administrator_approved:
            raise PermissionError(f"plugin requires verification and administrator approval: {plugin.plugin_id}")
        if not granted.allows(plugin.permissions):
            raise PermissionError(f"plugin permissions exceed grant: {plugin.plugin_id}")
        self.plugins[plugin.plugin_id] = plugin
        return plugin

    def register_connector(self, connector: Connector) -> Connector:
        self.connectors[connector.connector_id] = connector
        return connector

    def register_hook(self, hook: Hook, *, granted: PermissionSet) -> Hook:
        if not granted.allows(hook.permissions):
            raise PermissionError(f"hook permissions exceed grant: {hook.hook_id}")
        self.hooks[hook.hook_id] = hook
        return hook

    def register_subagent(self, agent: Subagent, *, granted: PermissionSet) -> Subagent:
        if not granted.allows(agent.permissions):
            raise PermissionError(f"subagent permissions exceed grant: {agent.agent_id}")
        self.subagents[agent.agent_id] = agent
        return agent


class HookDispatcher:
    def __init__(self, registry: ExtensionRegistry, handlers: dict[str, Callable[[dict[str, Any]], Any]] | None = None) -> None:
        self.registry = registry
        self.handlers = handlers or {}

    def dispatch(self, event: str, payload: dict[str, Any], *, task_permissions: PermissionSet) -> list[Any]:
        results: list[Any] = []
        for hook in self.registry.hooks.values():
            if hook.enabled and hook.event == event:
                if not task_permissions.allows(hook.permissions):
                    raise PermissionError(f"task cannot invoke hook: {hook.hook_id}")
                handler = self.handlers.get(hook.handler_name)
                if handler is None:
                    raise LookupError(f"hook handler unavailable: {hook.handler_name}")
                results.append(handler(dict(payload)))
        return results
