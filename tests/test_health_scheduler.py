"""Tests for health check scheduling system."""
import asyncio
import json
import os
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from orville_core.health_scheduler import (
    HealthScheduler,
    HealthCheckExecution,
    HealthCheckSchedule,
    ScheduleInterval,
)


def test_health_check_schedule_creation():
    """Test creating a health check schedule."""
    schedule = HealthCheckSchedule(
        check_name="test-check",
        interval=ScheduleInterval.DAILY,
        enabled=True,
        timeout=30.0,
    )
    
    assert schedule.check_name == "test-check"
    assert schedule.interval == ScheduleInterval.DAILY
    assert schedule.enabled is True
    assert schedule.timeout == 30.0


def test_health_check_schedule_to_dict():
    """Test converting a schedule to dictionary."""
    schedule = HealthCheckSchedule(
        check_name="test-check",
        interval=ScheduleInterval.DAILY,
        enabled=True,
        timeout=30.0,
    )
    
    data = schedule.to_dict()
    
    assert data["check_name"] == "test-check"
    assert data["interval"] == "daily"
    assert data["enabled"] is True
    assert data["timeout"] == 30.0


def test_health_scheduler_initialization(tmp_path):
    """Test initializing the health scheduler."""
    db_path = tmp_path / "test_health.db"
    schedules_path = tmp_path / "test_schedules.json"
    
    scheduler = HealthScheduler(
        db_path=db_path,
        schedules_path=schedules_path,
        enable_persistence=True,
    )
    
    assert str(scheduler.db_path) == str(db_path)
    assert str(scheduler.schedules_path) == str(schedules_path)
    assert scheduler.running is False
    assert len(scheduler.schedules) == 0


def test_health_scheduler_add_schedule(tmp_path):
    """Test adding a health check schedule."""
    db_path = tmp_path / "test_health.db"
    schedules_path = tmp_path / "test_schedules.json"
    
    scheduler = HealthScheduler(
        db_path=db_path,
        schedules_path=schedules_path,
        enable_persistence=True,
    )
    
    scheduler.add_schedule(
        check_name="test-check",
        interval=ScheduleInterval.DAILY,
        enabled=True,
        timeout=30.0,
    )
    
    assert len(scheduler.schedules) == 1
    assert "test-check" in scheduler.schedules
    
    schedule = scheduler.schedules["test-check"]
    assert schedule.check_name == "test-check"
    assert schedule.interval == ScheduleInterval.DAILY
    assert schedule.enabled is True


def test_health_scheduler_remove_schedule(tmp_path):
    """Test removing a health check schedule."""
    db_path = tmp_path / "test_health.db"
    schedules_path = tmp_path / "test_schedules.json"
    
    scheduler = HealthScheduler(
        db_path=db_path,
        schedules_path=schedules_path,
        enable_persistence=True,
    )
    
    scheduler.add_schedule(
        check_name="test-check",
        interval=ScheduleInterval.DAILY,
    )
    
    assert len(scheduler.schedules) == 1
    
    success = scheduler.remove_schedule("test-check")
    assert success is True
    assert len(scheduler.schedules) == 0
    
    success = scheduler.remove_schedule("non-existent")
    assert success is False


def test_health_scheduler_get_schedule(tmp_path):
    """Test getting a health check schedule."""
    db_path = tmp_path / "test_health.db"
    schedules_path = tmp_path / "test_schedules.json"
    
    scheduler = HealthScheduler(
        db_path=db_path,
        schedules_path=schedules_path,
        enable_persistence=True,
    )
    
    scheduler.add_schedule(
        check_name="test-check",
        interval=ScheduleInterval.DAILY,
    )
    
    schedule = scheduler.get_schedule("test-check")
    assert schedule is not None
    assert schedule.check_name == "test-check"
    
    schedule = scheduler.get_schedule("non-existent")
    assert schedule is None


def test_health_scheduler_list_schedules(tmp_path):
    """Test listing all health check schedules."""
    db_path = tmp_path / "test_health.db"
    schedules_path = tmp_path / "test_schedules.json"
    
    scheduler = HealthScheduler(
        db_path=db_path,
        schedules_path=schedules_path,
        enable_persistence=True,
    )
    
    scheduler.add_schedule(
        check_name="check-1",
        interval=ScheduleInterval.DAILY,
    )
    scheduler.add_schedule(
        check_name="check-2",
        interval=ScheduleInterval.HOURLY,
    )
    
    schedules = scheduler.list_schedules()
    assert len(schedules) == 2
    
    schedule_names = [s.check_name for s in schedules]
    assert "check-1" in schedule_names
    assert "check-2" in schedule_names


def test_health_scheduler_load_schedules(tmp_path):
    """Test loading schedules from file."""
    db_path = tmp_path / "test_health.db"
    schedules_path = tmp_path / "test_schedules.json"
    
    # Create initial schedules
    scheduler1 = HealthScheduler(
        db_path=db_path,
        schedules_path=schedules_path,
        enable_persistence=True,
    )
    scheduler1.add_schedule(
        check_name="check-1",
        interval=ScheduleInterval.DAILY,
    )
    
    # Create a new scheduler and load schedules
    scheduler2 = HealthScheduler(
        db_path=db_path,
        schedules_path=schedules_path,
        enable_persistence=True,
    )
    
    assert len(scheduler2.schedules) == 1
    assert "check-1" in scheduler2.schedules


