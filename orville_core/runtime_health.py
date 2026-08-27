"""Repeatable, secret-safe runtime health checks for Orville deployments."""
from __future__ import annotations

import importlib.util
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HealthCheck:
    name: str
    available: bool
    version: str | None = None
    detail: str = ""
    required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "available": self.available, "version": self.version, "detail": self.detail, "required": self.required}


class RuntimeHealth:
    def __init__(self, *, required_commands: tuple[str, ...] = ("git",), optional_commands: tuple[str, ...] = ("node", "pnpm", "gh", "manus-config", "manus-mcp-cli"), optional_modules: tuple[str, ...] = ("fastapi", "uvicorn")) -> None:
        self.required_commands = required_commands
        self.optional_commands = optional_commands
        self.optional_modules = optional_modules

    @staticmethod
    def _command_version(command: str) -> str | None:
        path = shutil.which(command)
        if not path:
            return None
        try:
            result = subprocess.run((command, "--version"), capture_output=True, text=True, timeout=5, check=False)
        except (OSError, subprocess.SubprocessError):
            return None
        value = (result.stdout or result.stderr).strip().splitlines()
        return value[0][:160] if value else None

    def run(self) -> dict[str, Any]:
        checks: list[HealthCheck] = []
        for command in self.required_commands:
            version = self._command_version(command)
            checks.append(HealthCheck(command, version is not None, version, "required runtime command"))
        for command in self.optional_commands:
            if command == "manus-mcp-cli":
                available = shutil.which(command) is not None
                checks.append(HealthCheck(command, available, None, "optional MCP utility; presence-only check", required=False))
            else:
                version = self._command_version(command)
                checks.append(HealthCheck(command, version is not None, version, "optional integration utility", required=False))
        for module in self.optional_modules:
            available = importlib.util.find_spec(module) is not None
            checks.append(HealthCheck(f"python:{module}", available, None, "optional Python module", required=False))
        return {
            "status": "ok" if all(check.available for check in checks if check.required) else "degraded",
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "cwd": os.getcwd(),
            "checks": [check.to_dict() for check in checks],
        }
