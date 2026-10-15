"""Tests for health check result visualization."""
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from orville_core.health_visualization import (
    HealthCheckVisualizer,
    VisualizationOptions,
    HealthCheckTrend,
    HealthCheckSummary,
)


def test_visualization_options_creation():
    """Test creating visualization options."""
    options = VisualizationOptions(
        check_name="test-check",
        time_range_days=7,
        include_trend=True,
        include_summary=True,
        include_details=True,
        chart_type="line",
    )
    
    assert options.check_name == "test-check"
    assert options.time_range_days == 7
    assert options.include_trend is True
    assert options.include_summary is True
    assert options.include_details is True
    assert options.chart_type == "line"


def test_health_check_visualizer_initialization(tmp_path):
    """Test initializing the health check visualizer."""
    db_path = tmp_path / "test_health.db"
    
    visualizer = HealthCheckVisualizer(db_path=db_path)
    
    assert str(visualizer.db_path) == str(db_path)
    assert visualizer.persistence is not None


def test_health_check_visualizer_visualize(tmp_path):
    """Test generating visualization data."""
    db_path = tmp_path / "test_health.db"
    visualizer = HealthCheckVisualizer(db_path=db_path)
    
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
        visualizer.persistence.save_record(record)
    
    options = VisualizationOptions(
        check_name="test-check",
        time_range_days=7,
        include_summary=True,
        include_details=True,
    )
    
    visualization = visualizer.visualize(options)
    
    assert "metadata" in visualization
    assert "summary" in visualization
    assert "records" in visualization
    assert visualization["metadata"]["check_name"] == "test-check"


def test_health_check_visualizer_generate_chart_data(tmp_path):
    """Test generating chart data."""
    db_path = tmp_path / "test_health.db"
    visualizer = HealthCheckVisualizer(db_path=db_path)
    
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
        visualizer.persistence.save_record(record)
    
    options = VisualizationOptions(
        check_name="test-check",
        time_range_days=7,
        include_trend=False,
        include_summary=False,
        include_details=False,
    )
    
    chart_data = visualizer.generate_chart_data(options)
    
    assert "type" in chart_data
    assert "title" in chart_data
    assert "labels" in chart_data
    assert "datasets" in chart_data
    assert chart_data["type"] == "line"


def test_health_check_visualizer_generate_dashboard(tmp_path):
    """Test generating a complete dashboard."""
    db_path = tmp_path / "test_health.db"
    visualizer = HealthCheckVisualizer(db_path=db_path)
    
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
        visualizer.persistence.save_record(record)
    
    options = VisualizationOptions(
        check_name="test-check",
        time_range_days=7,
        include_trend=True,
        include_summary=True,
        include_details=True,
    )
    
    dashboard = visualizer.generate_dashboard(options)
    
    assert "metadata" in dashboard
    assert "summary" in dashboard
    assert "trend_chart" in dashboard
    assert "records" in dashboard


def test_health_check_visualizer_export_visualization(tmp_path):
    """Test exporting visualization data to JSON."""
    db_path = tmp_path / "test_health.db"
    visualizer = HealthCheckVisualizer(db_path=db_path)
    
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
        visualizer.persistence.save_record(record)
    
    output_path = tmp_path / "visualization.json"
    options = VisualizationOptions(
        check_name="test-check",
        time_range_days=7,
        include_trend=True,
        include_summary=True,
        include_details=True,
    )
    
    visualizer.export_visualization(options, output_path)
    
    assert output_path.exists()
    
    with open(output_path) as f:
        data = json.load(f)
    
    assert "metadata" in data
    assert "summary" in data


def test_health_check_visualizer_generate_markdown_report(tmp_path):
    """Test generating a Markdown report."""
    db_path = tmp_path / "test_health.db"
    visualizer = HealthCheckVisualizer(db_path=db_path)
    
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
        visualizer.persistence.save_record(record)
    
    options = VisualizationOptions(
        check_name="test-check",
        time_range_days=7,
        include_trend=False,
        include_summary=True,
        include_details=True,
    )
    
    markdown = visualizer.generate_markdown_report(options)
    
    assert "# Health Check Report" in markdown
    assert "test-check" in markdown
    assert "Summary" in markdown