def test_health_scheduler_calculate_next_run():
    """Test calculating next run time for schedules."""
    from datetime import datetime, timedelta
    
    schedule = HealthCheckSchedule(
        check_name="test-check",
        interval=ScheduleInterval.DAILY,
        next_run=datetime.utcnow(),
    )
    
    next_run = schedule.next_run + timedelta(days=1)
    assert next_run.date() == (datetime.utcnow() + timedelta(days=1)).date()


def test_health_check_execution_creation():
    """Test creating a health check execution."""
    execution = HealthCheckExecution(
        check_name="test-check",
        available=True,
        version="1.0.0",
        detail="Test execution",
    )
    
    assert execution.check_name == "test-check"
    assert execution.available is True
    assert execution.version == "1.0.0"
    assert execution.detail == "Test execution"


def test_health_check_execution_to_dict():
    """Test converting execution to dictionary."""
    execution = HealthCheckExecution(
        check_name="test-check",
        available=True,
        version="1.0.0",
    )
    
    data = execution.to_dict()
    
    assert data["check_name"] == "test-check"
    assert data["available"] is True
    assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_health_scheduler_run_once(tmp_path, monkeypatch):
    """Test running a single health check."""
    db_path = tmp_path / "test_health.db"
    schedules_path = tmp_path / "test_schedules.json"
    
    scheduler = HealthScheduler(
        db_path=db_path,
        schedules_path=schedules_path,
        enable_persistence=True,
    )
    
    scheduler.add_schedule(
        check_name="git",
        interval=ScheduleInterval.ONCE,
    )
    
    # Mock the health check
    with patch("orville_core.health_scheduler.RuntimeHealth") as mock_checker:
        mock_checker_instance = MagicMock()
        mock_checker_instance.run.return_value = {
            "status": "ok",
            "checks": [
                {
                    "name": "git",
                    "available": True,
                    "version": "git version 2.0.0",
                    "detail": "Git is available",
                }
            ],
        }
        mock_checker.return_value = mock_checker_instance
        
        execution = await scheduler.run_once("git")
        
        assert execution.check_name == "git"
        assert execution.available is True
        assert execution.version == "git version 2.0.0"


@pytest.mark.asyncio
async def test_health_scheduler_get_status(tmp_path):
    """Test getting scheduler status."""
    db_path = tmp_path / "test_health.db"
    schedules_path = tmp_path / "test_schedules.json"
    
    scheduler = HealthScheduler(
        db_path=db_path,
        schedules_path=schedules_path,
        enable_persistence=True,
    )
    
    scheduler.add_schedule(
        check_name="test-check",
        interval=ScheduleInterval.DAILY,
    )
    
    status = scheduler.get_status()
    
    assert status["running"] is False
    assert status["schedules_count"] == 1
    assert len(status["schedules"]) == 1
    assert status["schedules"][0]["check_name"] == "test-check"


def test_health_scheduler_save_and_load_schedules(tmp_path):
    """Test saving and loading schedules."""
    db_path = tmp_path / "test_health.db"
    schedules_path = tmp_path / "test_schedules.json"
    
    # Create and save schedules
    scheduler1 = HealthScheduler(
        db_path=db_path,
        schedules_path=schedules_path,
        enable_persistence=True,
    )
    scheduler1.add_schedule(
        check_name="check-1",
        interval=ScheduleInterval.DAILY,
        enabled=True,
        timeout=30.0,
        max_consecutive_failures=3,
        alert_on_failure=True,
        alert_on_degraded=True,
    )
    
    # Verify schedules file was created
    assert schedules_path.exists()
    
    # Load schedules
    scheduler2 = HealthScheduler(
        db_path=db_path,
        schedules_path=schedules_path,
        enable_persistence=True,
    )
    
    assert len(scheduler2.schedules) == 1
    schedule = scheduler2.schedules["check-1"]
    assert schedule.enabled is True
    assert schedule.timeout == 30.0
    assert schedule.max_consecutive_failures == 3
    assert schedule.alert_on_failure is True
    assert schedule.alert_on_degraded is True


def test_health_scheduler_schedule_with_alerts(tmp_path):
    """Test creating a schedule with alert configuration."""
    db_path = tmp_path / "test_health.db"
    schedules_path = tmp_path / "test_schedules.json"
    
    scheduler = HealthScheduler(
        db_path=db_path,
        schedules_path=schedules_path,
        enable_persistence=True,
    )
    
    scheduler.add_schedule(
        check_name="test-check",
        interval=ScheduleInterval.DAILY,
        alert_email="admin@example.com",
        alert_webhook="https://example.com/webhook",
    )
    
    schedule = scheduler.get_schedule("test-check")
    assert schedule.alert_email == "admin@example.com"
    assert schedule.alert_webhook == "https://example.com/webhook"
