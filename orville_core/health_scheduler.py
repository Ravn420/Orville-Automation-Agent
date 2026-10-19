"""Health check scheduling and periodic execution for Orville deployments.

This module provides a scheduling system for running health checks at regular intervals,
with support for configurable schedules and execution modes.
"""

from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from orville_core.health_persistence import HealthCheckPersistence
from orville_core.runtime_health import RuntimeHealth


class ScheduleInterval(Enum):
    """Supported schedule intervals for health checks."""
    ONCE = "once"
    MINUTES = "minutes"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


@dataclass
class HealthCheckSchedule:
    """Configuration for a health check schedule."""
    check_name: str
    interval: ScheduleInterval
    enabled: bool = True
    timeout: float = 30.0
    next_run: datetime = field(default_factory=datetime.utcnow)
    last_run: datetime | None = None
    consecutive_failures: int = 0
    max_consecutive_failures: int = 3
    alert_on_failure: bool = True
    alert_on_degraded: bool = True
    alert_email: str | None = None
    alert_webhook: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "check_name": self.check_name,
            "interval": self.interval.value,
            "enabled": self.enabled,
            "timeout": self.timeout,
            "next_run": self.next_run.isoformat(),
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "consecutive_failures": self.consecutive_failures,
            "max_consecutive_failures": self.max_consecutive_failures,
            "alert_on_failure": self.alert_on_failure,
            "alert_on_degraded": self.alert_on_degraded,
            "alert_email": self.alert_email,
            "alert_webhook": self.alert_webhook,
        }


@dataclass
class HealthCheckExecution:
    """Result of a health check execution."""
    check_name: str
    available: bool
    version: str | None = None
    detail: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration_ms: float = 0.0
    error: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "check_name": self.check_name,
            "available": self.available,
            "version": self.version,
            "detail": self.detail,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "error": self.error,
        }


