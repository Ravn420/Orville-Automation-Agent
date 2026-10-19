"""Tests for health check result export functionality."""
import csv
import json
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from orville_core.health_export import (
    HealthCheckExporter,
    ExportFormat,
    ExportOptions,
)


def test_export_format_enum():
    """Test ExportFormat enum values."""
    assert ExportFormat.JSON.value == "json"
    assert ExportFormat.CSV.value == "csv"
    assert ExportFormat.HTML.value == "html"
    assert ExportFormat.MARKDOWN.value == "markdown"


def test_export_options_creation():
    """Test creating export options."""
    options = ExportOptions(
        format=ExportFormat.JSON,
        output_path="output.json",
        include_history=True,
        include_summary=True,
    )
    
    assert options.format == ExportFormat.JSON
    assert options.output_path == "output.json"
    assert options.include_history is True
    assert options.include_summary is True


def test_health_check_exporter_initialization(tmp_path):
    """Test initializing the health check exporter."""
    db_path = tmp_path / "test_health.db"
    
    exporter = HealthCheckExporter(db_path=db_path)
    
    assert str(exporter.db_path) == str(db_path)
    assert exporter.persistence is not None


def test_health_check_exporter_export_json(tmp_path):
    """Test exporting to JSON format."""
    db_path = tmp_path / "test_health.db"
    exporter = HealthCheckExporter(db_path=db_path)
    
    # Add some test records
    for i in range(3):
        from orville_core.health_persistence import HealthCheckRecord
        record = HealthCheckRecord(
            check_name="test-check",
            available=True,
            version=f"1.0.{i}",
            detail=f"Test detail {i}",
            required=True,
        )
        exporter.persistence.save_record(record)
    
    output_path = tmp_path / "output.json"
    options = ExportOptions(
        format=ExportFormat.JSON,
        output_path=output_path,
        include_history=True,
        include_summary=True,
    )
    
    exporter.export(options)
    
    assert output_path.exists()
    
    with open(output_path) as f:
        data = json.load(f)
    
    assert "summary" in data
    assert "records" in data
    assert len(data["records"]) == 3


def test_health_check_exporter_export_csv(tmp_path):
    """Test exporting to CSV format."""
    db_path = tmp_path / "test_health.db"
    exporter = HealthCheckExporter(db_path=db_path)
    
    # Add some test records
    for i in range(3):
        from orville_core.health_persistence import HealthCheckRecord
        record = HealthCheckRecord(
            check_name="test-check",
            available=True,
            version=f"1.0.{i}",
            detail=f"Test detail {i}",
            required=True,
        )
        exporter.persistence.save_record(record)
    
    output_path = tmp_path / "output.csv"
    options = ExportOptions(
        format=ExportFormat.CSV,
        output_path=output_path,
    )
    
    exporter.export(options)
    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 3
    assert rows[0]["check_name"] == "test-check"
    assert rows[0]["available"] == "yes"


def test_health_check_exporter_export_html(tmp_path):
    """Test exporting to HTML format."""
    db_path = tmp_path / "test_health.db"
    exporter = HealthCheckExporter(db_path=db_path)
    
    # Add some test records
    for i in range(3):
        from orville_core.health_persistence import HealthCheckRecord
        record = HealthCheckRecord(
            check_name="test-check",
            available=True,
            version=f"1.0.{i}",
            detail=f"Test detail {i}",
            required=True,
        )
        exporter.persistence.save_record(record)
    
    output_path = tmp_path / "output.html"
    options = ExportOptions(
        format=ExportFormat.HTML,
        output_path=output_path,
    )
    
    exporter.export(options)
    
    assert output_path.exists()
    
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "<!DOCTYPE html>" in content
    assert "Health Check Export" in content
    assert "test-check" in content


def test_health_check_exporter_export_markdown(tmp_path):
    """Test exporting to Markdown format."""
    db_path = tmp_path / "test_health.db"
    exporter = HealthCheckExporter(db_path=db_path)
    
    # Add some test records
    for i in range(3):
        from orville_core.health_persistence import HealthCheckRecord
        record = HealthCheckRecord(
            check_name="test-check",
            available=True,
            version=f"1.0.{i}",
            detail=f"Test detail {i}",
            required=True,
        )
        exporter.persistence.save_record(record)
    
    output_path = tmp_path / "output.md"
    options = ExportOptions(
        format=ExportFormat.MARKDOWN,
        output_path=output_path,
    )
    
    exporter.export(options)
    
    assert output_path.exists()
    
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "# Health Check Export" in content
    assert "test-check" in content


def test_health_check_exporter_export_latest(tmp_path):
    """Test exporting latest health check results."""
    db_path = tmp_path / "test_health.db"
    exporter = HealthCheckExporter(db_path=db_path)
    
    # Add some test records
    for i in range(3):
        from orville_core.health_persistence import HealthCheckRecord
        record = HealthCheckRecord(
            check_name="test-check",
            available=True,
            version=f"1.0.{i}",
            detail=f"Test detail {i}",
            required=True,
        )
        exporter.persistence.save_record(record)
    
    output_path = tmp_path / "latest.json"
    exporter.export_latest(output_path, format=ExportFormat.JSON)
    
    assert output_path.exists()
    
    with open(output_path) as f:
        data = json.load(f)
    
    assert "summary" in data
    assert "records" in data


