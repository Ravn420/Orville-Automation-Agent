"""Endpoint health check scheduling and integration with health scheduler.

This module provides scheduling capabilities for endpoint health checks,
integrating the endpoint monitoring system with the health scheduler from Phase 3.1.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .endpoint_config import (
    EnvironmentConfig,
    LocalModelSpec,
    ProviderEndpointSpec,
)
from .endpoint_health import (
    EndpointHealth,
    EndpointHealthReport,
    EndpointHealthStatus,
)
from .endpoint_monitor import EndpointMonitor, EndpointMonitorConfig
from .health_scheduler import HealthScheduler, ScheduleInterval


class EndpointSchedulingError(Exception):
    """Base exception for endpoint scheduling errors."""


class EndpointValidationError(EndpointSchedulingError):
    """Error related to endpoint validation."""


@dataclass(frozen=True)
class EndpointScheduleConfig:
    """Configuration for endpoint health check scheduling."""
    check_interval_seconds: int = 60
    failure_threshold: int = 3
    success_threshold: int = 2
    probe_timeout_seconds: float = 5.0
    alert_on_failure: bool = True
    alert_on_degraded: bool = True
    alert_on_recovery: bool = True
    max_history_entries: int = 1000
    enable_scheduling: bool = True
    schedule_interval: ScheduleInterval = ScheduleInterval.MINUTES
    environment: str = "default"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "check_interval_seconds": self.check_interval_seconds,
            "failure_threshold": self.failure_threshold,
            "success_threshold": self.success_threshold,
            "probe_timeout_seconds": self.probe_timeout_seconds,
            "alert_on_failure": self.alert_on_failure,
            "alert_on_degraded": self.alert_on_degraded,
            "alert_on_recovery": self.alert_on_recovery,
            "max_history_entries": self.max_history_entries,
            "enable_scheduling": self.enable_scheduling,
            "schedule_interval": self.schedule_interval.value,
            "environment": self.environment,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EndpointScheduleConfig:
        """Create EndpointScheduleConfig from dictionary."""
        interval_value = data.get("schedule_interval", "minutes")
        return cls(
            check_interval_seconds=data.get("check_interval_seconds", 60),
            failure_threshold=data.get("failure_threshold", 3),
            success_threshold=data.get("success_threshold", 2),
            probe_timeout_seconds=data.get("probe_timeout_seconds", 5.0),
            alert_on_failure=data.get("alert_on_failure", True),
            alert_on_degraded=data.get("alert_on_degraded", True),
            alert_on_recovery=data.get("alert_on_recovery", True),
            max_history_entries=data.get("max_history_entries", 1000),
            enable_scheduling=data.get("enable_scheduling", True),
            schedule_interval=ScheduleInterval(interval_value),
            environment=data.get("environment", "default"),
        )


@dataclass
class ScheduledEndpointCheck:
    """Represents a scheduled endpoint health check."""
    endpoint_url: str
    schedule_config: EndpointScheduleConfig
    environment_config: EnvironmentConfig | None = None
    last_check: datetime | None = None
    next_check: datetime | None = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "endpoint_url": self.endpoint_url,
            "schedule_config": self.schedule_config.to_dict(),
            "environment_config": self.environment_config.to_dict() if self.environment_config else None,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "next_check": self.next_check.isoformat() if self.next_check else None,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "enabled": self.enabled,
            "metadata": self.metadata,
        }


class EndpointEnvironmentValidator:
    """Validates endpoints against environment-specific rules."""

    def __init__(self, environment_config: EnvironmentConfig):
        """
        Initialize the validator with environment configuration.

        Args:
            environment_config: Environment-specific configuration
        """
        self.environment_config = environment_config

    def validate_endpoint_url(self, url: str) -> tuple[bool, str]:
        """
        Validate an endpoint URL against environment rules.

        Args:
            url: The endpoint URL to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        from urllib.parse import urlparse

        try:
            parsed = urlparse(url)
        except Exception as exc:
            return False, f"Invalid URL: {exc}"

        # Check scheme
        if parsed.scheme not in {"http", "https"}:
            return False, f"URL scheme '{parsed.scheme}' not allowed. Only http/https allowed."

        # Check if private network is allowed
        if not self.environment_config.allow_private_network:
            hostname = parsed.hostname or ""
            # Check for private IP ranges
            if self._is_private_ip(hostname):
                return False, "Private network addresses are not allowed in this environment"

        # Check allowed hosts
        if self.environment_config.allowed_hosts:
            hostname = parsed.hostname or ""
            if hostname not in self.environment_config.allowed_hosts:
                allowed = ", ".join(self.environment_config.allowed_hosts)
                return False, f"Host '{hostname}' not in allowed hosts: {allowed}"

        # Check allowed ports
        if self.environment_config.allowed_ports:
            port = parsed.port
            if port is None:
                port = 443 if parsed.scheme == "https" else 80
            if port not in self.environment_config.allowed_ports:
                allowed = ", ".join(map(str, self.environment_config.allowed_ports))
                return False, f"Port {port} not in allowed ports: {allowed}"

        # Check SSL verification for HTTPS
        if parsed.scheme == "https" and not self.environment_config.enable_ssl_verification:
            return False, "SSL verification is required for HTTPS endpoints in this environment"

        return True, ""

    def validate_provider_endpoint(self, spec: ProviderEndpointSpec) -> tuple[bool, str]:
        """
        Validate a provider endpoint spec against environment rules.

        Args:
            spec: The provider endpoint spec to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate the URL
        is_valid, error = self.validate_endpoint_url(spec.endpoint_url)
        if not is_valid:
            return False, error

        # Check environment match
        if spec.environment != self.environment_config.name:
            return False, (
                f"Endpoint environment '{spec.environment}' does not match "
                f"validator environment '{self.environment_config.name}'"
            )

        # Validate timeout is reasonable
        effective_timeout = spec.get_effective_timeout()
        max_timeout = 300 * self.environment_config.timeout_multiplier  # 5 minutes base
        if effective_timeout > max_timeout:
            return False, f"Timeout {effective_timeout}s exceeds maximum {max_timeout}s for this environment"

        return True, ""

    def validate_local_model(self, spec: LocalModelSpec) -> tuple[bool, str]:
        """
        Validate a local model spec against environment rules.

        Args:
            spec: The local model spec to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check environment match
        if spec.environment != self.environment_config.name:
            return False, (
                f"Model environment '{spec.environment}' does not match "
                f"validator environment '{self.environment_config.name}'"
            )

        # Check if local models are allowed in this environment
        if not self.environment_config.allow_private_network:
            return False, "Local models are not allowed in this environment"

        # Validate source path exists (if we can check it)
        if not spec.source_path.exists():
            return False, f"Model source path does not exist: {spec.source_path}"

        return True, ""

    def _is_private_ip(self, hostname: str) -> bool:
        """Check if a hostname is a private IP address."""
        import ipaddress

        # Common private hostnames
        if hostname in {"localhost", "127.0.0.1", "::1"}:
            return True

        # Try to parse as IP address
        try:
            ip = ipaddress.ip_address(hostname)
            return ip.is_private
        except ValueError:
            # Not an IP address, check for localhost variants
            if hostname.startswith("127."):
                return True
            if hostname.startswith("192.168."):
                return True
            if hostname.startswith("10."):
                return True
            if hostname.startswith("172."):
                try:
                    second_octet = int(hostname.split(".")[1])
                    if 16 <= second_octet <= 31:
                        return True
                except (ValueError, IndexError):
                    pass

        return False

    def get_validation_summary(self) -> dict[str, Any]:
        """Get a summary of the validation configuration."""
        return {
            "environment": self.environment_config.name,
            "allow_private_network": self.environment_config.allow_private_network,
            "allowed_hosts": list(self.environment_config.allowed_hosts),
            "allowed_ports": list(self.environment_config.allowed_ports),
            "enable_ssl_verification": self.environment_config.enable_ssl_verification,
            "timeout_multiplier": self.environment_config.timeout_multiplier,
            "max_retries": self.environment_config.max_retries,
        }


