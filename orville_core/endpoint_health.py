"""Endpoint health monitoring and validation system for cloud and local model endpoints."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .endpoint_config import LocalModelSpec, ProviderEndpointSpec
from .endpoint_probe import probe_endpoint


class EndpointHealthStatus(Enum):
    """Health status for endpoints."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class EndpointHealth:
    """Health status for a single endpoint."""
    endpoint_url: str
    status: EndpointHealthStatus
    last_probed: datetime
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    average_response_time_ms: float = 0.0
    probe_count: int = 0
    last_error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "endpoint_url": self.endpoint_url,
            "status": self.status.value,
            "last_probed": self.last_probed.isoformat(),
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "average_response_time_ms": self.average_response_time_ms,
            "probe_count": self.probe_count,
            "last_error": self.last_error,
            "metadata": self.metadata,
        }

    def redacted(self) -> dict[str, Any]:
        """Return redacted version (no sensitive data)."""
        return {
            "endpoint_url": self.endpoint_url,
            "status": self.status.value,
            "last_probed": self.last_probed.isoformat(),
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "average_response_time_ms": self.average_response_time_ms,
            "probe_count": self.probe_count,
            "last_error": self.last_error,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class EndpointHealthReport:
    """Comprehensive health report for multiple endpoints."""
    environment: str
    timestamp: datetime
    total_endpoints: int
    healthy_count: int
    degraded_count: int
    unhealthy_count: int
    unknown_count: int
    endpoints: dict[str, EndpointHealth] = field(default_factory=dict)
    overall_status: EndpointHealthStatus = EndpointHealthStatus.UNKNOWN

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "environment": self.environment,
            "timestamp": self.timestamp.isoformat(),
            "total_endpoints": self.total_endpoints,
            "healthy_count": self.healthy_count,
            "degraded_count": self.degraded_count,
            "unhealthy_count": self.unhealthy_count,
            "unknown_count": self.unknown_count,
            "endpoints": {url: health.to_dict() for url, health in self.endpoints.items()},
            "overall_status": self.overall_status.value,
        }

    def get_summary(self) -> dict[str, Any]:
        """Get a human-readable summary."""
        return {
            "environment": self.environment,
            "timestamp": self.timestamp.isoformat(),
            "overall_status": self.overall_status.value,
            "summary": {
                "total": self.total_endpoints,
                "healthy": self.healthy_count,
                "degraded": self.degraded_count,
                "unhealthy": self.unhealthy_count,
                "unknown": self.unknown_count,
            },
            "details": [
                {
                    "url": url,
                    "status": health.status.value,
                    "consecutive_failures": health.consecutive_failures,
                    "consecutive_successes": health.consecutive_successes,
                    "average_response_time_ms": health.average_response_time_ms,
                }
                for url, health in self.endpoints.items()
            ],
        }