def test_health_check_exporter_export_by_check(tmp_path):
    """Test exporting health check history for a specific check."""
    db_path = tmp_path / "test_health.db"
    exporter = HealthCheckExporter(db_path=db_path)
    
    # Add some test records for different checks
    for i in range(3):
        from orville_core.health_persistence import HealthCheckRecord
        record = HealthCheckRecord(
            check_name="check-1",
            available=True,
            version=f"1.0.{i}",
            detail=f"Test detail {i}",
            required=True,
        )
        exporter.persistence.save_record(record)
    
    for i in range(2):
        from orville_core.health_persistence import HealthCheckRecord
        record = HealthCheckRecord(
            check_name="check-2",
            available=True,
            version=f"2.0.{i}",
            detail=f"Test detail {i}",
            required=True,
        )
        exporter.persistence.save_record(record)
    
    output_path = tmp_path / "check-1.json"
    exporter.export_by_check("check-1", output_path, format=ExportFormat.JSON)
    
    assert output_path.exists()
    
    with open(output_path) as f:
        data = json.load(f)
    
    assert "summary" in data
    assert "records" in data
    assert all(r["check_name"] == "check-1" for r in data["records"])


def test_health_check_exporter_export_summary(tmp_path):
    """Test exporting health check summary statistics."""
    db_path = tmp_path / "test_health.db"
    exporter = HealthCheckExporter(db_path=db_path)
    
    # Add some test records
    for i in range(3):
        from orville_core.health_persistence import HealthCheckRecord
        record = HealthCheckRecord(
            check_name="test-check",
            available=True,
            version=f"1.0.{i}",
            detail=f"Test detail {i}",
            required=True,
        )
        exporter.persistence.save_record(record)
    
    output_path = tmp_path / "summary.json"
    exporter.export_summary(output_path, format=ExportFormat.JSON)
    
    assert output_path.exists()
    
    with open(output_path) as f:
        data = json.load(f)
    
    assert "summary" in data
    assert "export_metadata" in data
    assert data["summary"]["total_checks"] == 3


def test_health_check_exporter_filter_by_check_names(tmp_path):
    """Test exporting with specific check names."""
    db_path = tmp_path / "test_health.db"
    exporter = HealthCheckExporter(db_path=db_path)
    
    # Add some test records
    for i in range(3):
        from orville_core.health_persistence import HealthCheckRecord
        record = HealthCheckRecord(
            check_name="check-1",
            available=True,
            version=f"1.0.{i}",
            detail=f"Test detail {i}",
            required=True,
        )
        exporter.persistence.save_record(record)
    
    for i in range(2):
        from orville_core.health_persistence import HealthCheckRecord
        record = HealthCheckRecord(
            check_name="check-2",
            available=True,
            version=f"2.0.{i}",
            detail=f"Test detail {i}",
            required=True,
        )
        exporter.persistence.save_record(record)
    
    output_path = tmp_path / "filtered.json"
    options = ExportOptions(
        format=ExportFormat.JSON,
        output_path=output_path,
        check_names=["check-1"],
    )
    
    exporter.export(options)
    
    assert output_path.exists()
    
    with open(output_path) as f:
        data = json.load(f)
    
    assert all(r["check_name"] == "check-1" for r in data["records"])


def test_health_check_exporter_filter_by_date_range(tmp_path):
    """Test exporting with date range filter."""
    db_path = tmp_path / "test_health.db"
    exporter = HealthCheckExporter(db_path=db_path)
    
    # Add some test records
    for i in range(3):
        from orville_core.health_persistence import HealthCheckRecord
        record = HealthCheckRecord(
            check_name="test-check",
            available=True,
            version=f"1.0.{i}",
            detail=f"Test detail {i}",
            required=True,
        )
        exporter.persistence.save_record(record)
    
    output_path = tmp_path / "date_filtered.json"
    start_date = datetime.utcnow() - timedelta(days=1)
    end_date = datetime.utcnow() + timedelta(days=1)
    
    options = ExportOptions(
        format=ExportFormat.JSON,
        output_path=output_path,
        date_range_start=start_date,
        date_range_end=end_date,
    )
    
    exporter.export(options)
    
    assert output_path.exists()
    
    with open(output_path) as f:
        data = json.load(f)
    
    # All records should be within the date range
    for record in data["records"]:
        record_time = datetime.fromisoformat(record["timestamp"])
        assert start_date <= record_time <= end_date


def test_health_check_exporter_truncate_long_details(tmp_path):
    """Test that long details are truncated in CSV export."""
    db_path = tmp_path / "test_health.db"
    exporter = HealthCheckExporter(db_path=db_path)
    
    # Add a record with very long detail
    from orville_core.health_persistence import HealthCheckRecord
    long_detail = "A" * 2000
    record = HealthCheckRecord(
        check_name="test-check",
        available=True,
        version="1.0.0",
        detail=long_detail,
        required=True,
    )
    exporter.persistence.save_record(record)
    
    output_path = tmp_path / "output.csv"
    options = ExportOptions(
        format=ExportFormat.CSV,
        output_path=output_path,
    )
    
    exporter.export(options)
    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 1
    # Detail should be truncated to 1000 characters
    assert len(rows[0]["detail"]) <= 1000


def test_health_check_exporter_include_options(tmp_path):
    """Test that export options control what is included."""
    db_path = tmp_path / "test_health.db"
    exporter = HealthCheckExporter(db_path=db_path)
    
    # Add some test records
    for i in range(3):
        from orville_core.health_persistence import HealthCheckRecord
        record = HealthCheckRecord(
            check_name="test-check",
            available=True,
            version=f"1.0.{i}",
            detail=f"Test detail {i}",
            required=True,
        )
        exporter.persistence.save_record(record)
    
    output_path = tmp_path / "minimal.json"
    options = ExportOptions(
        format=ExportFormat.JSON,
        output_path=output_path,
        include_history=False,
        include_summary=False,
        include_details=False,
    )
    
    exporter.export(options)
    
    assert output_path.exists()
    
    with open(output_path) as f:
        data = json.load(f)
    
    # Should only have export metadata
    assert "export_metadata" in data
    assert "summary" not in data
    assert "records" not in data