class EndpointHealthScheduler:
    """Scheduler for endpoint health checks with health scheduler integration."""

    def __init__(
        self,
        config: EndpointScheduleConfig,
        database_path: Path | None = None,
        environment_config: EnvironmentConfig | None = None,
    ):
        """
        Initialize the endpoint health scheduler.

        Args:
            config: Schedule configuration
            database_path: Path to the monitoring database
            environment_config: Environment-specific configuration
        """
        self.config = config
        self.database_path = database_path or Path(".orville/endpoint_scheduler.db")
        self.environment_config = environment_config or EnvironmentConfig.get_default()
        self.validator = EndpointEnvironmentValidator(self.environment_config)
        self._scheduled_checks: dict[str, ScheduledEndpointCheck] = {}
        self._monitor: EndpointMonitor | None = None
        self._health_scheduler: HealthScheduler | None = None
        self._initialized = False
        self._running = False

    def initialize(self) -> None:
        """Initialize the scheduler and its components."""
        if self._initialized:
            return

        # Initialize the endpoint monitor
        monitor_config = EndpointMonitorConfig(
            database_path=self.database_path,
            check_interval_seconds=self.config.check_interval_seconds,
            failure_threshold=self.config.failure_threshold,
            success_threshold=self.config.success_threshold,
            probe_timeout_seconds=self.config.probe_timeout_seconds,
            alert_on_failure=self.config.alert_on_failure,
            alert_on_degraded=self.config.alert_on_degraded,
            alert_on_recovery=self.config.alert_on_recovery,
            max_history_entries=self.config.max_history_entries,
        )
        self._monitor = EndpointMonitor(monitor_config)
        self._monitor.initialize()

        # Initialize the health scheduler if scheduling is enabled
        if self.config.enable_scheduling:
            schedules_path = self.database_path.parent / "endpoint_schedules.json"
            self._health_scheduler = HealthScheduler(
                db_path=self.database_path,
                schedules_path=schedules_path,
                enable_persistence=True,
            )

        self._initialized = True

    def add_endpoint(
        self,
        url: str,
        environment_config: EnvironmentConfig | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Add an endpoint to the scheduling system.

        Args:
            url: The endpoint URL to monitor
            environment_config: Optional environment config for this endpoint
            metadata: Optional metadata for the endpoint

        Raises:
            EndpointValidationError: If the endpoint fails validation
            EndpointSchedulingError: If the endpoint is already scheduled
        """
        self.initialize()

        if url in self._scheduled_checks:
            raise EndpointSchedulingError(f"Endpoint {url} is already scheduled")

        # Validate the endpoint
        validator = EndpointEnvironmentValidator(
            environment_config or self.environment_config
        )
        is_valid, error = validator.validate_endpoint_url(url)
        if not is_valid:
            raise EndpointValidationError(f"Endpoint validation failed: {error}")

        # Add to monitor
        self._monitor.add_endpoint(url)

        # Create scheduled check
        scheduled_check = ScheduledEndpointCheck(
            endpoint_url=url,
            schedule_config=self.config,
            environment_config=environment_config or self.environment_config,
            next_check=datetime.now() + timedelta(seconds=self.config.check_interval_seconds),
            metadata=metadata or {},
        )
        self._scheduled_checks[url] = scheduled_check

        # Add to health scheduler if enabled
        if self._health_scheduler and self.config.enable_scheduling:
            check_name = f"endpoint_{url.replace('://', '_').replace('/', '_').replace(':', '_')}"
            self._health_scheduler.add_schedule(
                check_name=check_name,
                interval=self.config.schedule_interval,
                enabled=True,
                timeout=self.config.probe_timeout_seconds,
                alert_on_failure=self.config.alert_on_failure,
                alert_on_degraded=self.config.alert_on_degraded,
            )

    def remove_endpoint(self, url: str) -> bool:
        """
        Remove an endpoint from the scheduling system.

        Args:
            url: The endpoint URL to remove

        Returns:
            True if the endpoint was removed, False if not found
        """
        self.initialize()

        if url not in self._scheduled_checks:
            return False

        # Remove from monitor
        self._monitor.remove_endpoint(url)

        # Remove from health scheduler if enabled
        if self._health_scheduler and self.config.enable_scheduling:
            check_name = f"endpoint_{url.replace('://', '_').replace('/', '_').replace(':', '_')}"
            self._health_scheduler.remove_schedule(check_name)

        # Remove from scheduled checks
        del self._scheduled_checks[url]

        return True

    def run_health_check(self, url: str) -> EndpointHealth:
        """
        Run a health check for a specific endpoint.

        Args:
            url: The endpoint URL to check

        Returns:
            The endpoint health status

        Raises:
            EndpointSchedulingError: If the endpoint is not scheduled
        """
        self.initialize()

        if url not in self._scheduled_checks:
            raise EndpointSchedulingError(f"Endpoint {url} is not scheduled")

        # Run probe through the monitor
        self._monitor.run_probes()

        # Get the health for this specific endpoint
        health = self._monitor.get_endpoint_health(url)
        if health is None:
            raise EndpointSchedulingError(f"Health data not found for endpoint {url}")

        # Update scheduled check
        scheduled_check = self._scheduled_checks[url]
        scheduled_check.last_check = datetime.now()
        scheduled_check.next_check = datetime.now() + timedelta(
            seconds=self.config.check_interval_seconds
        )

        if health.status == EndpointHealthStatus.HEALTHY:
            scheduled_check.consecutive_successes += 1
            scheduled_check.consecutive_failures = 0
        else:
            scheduled_check.consecutive_failures += 1
            scheduled_check.consecutive_successes = 0

        return health

    def run_all_health_checks(self) -> EndpointHealthReport:
        """
        Run health checks for all scheduled endpoints.

        Returns:
            Health report for all endpoints
        """
        self.initialize()

        report = self._monitor.run_probes()

        # Update all scheduled checks
        now = datetime.now()
        for url, health in report.endpoints.items():
            if url in self._scheduled_checks:
                scheduled_check = self._scheduled_checks[url]
                scheduled_check.last_check = now
                scheduled_check.next_check = now + timedelta(
                    seconds=self.config.check_interval_seconds
                )

                if health.status == EndpointHealthStatus.HEALTHY:
                    scheduled_check.consecutive_successes += 1
                    scheduled_check.consecutive_failures = 0
                else:
                    scheduled_check.consecutive_failures += 1
                    scheduled_check.consecutive_successes = 0

        return report

    def get_endpoint_health(self, url: str) -> EndpointHealth | None:
        """
        Get the current health status for an endpoint.

        Args:
            url: The endpoint URL

        Returns:
            The endpoint health status, or None if not found
        """
        self.initialize()
        return self._monitor.get_endpoint_health(url)

    def get_all_health(self) -> dict[str, EndpointHealth]:
        """
        Get health status for all scheduled endpoints.

        Returns:
            Dictionary mapping URLs to health statuses
        """
        self.initialize()
        return self._monitor.get_all_health()

    def get_scheduled_checks(self) -> dict[str, ScheduledEndpointCheck]:
        """
        Get all scheduled endpoint checks.

        Returns:
            Dictionary mapping URLs to scheduled checks
        """
        self.initialize()
        return self._scheduled_checks.copy()

    def get_health_report(self) -> EndpointHealthReport:
        """
        Get the current health report without running new checks.

        Returns:
            Current health report
        """
        self.initialize()
        return self._monitor.get_report()

    def get_endpoint_history(self, url: str, limit: int = 100) -> list[dict[str, Any]]:
        """
        Get health history for a specific endpoint.

        Args:
            url: The endpoint URL
            limit: Maximum number of history entries

        Returns:
            List of health history entries
        """
        self.initialize()
        return self._monitor.get_history(url, limit)

    def export_health_report(self, output_path: Path) -> None:
        """
        Export the health report to a JSON file.

        Args:
            output_path: Path to the output file
        """
        self.initialize()
        self._monitor.export_report(output_path)

    async def start_scheduling(self) -> None:
        """Start the health check scheduling loop."""
        self.initialize()

        if not self.config.enable_scheduling or not self._health_scheduler:
            return

        self._running = True
        await self._health_scheduler.start()

    async def stop_scheduling(self) -> None:
        """Stop the health check scheduling loop."""
        self._running = False
        if self._health_scheduler:
            await self._health_scheduler.stop()

    def get_status(self) -> dict[str, Any]:
        """
        Get the current status of the scheduler.

        Returns:
            Dictionary with scheduler status
        """
        self.initialize()

        status = {
            "initialized": self._initialized,
            "running": self._running,
            "config": self.config.to_dict(),
            "environment": self.environment_config.to_dict(),
            "scheduled_endpoints": len(self._scheduled_checks),
            "endpoints": [
                {
                    "url": url,
                    "enabled": check.enabled,
                    "last_check": check.last_check.isoformat() if check.last_check else None,
                    "next_check": check.next_check.isoformat() if check.next_check else None,
                    "consecutive_failures": check.consecutive_failures,
                    "consecutive_successes": check.consecutive_successes,
                }
                for url, check in self._scheduled_checks.items()
            ],
        }

        if self._health_scheduler:
            status["health_scheduler"] = self._health_scheduler.get_status()

        return status

    def close(self) -> None:
        """Close the scheduler and release resources."""
        if self._monitor:
            self._monitor.close()
        self._initialized = False


class EndpointHealthSchedulerManager:
    """Manager for multiple endpoint health schedulers across environments."""

    def __init__(self, base_path: Path | None = None):
        """
        Initialize the scheduler manager.

        Args:
            base_path: Base path for scheduler databases
        """
        self.base_path = base_path or Path(".orville/endpoint_schedulers")
        self._schedulers: dict[str, EndpointHealthScheduler] = {}

    def get_or_create_scheduler(
        self,
        environment: str,
        config: EndpointScheduleConfig | None = None,
        environment_config: EnvironmentConfig | None = None,
    ) -> EndpointHealthScheduler:
        """
        Get or create a scheduler for a specific environment.

        Args:
            environment: Environment name
            config: Optional schedule configuration
            environment_config: Optional environment configuration

        Returns:
            EndpointHealthScheduler for the environment
        """
        if environment in self._schedulers:
            return self._schedulers[environment]

        # Create environment config if not provided
        if environment_config is None:
            if environment == "local":
                environment_config = EnvironmentConfig.get_local()
            elif environment == "staging":
                environment_config = EnvironmentConfig.get_staging()
            elif environment == "production":
                environment_config = EnvironmentConfig.get_production()
            else:
                environment_config = EnvironmentConfig.get_default()

        # Create config if not provided
        if config is None:
            config = EndpointScheduleConfig(environment=environment)

        # Create scheduler
        database_path = self.base_path / f"{environment}_scheduler.db"
        scheduler = EndpointHealthScheduler(
            config=config,
            database_path=database_path,
            environment_config=environment_config,
        )

        self._schedulers[environment] = scheduler
        return scheduler

    def get_scheduler(self, environment: str) -> EndpointHealthScheduler | None:
        """
        Get a scheduler for a specific environment.

        Args:
            environment: Environment name

        Returns:
            EndpointHealthScheduler if found, None otherwise
        """
        return self._schedulers.get(environment)

    def remove_scheduler(self, environment: str) -> bool:
        """
        Remove a scheduler for a specific environment.

        Args:
            environment: Environment name

        Returns:
            True if the scheduler was removed, False if not found
        """
        if environment in self._schedulers:
            self._schedulers[environment].close()
            del self._schedulers[environment]
            return True
        return False

    def get_all_schedulers(self) -> dict[str, EndpointHealthScheduler]:
        """
        Get all managed schedulers.

        Returns:
            Dictionary mapping environment names to schedulers
        """
        return self._schedulers.copy()

    def get_all_status(self) -> dict[str, dict[str, Any]]:
        """
        Get status for all managed schedulers.

        Returns:
            Dictionary mapping environment names to status dictionaries
        """
        return {
            environment: scheduler.get_status()
            for environment, scheduler in self._schedulers.items()
        }

    def close_all(self) -> None:
        """Close all managed schedulers."""
        for scheduler in self._schedulers.values():
            scheduler.close()
        self._schedulers.clear()
