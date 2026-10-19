"""Repeatable, secret-safe runtime health checks for Orville deployments."""
from __future__ import annotations

import importlib.util
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psutil

from orville_core.health_integration import (
    IntegrationHealthChecker,
    create_health_check_from_integration_result,
)
from orville_core.health_persistence import HealthCheckPersistence


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
    def __init__(
        self,
        *,
        required_commands: tuple[str, ...] = ("git",),
        optional_commands: tuple[str, ...] = ("node", "pnpm", "gh", "manus-config", "manus-mcp-cli"),
        optional_modules: tuple[str, ...] = ("fastapi", "uvicorn"),
        check_resources: bool = True,
        check_environment: bool = True,
        check_integrations: bool = True,
        enable_persistence: bool = True,
        db_path: str | Path = ".orville/health.db",
    ) -> None:
        self.required_commands = required_commands
        self.optional_commands = optional_commands
        self.optional_modules = optional_modules
        self.check_resources = check_resources
        self.check_environment = check_environment
        self.check_integrations = check_integrations
        self.enable_persistence = enable_persistence
        self.db_path = db_path
        self.persistence: HealthCheckPersistence | None = None
        
        if self.enable_persistence:
            self.persistence = HealthCheckPersistence(self.db_path)

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

        if self.check_environment:
            environment_checks = self._check_environment()
            checks.extend(environment_checks)

        if self.check_resources:
            resource_checks = self._check_resources()
            checks.extend(resource_checks)

        if self.check_integrations:
            integration_checker = IntegrationHealthChecker()
            integration_results = integration_checker.run_all()
            
            for integration_result in integration_results:
                health_check = create_health_check_from_integration_result(integration_result)
                checks.append(health_check)
                
                # Persist integration results
                if self.persistence:
                    from orville_core.health_persistence import HealthCheckRecord
                    record = HealthCheckRecord(
                        check_name=health_check.name,
                        available=health_check.available,
                        version=health_check.version,
                        detail=health_check.detail,
                        required=False,
                        integration_name=integration_result.integration_name,
                        error=health_check.detail if not health_check.available else None,
                    )
                    self.persistence.save_record(record)

        return {
            "status": "ok" if all(check.available for check in checks if check.required) else "degraded",
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "cwd": os.getcwd(),
            "checks": [check.to_dict() for check in checks],
            "persistence": {
                "enabled": self.enable_persistence,
                "db_path": str(self.db_path) if self.persistence else None,
                "summary": self.persistence.get_summary() if self.persistence else None,
            } if self.enable_persistence else None,
        }

    def _check_environment(self) -> list[HealthCheck]:
        """Check environment-specific conditions."""
        checks: list[HealthCheck] = []

        # Detect cloud environment
        cloud_env = self._detect_cloud_environment()
        checks.append(
            HealthCheck(
                "cloud-environment",
                cloud_env is not None,
                cloud_env,
                f"cloud environment detected: {cloud_env}" if cloud_env else "local environment",
                required=False,
            )
        )

        # Check for production environment indicators
        is_production = self._is_production_environment()
        checks.append(
            HealthCheck(
                "production-environment",
                is_production,
                "true" if is_production else "false",
                "production environment detected" if is_production else "development/staging environment",
                required=False,
            )
        )

        return checks

    def _check_resources(self) -> list[HealthCheck]:
        """Check system resource availability."""
        checks: list[HealthCheck] = []

        try:
            # Check disk space
            disk_usage = shutil.disk_usage(os.getcwd())
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            disk_available = disk_percent < 90
            checks.append(
                HealthCheck(
                    "disk-space",
                    disk_available,
                    f"{disk_percent:.1f}%",
                    f"disk usage: {disk_percent:.1f}%" if not disk_available else "sufficient disk space",
                    required=False,
                )
            )

            # Check memory
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available = memory_percent < 90
            checks.append(
                HealthCheck(
                    "memory",
                    memory_available,
                    f"{memory_percent:.1f}%",
                    f"memory usage: {memory_percent:.1f}%" if not memory_available else "sufficient memory",
                    required=False,
                )
            )

            # Check CPU
            cpu_count = psutil.cpu_count(logical=False)
            cpu_percent = psutil.cpu_percent(interval=0.1)
            checks.append(
                HealthCheck(
                    "cpu",
                    True,
                    f"{cpu_percent:.1f}%",
                    f"CPU usage: {cpu_percent:.1f}%, cores: {cpu_count}",
                    required=False,
                )
            )
        except (ImportError, psutil.Error, OSError) as exc:
            # If psutil is not available or disk space check fails, create a single resources check
            checks.append(
                HealthCheck(
                    "resources",
                    False,
                    None,
                    f"resource check unavailable: {exc!s}",
                    required=False,
                )
            )

        return checks

    def _detect_cloud_environment(self) -> str | None:
        """Detect if running in a cloud environment."""
        # Check for common cloud environment variables
        cloud_indicators = {
            "AWS_ACCESS_KEY_ID": "AWS",
            "AZURE_STORAGE_ACCOUNT": "AZURE",
            "GOOGLE_APPLICATION_CREDENTIALS": "GCP",
            "CLOUDSDK_PROJECT": "CLOUD",
        }

        # Debug: print all environment variables
        import sys
        print("DEBUG: Checking cloud environment variables", file=sys.stderr)
        for env_var, provider in cloud_indicators.items():
            value = os.getenv(env_var)
            print(f"DEBUG: {env_var} = {value}", file=sys.stderr)
            if value:
                print(f"DEBUG: Found {provider}", file=sys.stderr)
                return provider

        # Check for cloud-specific metadata endpoints
        try:
            # AWS metadata
            if os.path.exists("/sys/class/dmi/id/product_name"):
                with open("/sys/class/dmi/id/product_name", "r") as f:
                    product_name = f.read().strip().lower()
                    if "amazon" in product_name or "ec2" in product_name:
                        return "AWS"

            # Azure metadata
            if os.path.exists("/sys/class/dmi/id/product_name"):
                with open("/sys/class/dmi/id/product_name", "r") as f:
                    product_name = f.read().strip().lower()
                    if "microsoft" in product_name or "virtual" in product_name:
                        return "AZURE"
        except OSError:
            pass

        return None

    def _is_production_environment(self) -> bool:
        """Check if running in a production environment."""
        # Check for production indicators
        production_indicators = [
            "PRODUCTION",
            "PROD",
            "STAGE",  # Sometimes used for production staging
        ]

        for indicator in production_indicators:
            if os.getenv(indicator):
                return True

        # Check for development indicators
        development_indicators = [
            "DEVELOPMENT",
            "DEV",
            "LOCAL",
            "STAGING",
        ]

        for indicator in development_indicators:
            if os.getenv(indicator):
                return False

        # Default to false (development) if no clear indicator
        return False