def test_health_check_visualizer_export_markdown_report(tmp_path):
    """Test exporting a Markdown report."""
    db_path = tmp_path / "test_health.db"
    visualizer = HealthCheckVisualizer(db_path=db_path)
    
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
        visualizer.persistence.save_record(record)
    
    output_path = tmp_path / "report.md"
    options = VisualizationOptions(
        check_name="test-check",
        time_range_days=7,
        include_trend=False,
        include_summary=True,
        include_details=True,
    )
    
    visualizer.export_markdown_report(options, output_path)
    
    assert output_path.exists()
    
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "# Health Check Report" in content
    assert "test-check" in content


def test_health_check_visualizer_multiple_checks(tmp_path):
    """Test visualizing multiple checks."""
    db_path = tmp_path / "test_health.db"
    visualizer = HealthCheckVisualizer(db_path=db_path)
    
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
        visualizer.persistence.save_record(record)

    for i in range(2):
        from orville_core.health_persistence import HealthCheckRecord
        record = HealthCheckRecord(
            check_name="check-2",
            available=True,
            version=f"2.0.{i}",
            detail=f"Test detail {i}",
            required=True,
        )
        visualizer.persistence.save_record(record)
    
    options = VisualizationOptions(
        check_name=None,  # All checks
        time_range_days=7,
        include_trend=False,
        include_summary=False,
        include_details=False,
    )

    # Debug: check what records are in the database
    all_records = visualizer.persistence.get_history("", limit=1000)

    chart_data = visualizer.generate_chart_data(options)

    print(f"DEBUG: Chart data labels: {chart_data.get('labels', [])}")

    assert "type" in chart_data
    assert "labels" in chart_data
    assert len(chart_data["labels"]) == 2  # Two checks
    assert "latest_status" in chart_data


def test_health_check_visualizer_single_check_chart(tmp_path):
    """Test generating chart data for a single check."""
    db_path = tmp_path / "test_health.db"
    visualizer = HealthCheckVisualizer(db_path=db_path)
    
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
        visualizer.persistence.save_record(record)
    
    options = VisualizationOptions(
        check_name="test-check",
        time_range_days=7,
        include_trend=False,
        include_summary=False,
        include_details=False,
    )
    
    chart_data = visualizer.generate_chart_data(options)
    
    assert chart_data["type"] == "line"
    assert "test-check" in chart_data["title"]
    assert "datasets" in chart_data
    assert len(chart_data["datasets"]) == 2  # Available and unavailable


def test_health_check_visualizer_trend_detection(tmp_path):
    """Test trend detection for health checks."""
    db_path = tmp_path / "test_health.db"
    visualizer = HealthCheckVisualizer(db_path=db_path)
    
    # Add records showing improving trend
    for i in range(3):
        from orville_core.health_persistence import HealthCheckRecord
        record = HealthCheckRecord(
            check_name="test-check",
            available=True,
            version=f"1.0.{i}",
            detail=f"Test detail {i}",
            required=True,
        )
        visualizer.persistence.save_record(record)
    
    options = VisualizationOptions(
        check_name="test-check",
        time_range_days=7,
        include_trend=True,
        include_summary=False,
        include_details=False,
    )
    
    trend = visualizer._generate_trend("test-check", 7)
    
    assert trend.check_name == "test-check"
    assert trend.trend == "stable"  # All available


def test_health_check_visualizer_trend_degrading(tmp_path):
    """Test trend detection for degrading health checks."""
    db_path = tmp_path / "test_health.db"
    visualizer = HealthCheckVisualizer(db_path=db_path)
    
    # Add records showing degrading trend
    for i in range(3):
        from orville_core.health_persistence import HealthCheckRecord
        record = HealthCheckRecord(
            check_name="test-check",
            available=(i < 1),  # First one available, last two not
            version=f"1.0.{i}",
            detail=f"Test detail {i}",
            required=True,
        )
        visualizer.persistence.save_record(record)
    
    trend = visualizer._generate_trend("test-check", 7)
    
    assert trend.trend == "degrading"