class EndpointHealthMonitor:
    """Monitor health of multiple endpoints with configurable thresholds."""

    def __init__(
        self,
        environment: str = "local",
        check_interval_seconds: int = 60,
        failure_threshold: int = 3,
        success_threshold: int = 2,
        probe_timeout_seconds: float = 5.0,
    ):
        """
        Initialize endpoint health monitor.

        Args:
            environment: Environment name (local, development, staging, production)
            check_interval_seconds: How often to check endpoints (default: 60s)
            failure_threshold: Consecutive failures before marking unhealthy (default: 3)
            success_threshold: Consecutive successes before marking healthy (default: 2)
            probe_timeout_seconds: Timeout for individual probes (default: 5s)
        """
        self.environment = environment
        self.check_interval_seconds = check_interval_seconds
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.probe_timeout_seconds = probe_timeout_seconds
        self._endpoints: dict[str, EndpointHealth] = {}
        self._running: bool = False
        self._monitor_thread: Any = None

    def add_endpoint(self, spec: ProviderEndpointSpec | LocalModelSpec) -> None:
        """
        Add an endpoint to monitor.

        Args:
            spec: Provider endpoint spec or local model spec
        """
        if isinstance(spec, ProviderEndpointSpec):
            url = spec.endpoint_url
        else:
            url = str(spec.source_path)

        if url in self._endpoints:
            raise ValueError(f"Endpoint {url} is already being monitored")

        self._endpoints[url] = EndpointHealth(
            endpoint_url=url,
            status=EndpointHealthStatus.UNKNOWN,
            last_probed=datetime.now(),
        )

    def remove_endpoint(self, url: str) -> bool:
        """
        Remove an endpoint from monitoring.

        Args:
            url: Endpoint URL to remove

        Returns:
            True if endpoint was removed, False if not found
        """
        if url in self._endpoints:
            del self._endpoints[url]
            return True
        return False

    def get_endpoint_health(self, url: str) -> EndpointHealth | None:
        """
        Get health status for a specific endpoint.

        Args:
            url: Endpoint URL

        Returns:
            EndpointHealth if found, None otherwise
        """
        return self._endpoints.get(url)

    def get_all_health(self) -> dict[str, EndpointHealth]:
        """
        Get health status for all monitored endpoints.

        Returns:
            Dictionary mapping URLs to EndpointHealth
        """
        return self._endpoints.copy()

    def run_probes(self) -> EndpointHealthReport:
        """
        Run health probes for all monitored endpoints.

        Returns:
            EndpointHealthReport with results
        """
        results = []
        total = len(self._endpoints)
        healthy = 0
        degraded = 0
        unhealthy = 0
        unknown = 0

        for url, health in self._endpoints.items():
            try:
                # Probe the endpoint
                probe_result = probe_endpoint(
                    url,
                    timeout_seconds=self.probe_timeout_seconds,
                )

                # Update health status
                now = datetime.now()
                response_time_ms = 0.0

                if probe_result.reachable:
                    # Calculate response time
                    if "start_time" in health.metadata:
                        elapsed = (now - datetime.fromisoformat(health.metadata["start_time"])).total_seconds() * 1000
                        response_time_ms = elapsed

                    # Update consecutive successes
                    health = EndpointHealth(
                        endpoint_url=url,
                        status=EndpointHealthStatus.HEALTHY,
                        last_probed=now,
                        consecutive_failures=0,
                        consecutive_successes=health.consecutive_successes + 1,
                        average_response_time_ms=(
                            (health.average_response_time_ms * health.probe_count + response_time_ms)
                            / (health.probe_count + 1)
                        ),
                        probe_count=health.probe_count + 1,
                        last_error=None,
                        metadata=health.metadata,
                    )
                    healthy += 1
                else:
                    # Update consecutive failures
                    health = EndpointHealth(
                        endpoint_url=url,
                        status=EndpointHealthStatus.UNHEALTHY,
                        last_probed=now,
                        consecutive_failures=health.consecutive_failures + 1,
                        consecutive_successes=0,
                        average_response_time_ms=health.average_response_time_ms,
                        probe_count=health.probe_count,
                        last_error=probe_result.detail,
                        metadata=health.metadata,
                    )
                    unhealthy += 1

            except Exception as exc:
                # Handle probe errors
                health = EndpointHealth(
                    endpoint_url=url,
                    status=EndpointHealthStatus.UNKNOWN,
                    last_probed=datetime.now(),
                    consecutive_failures=health.consecutive_failures + 1,
                    consecutive_successes=0,
                    average_response_time_ms=health.average_response_time_ms,
                    probe_count=health.probe_count,
                    last_error=str(exc),
                    metadata=health.metadata,
                )
                unknown += 1

            results.append(health)
            self._endpoints[url] = health

        # Determine overall status
        if unhealthy > 0:
            overall_status = EndpointHealthStatus.UNHEALTHY
        elif degraded > 0:
            overall_status = EndpointHealthStatus.DEGRADED
        elif healthy > 0:
            overall_status = EndpointHealthStatus.HEALTHY
        else:
            overall_status = EndpointHealthStatus.UNKNOWN

        return EndpointHealthReport(
            environment=self.environment,
            timestamp=datetime.now(),
            total_endpoints=total,
            healthy_count=healthy,
            degraded_count=degraded,
            unhealthy_count=unhealthy,
            unknown_count=unknown,
            endpoints={h.endpoint_url: h for h in results},
            overall_status=overall_status,
        )

    def start_monitoring(self) -> None:
        """Start background monitoring thread."""
        if self._running:
            return

        self._running = True

        def monitor_loop():
            while self._running:
                try:
                    self.run_probes()
                    time.sleep(self.check_interval_seconds)
                except Exception as exc:
                    # Log error but continue monitoring
                    print(f"Error in monitoring loop: {exc}")

        self._monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self) -> None:
        """Stop background monitoring thread."""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

    def get_report(self) -> EndpointHealthReport:
        """
        Get current health report without running new probes.

        Returns:
            Current EndpointHealthReport
        """
        return EndpointHealthReport(
            environment=self.environment,
            timestamp=datetime.now(),
            total_endpoints=len(self._endpoints),
            healthy_count=sum(1 for h in self._endpoints.values() if h.status == EndpointHealthStatus.HEALTHY),
            degraded_count=sum(1 for h in self._endpoints.values() if h.status == EndpointHealthStatus.DEGRADED),
            unhealthy_count=sum(1 for h in self._endpoints.values() if h.status == EndpointHealthStatus.UNHEALTHY),
            unknown_count=sum(1 for h in self._endpoints.values() if h.status == EndpointHealthStatus.UNKNOWN),
            endpoints=self._endpoints.copy(),
            overall_status=self._determine_overall_status(),
        )

    def _determine_overall_status(self) -> EndpointHealthStatus:
        """Determine overall health status based on endpoint statuses."""
        if not self._endpoints:
            return EndpointHealthStatus.UNKNOWN

        unhealthy = sum(1 for h in self._endpoints.values() if h.status == EndpointHealthStatus.UNHEALTHY)
        degraded = sum(1 for h in self._endpoints.values() if h.status == EndpointHealthStatus.DEGRADED)
        healthy = sum(1 for h in self._endpoints.values() if h.status == EndpointHealthStatus.HEALTHY)

        if unhealthy > 0:
            return EndpointHealthStatus.UNHEALTHY
        elif degraded > 0:
            return EndpointHealthStatus.DEGRADED
        elif healthy > 0:
            return EndpointHealthStatus.HEALTHY
        else:
            return EndpointHealthStatus.UNKNOWN