class HealthScheduler:
    """Scheduler for periodic health check execution."""
    
    def __init__(
        self,
        *,
        db_path: str | Path = ".orville/health.db",
        schedules_path: str | Path = ".orville/health_schedules.json",
        enable_persistence: bool = True,
    ) -> None:
        """Initialize the health scheduler.
        
        Args:
            db_path: Path to the health check database
            schedules_path: Path to the schedules configuration file
            enable_persistence: Whether to persist schedules
        """
        self.db_path = Path(db_path)
        self.schedules_path = Path(schedules_path)
        self.enable_persistence = enable_persistence
        self.schedules: dict[str, HealthCheckSchedule] = {}
        self.running: bool = False
        self._task: asyncio.Task | None = None
        self._lock = asyncio.Lock()
        
        # Load existing schedules
        if self.enable_persistence and self.schedules_path.exists():
            self._load_schedules()
    
    def _load_schedules(self) -> None:
        """Load schedules from the configuration file."""
        try:
            with open(self.schedules_path, "r") as f:
                data = json.load(f)
            
            for check_name, schedule_data in data.items():
                self.schedules[check_name] = HealthCheckSchedule(
                    check_name=check_name,
                    interval=ScheduleInterval(schedule_data["interval"]),
                    enabled=schedule_data.get("enabled", True),
                    timeout=schedule_data.get("timeout", 30.0),
                    next_run=datetime.fromisoformat(schedule_data["next_run"]) if schedule_data.get("next_run") else datetime.utcnow(),
                    last_run=datetime.fromisoformat(schedule_data["last_run"]) if schedule_data.get("last_run") else None,
                    consecutive_failures=schedule_data.get("consecutive_failures", 0),
                    max_consecutive_failures=schedule_data.get("max_consecutive_failures", 3),
                    alert_on_failure=schedule_data.get("alert_on_failure", True),
                    alert_on_degraded=schedule_data.get("alert_on_degraded", True),
                    alert_email=schedule_data.get("alert_email"),
                    alert_webhook=schedule_data.get("alert_webhook"),
                )
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            print(f"Warning: Failed to load schedules: {exc}", file=sys.stderr)
    
    def _save_schedules(self) -> None:
        """Save schedules to the configuration file."""
        if not self.enable_persistence:
            return
        
        try:
            data = {
                check_name: {
                    "interval": schedule.interval.value,
                    "enabled": schedule.enabled,
                    "timeout": schedule.timeout,
                    "next_run": schedule.next_run.isoformat(),
                    "last_run": schedule.last_run.isoformat() if schedule.last_run else None,
                    "consecutive_failures": schedule.consecutive_failures,
                    "max_consecutive_failures": schedule.max_consecutive_failures,
                    "alert_on_failure": schedule.alert_on_failure,
                    "alert_on_degraded": schedule.alert_on_degraded,
                    "alert_email": schedule.alert_email,
                    "alert_webhook": schedule.alert_webhook,
                }
                for check_name, schedule in self.schedules.items()
            }
            
            self.schedules_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.schedules_path, "w") as f:
                json.dump(data, f, indent=2)
        except OSError as exc:
            print(f"Warning: Failed to save schedules: {exc}", file=sys.stderr)
    
    def add_schedule(
        self,
        check_name: str,
        interval: ScheduleInterval,
        *,
        enabled: bool = True,
        timeout: float = 30.0,
        max_consecutive_failures: int = 3,
        alert_on_failure: bool = True,
        alert_on_degraded: bool = True,
        alert_email: str | None = None,
        alert_webhook: str | None = None,
    ) -> None:
        """Add a new health check schedule.
        
        Args:
            check_name: Name of the health check to schedule
            interval: Schedule interval
            enabled: Whether the schedule is enabled
            timeout: Timeout for each check in seconds
            max_consecutive_failures: Maximum consecutive failures before alerting
            alert_on_failure: Whether to alert on failures
            alert_on_degraded: Whether to alert on degraded status
            alert_email: Email address for alerts
            alert_webhook: Webhook URL for alerts
        """
        self.schedules[check_name] = HealthCheckSchedule(
            check_name=check_name,
            interval=interval,
            enabled=enabled,
            timeout=timeout,
            next_run=datetime.utcnow(),
            max_consecutive_failures=max_consecutive_failures,
            alert_on_failure=alert_on_failure,
            alert_on_degraded=alert_on_degraded,
            alert_email=alert_email,
            alert_webhook=alert_webhook,
        )
        self._save_schedules()
    
    def remove_schedule(self, check_name: str) -> bool:
        """Remove a health check schedule.
        
        Args:
            check_name: Name of the health check to remove
            
        Returns:
            True if the schedule was removed, False if it didn't exist
        """
        if check_name in self.schedules:
            del self.schedules[check_name]
            self._save_schedules()
            return True
        return False
    
    def get_schedule(self, check_name: str) -> HealthCheckSchedule | None:
        """Get a health check schedule.
        
        Args:
            check_name: Name of the health check
            
        Returns:
            The schedule or None if not found
        """
        return self.schedules.get(check_name)
    
    def list_schedules(self) -> list[HealthCheckSchedule]:
        """List all health check schedules.
        
        Returns:
            List of all schedules
        """
        return list(self.schedules.values())
    
    def _calculate_next_run(self, schedule: HealthCheckSchedule) -> datetime:
        """Calculate the next run time for a schedule.
        
        Args:
            schedule: The schedule to calculate next run for
            
        Returns:
            The next run datetime
        """
        datetime.utcnow()
        
        if schedule.interval == ScheduleInterval.ONCE:
            return schedule.next_run
        
        delta = timedelta()
        if schedule.interval == ScheduleInterval.MINUTES:
            delta = timedelta(minutes=1)
        elif schedule.interval == ScheduleInterval.HOURLY:
            delta = timedelta(hours=1)
        elif schedule.interval == ScheduleInterval.DAILY:
            delta = timedelta(days=1)
        elif schedule.interval == ScheduleInterval.WEEKLY:
            delta = timedelta(weeks=1)
        
        return schedule.next_run + delta
    
    async def _run_health_check(self, check_name: str) -> HealthCheckExecution:
        """Run a single health check.
        
        Args:
            check_name: Name of the health check to run
            
        Returns:
            The execution result
        """
        start_time = datetime.utcnow()
        
        try:
            # Run the health check
            health_checker = RuntimeHealth()
            result = health_checker.run()
            
            # Find the check result
            check_result = None
            for check in result.get("checks", []):
                if check["name"] == check_name:
                    check_result = check
                    break
            
            if check_result is None:
                return HealthCheckExecution(
                    check_name=check_name,
                    available=False,
                    error=f"Check '{check_name}' not found in results",
                )
            
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return HealthCheckExecution(
                check_name=check_name,
                available=check_result["available"],
                version=check_result.get("version"),
                detail=check_result.get("detail", ""),
                duration_ms=duration_ms,
            )
        except Exception as exc:
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            return HealthCheckExecution(
                check_name=check_name,
                available=False,
                error=str(exc),
                duration_ms=duration_ms,
            )
    
    async def _process_execution(
        self,
        schedule: HealthCheckSchedule,
        execution: HealthCheckExecution,
    ) -> None:
        """Process the result of a health check execution.
        
        Args:
            schedule: The schedule that was executed
            execution: The execution result
        """
        schedule.last_run = datetime.utcnow()
        schedule.next_run = self._calculate_next_run(schedule)
        
        if not execution.available:
            schedule.consecutive_failures += 1
        else:
            schedule.consecutive_failures = 0
        
        # Persist the result
        if self.enable_persistence:
            persistence = HealthCheckPersistence(self.db_path)
            from orville_core.health_persistence import HealthCheckRecord
            
            record = HealthCheckRecord(
                check_name=execution.check_name,
                available=execution.available,
                version=execution.version,
                detail=execution.detail,
                required=False,
                error=execution.error,
            )
            persistence.save_record(record)
        
        # Alert if needed
        if execution.error and schedule.alert_on_failure:
            await self._send_alert(
                schedule=schedule,
                level="error",
                message=f"Health check '{execution.check_name}' failed: {execution.error}",
            )
        elif not execution.available and schedule.alert_on_degraded:
            await self._send_alert(
                schedule=schedule,
                level="warning",
                message=f"Health check '{execution.check_name}' is unavailable",
            )
        
        self._save_schedules()
    
    async def _send_alert(
        self,
        schedule: HealthCheckSchedule,
        level: str,
        message: str,
    ) -> None:
        """Send an alert for a health check event.
        
        Args:
            schedule: The schedule that triggered the alert
            level: Alert level (error, warning)
            message: Alert message
        """
        # In a real implementation, this would send emails or webhooks
        # For now, we'll just print to stderr
        alert_msg = f"[{level.upper()}] Health Check Alert: {message}"
        print(alert_msg, file=sys.stderr)
        
        if schedule.alert_email:
            print(f"  Email: {schedule.alert_email}", file=sys.stderr)
        
        if schedule.alert_webhook:
            print(f"  Webhook: {schedule.alert_webhook}", file=sys.stderr)
    
    async def _run_loop(self) -> None:
        """Main scheduling loop."""
        while self.running:
            try:
                async with self._lock:
                    now = datetime.utcnow()
                    
                    # Find schedules that are due
                    for check_name, schedule in list(self.schedules.items()):
                        if not schedule.enabled:
                            continue
                        
                        if now >= schedule.next_run:
                            # Run the health check
                            execution = await self._run_health_check(check_name)
                            
                            # Process the result
                            await self._process_execution(schedule, execution)
                    
                    # Wait for the next check or exit
                    if self.running:
                        # Find the next run time
                        next_run = min(
                            (s.next_run for s in self.schedules.values() if s.enabled),
                            default=now + timedelta(minutes=1),
                        )
                        wait_seconds = max(1, (next_run - now).total_seconds())
                        await asyncio.sleep(wait_seconds)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                print(f"Error in health check loop: {exc}", file=sys.stderr)
                await asyncio.sleep(60)  # Wait before retrying
    
    async def start(self) -> None:
        """Start the health check scheduler."""
        if self.running:
            return
        
        self.running = True
        self._task = asyncio.create_task(self._run_loop())
    
    async def stop(self) -> None:
        """Stop the health check scheduler."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def run_once(self, check_name: str) -> HealthCheckExecution:
        """Run a single health check immediately.
        
        Args:
            check_name: Name of the health check to run
            
        Returns:
            The execution result
        """
        async with self._lock:
            schedule = self.schedules.get(check_name)
            if not schedule:
                raise ValueError(f"No schedule found for check: {check_name}")
            
            execution = await self._run_health_check(check_name)
            await self._process_execution(schedule, execution)
            
            return execution
    
    def get_status(self) -> dict[str, Any]:
        """Get the current status of the scheduler.
        
        Returns:
            Dictionary with scheduler status
        """
        return {
            "running": self.running,
            "schedules_count": len(self.schedules),
            "schedules": [
                {
                    "check_name": s.check_name,
                    "enabled": s.enabled,
                    "next_run": s.next_run.isoformat(),
                    "last_run": s.last_run.isoformat() if s.last_run else None,
                    "consecutive_failures": s.consecutive_failures,
                }
                for s in self.schedules.values()
            ],
        }