def test_health_check_summary_creation():
    """Test creating a health check summary."""
    summary = HealthCheckSummary(
        total_checks=10,
        available_count=8,
        unavailable_count=2,
        availability_percentage=80.0,
    )
    
    assert summary.total_checks == 10
    assert summary.available_count == 8
    assert summary.unavailable_count == 2
    assert summary.availability_percentage == 80.0


def test_health_check_trend_creation():
    """Test creating a health check trend."""
    trend = HealthCheckTrend(
        check_name="test-check",
        available_count=8,
        unavailable_count=2,
        trend="stable",
    )
    
    assert trend.check_name == "test-check"
    assert trend.available_count == 8
    assert trend.unavailable_count == 2
    assert trend.trend == "stable"


def test_health_check_visualizer_time_range_filtering(tmp_path):
    """Test that time range filtering works correctly."""
    db_path = tmp_path / "test_health.db"
    visualizer = HealthCheckVisualizer(db_path=db_path)
    
    # Add records with different timestamps
    for i in range(3):
        from orville_core.health_persistence import HealthCheckRecord
        record = HealthCheckRecord(
            check_name="test-check",
            available=True,
            version=f"1.0.{i}",
            detail=f"Test detail {i}",
            required=True,
        )
        visualizer.persistence.save_record(record)
    
    # Test with 1 day range
    options = VisualizationOptions(
        check_name="test-check",
        time_range_days=1,
        include_trend=False,
        include_summary=False,
        include_details=False,
    )
    
    records = visualizer._get_records_for_visualization(options)
    assert len(records) == 3  # All records should be within 1 day


def test_health_check_visualizer_check_name_filtering(tmp_path):
    """Test that check name filtering works correctly."""
    db_path = tmp_path / "test_health.db"
    visualizer = HealthCheckVisualizer(db_path=db_path)
    
    # Add records for different checks
    for i in range(3):
        from orville_core.health_persistence import HealthCheckRecord
        record = HealthCheckRecord(
            check_name="check-1",
            available=True,
            version=f"1.0.{i}",
            detail=f"Test detail {i}",
            required=True,
        )
        visualizer.persistence.save_record(record)
    
    for i in range(2):
        from orville_core.health_persistence import HealthCheckRecord
        record = HealthCheckRecord(
            check_name="check-2",
            available=True,
            version=f"2.0.{i}",
            detail=f"Test detail {i}",
            required=True,
        )
        visualizer.persistence.save_record(record)
    
    # Filter by check-1
    options = VisualizationOptions(
        check_name="check-1",
        time_range_days=7,
        include_trend=False,
        include_summary=False,
        include_details=False,
    )
    
    records = visualizer._get_records_for_visualization(options)
    assert all(r.check_name == "check-1" for r in records)


def test_health_check_visualizer_limit_parameter(tmp_path):
    """Test that limit parameter works correctly."""
    db_path = tmp_path / "test_health.db"
    visualizer = HealthCheckVisualizer(db_path=db_path)
    
    # Add many records
    for i in range(10):
        from orville_core.health_persistence import HealthCheckRecord
        record = HealthCheckRecord(
            check_name="test-check",
            available=True,
            version=f"1.0.{i}",
            detail=f"Test detail {i}",
            required=True,
        )
        visualizer.persistence.save_record(record)
    
    options = VisualizationOptions(
        check_name="test-check",
        time_range_days=7,
        include_trend=False,
        include_summary=False,
        include_details=False,
    )
    
    records = visualizer._get_records_for_visualization(options)
    assert len(records) == 10  # All records should be returned


def test_health_check_visualizer_empty_results(tmp_path):
    """Test handling of empty results."""
    db_path = tmp_path / "test_health.db"
    visualizer = HealthCheckVisualizer(db_path=db_path)
    
    options = VisualizationOptions(
        check_name="non-existent-check",
        time_range_days=7,
        include_trend=False,
        include_summary=False,
        include_details=False,
    )
    
    chart_data = visualizer.generate_chart_data(options)
    
    assert "type" in chart_data
    assert "labels" in chart_data
    assert len(chart_data["labels"]) == 0
