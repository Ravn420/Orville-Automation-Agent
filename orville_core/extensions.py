"""Permissioned skills, plugins, connectors, hooks, and subagent contracts."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable
from pathlib import Path

logger = logging.getLogger("orville.core.extensions")
logger.debug("HookDispatcher module loaded")


@dataclass
class Connector:
    """External service integration contract."""

    name: str
    base_url: str
    auth: dict = field(default_factory=dict)
    timeout: float = 30.0
    enabled: bool = True

    def request(self, method: str, path: str, **kwargs):
        import requests
        url = self.base_url.rstrip("/") + path
        return requests.request(method, url, timeout=self.timeout, **kwargs)


@dataclass
class PermissionSet:
    """Fine-grained permissions for a skill or plugin."""

    tools: frozenset = field(default_factory=frozenset)
    allowed_actions: list = field(default_factory=list)
    denied_actions: list = field(default_factory=list)
    network_hosts: frozenset = field(default_factory=frozenset)
    scopes: frozenset = field(default_factory=frozenset)

    def can(self, action: str) -> bool:
        if action in self.denied_actions:
            return False
        if not self.allowed_actions:
            return True
        return action in self.allowed_actions

    def allows(self, required: "PermissionSet") -> bool:
        """Check if this permission set grants all the tools, scopes, and network_hosts of the required set."""
        if not required.tools.issubset(self.tools):
            return False
        if not required.scopes.issubset(self.scopes):
            return False
        if not required.network_hosts.issubset(self.network_hosts):
            return False
        return True


@dataclass
class Hook:
    """Event hook definition."""

    name: str
    event: str
    action: str
    permissions: PermissionSet
    enabled: bool = True


@dataclass
class Skill:
    """Skill definition."""

    name: str
    version: str
    description: str
    required_tools: tuple = field(default_factory=tuple)
    permissions: PermissionSet = field(default_factory=PermissionSet)


@dataclass
class Plugin:
    """Plugin definition."""

    name: str
    version: str
    verified: bool = False


@dataclass
class Subagent:
    """Subagent definition."""

    name: str
    purpose: str
    capabilities: tuple
    permissions: PermissionSet


@dataclass
class ExtensionRegistry:
    """Registry of loaded extensions."""

    extensions: dict = field(default_factory=dict)
    connectors: dict = field(default_factory=dict)
    hooks: dict = field(default_factory=dict)
    skills: dict = field(default_factory=dict)
    plugins: dict = field(default_factory=dict)
    subagents: dict = field(default_factory=dict)

    def register(self, name: str, extension: Any) -> None:
        self.extensions[name] = extension

    def get(self, name: str) -> Any:
        return self.extensions.get(name)

    def register_connector(self, connector: Connector) -> None:
        self.connectors[connector.name] = connector

    def register_hook(self, hook: Hook, granted: PermissionSet) -> None:
        if not granted.allows(hook.permissions):
            raise PermissionError(f"Insufficient permissions to register hook {hook.name}")
        self.hooks[hook.name] = hook

    def install_skill(self, skill: Skill, granted: PermissionSet) -> None:
        if not granted.allows(skill.permissions):
            raise PermissionError(f"Insufficient permissions to install skill {skill.name}")
        self.skills[skill.name] = skill

    def install_plugin(self, plugin: Plugin, granted: PermissionSet, administrator_approved: bool = False) -> None:
        if not plugin.verified:
            raise PermissionError(f"Plugin {plugin.name} is not verified")
        self.plugins[plugin.name] = plugin

    def register_subagent(self, agent: Subagent, granted: PermissionSet) -> None:
        if not granted.allows(agent.permissions):
            raise PermissionError(f"Insufficient permissions to register subagent {agent.name}")
        self.subagents[agent.name] = agent


@dataclass
class HookDispatcher:
    """Dispatches events to registered handlers."""

    registry: ExtensionRegistry
    handlers: dict

    def dispatch(self, event: str, *args, task_permissions: PermissionSet = None, **kwargs) -> list:
        results = []
        for hook_name, hook in self.registry.hooks.items():
            if hook.event == event and hook.enabled:
                if task_permissions is not None and not task_permissions.allows(hook.permissions):
                    raise PermissionError(f"Insufficient permissions for hook {hook.name}")
                handler = self.handlers.get(hook.action)
                if handler is None:
                    continue
                result = handler(*args, **kwargs)
                if result is not None:
                    results.append(result)
        return results


@dataclass
class ExtensionContext:
    """Runtime context passed to extensions."""

    registry: ExtensionRegistry
    hooks: HookDispatcher
    connector: Connector | None = None
    permissions: PermissionSet | None = None

    def emit(self, event: str, *args, **kwargs):
        return self.hooks.dispatch(event, *args, **kwargs)


# Re-export ExtensionManager so `from .extensions import ExtensionManager` works
from .extension_manager import ExtensionManager  # noqa: E402,F401
