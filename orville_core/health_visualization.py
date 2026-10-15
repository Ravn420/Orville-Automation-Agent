"""Health check result visualization for Orville deployments.

This module provides visualization capabilities for health check results,
including charts, graphs, and summary statistics.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from orville_core.health_persistence import HealthCheckPersistence, HealthCheckRecord


@dataclass
class VisualizationOptions:
    """Options for health check visualization."""
    check_name: str | None = None
    time_range_days: int = 7
    include_trend: bool = True
    include_summary: bool = True
    include_details: bool = True
    chart_type: str = "line"  # line, bar, pie
    output_path: str | Path | None = None


@dataclass
class HealthCheckTrend:
    """Trend data for a health check."""
    check_name: str
    available_count: int
    unavailable_count: int
    trend: str  # "stable", "improving", "degrading", "unstable"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "check_name": self.check_name,
            "available_count": self.available_count,
            "unavailable_count": self.unavailable_count,
            "trend": self.trend,
        }


@dataclass
class HealthCheckSummary:
    """Summary data for health checks."""
    total_checks: int
    available_count: int
    unavailable_count: int
    availability_percentage: float
    recent_trend: HealthCheckTrend | None = None


class HealthCheckVisualizer:
    """Visualizer for health check results."""
    
    def __init__(self, db_path: str | Path = ".orville/health.db") -> None:
        """Initialize the health check visualizer.
        
        Args:
            db_path: Path to the health check database
        """
        self.db_path = Path(db_path)
        self.persistence = HealthCheckPersistence(db_path)
    
    def visualize(
        self,
        options: VisualizationOptions,
    ) -> dict[str, Any]:
        """Generate visualization data.
        
        Args:
            options: Visualization options
            
        Returns:
            Dictionary with visualization data
        """
        # Get records
        records = self._get_records_for_visualization(options)
        
        # Build visualization data
        visualization = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "check_name": options.check_name,
                "time_range_days": options.time_range_days,
                "chart_type": options.chart_type,
            },
        }
        
        if options.include_summary:
            visualization["summary"] = self._generate_summary(records, options)
        
        if options.include_trend and options.check_name:
            trend = self._generate_trend(options.check_name, options.time_range_days)
            visualization["trend"] = trend.to_dict()
        
        if options.include_details:
            visualization["records"] = [record.to_dict() for record in records]
        
        return visualization
    
    def _get_records_for_visualization(
        self,
        options: VisualizationOptions,
    ) -> list[HealthCheckRecord]:
        """Get health check records for visualization.
        
        Args:
            options: Visualization options
            
        Returns:
            List of health check records
        """
        # Calculate time range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=options.time_range_days)
        
        # Get records
        if options.check_name:
            records = self.persistence.get_history(options.check_name, limit=1000)
        else:
            # Get all unique check names
            all_records = self.persistence.get_history("", limit=1000)
            check_names = {r.check_name for r in all_records}
            records = []
            
            for check_name in check_names:
                check_records = self.persistence.get_history(check_name, limit=1000)
                records.extend(check_records)
        
        # Filter by time range
        records = [
            r for r in records
            if start_date <= datetime.fromisoformat(r.timestamp) <= end_date
        ]
        
        # Sort by timestamp
        records.sort(key=lambda r: r.timestamp)
        
        return records
    
    def _generate_summary(
        self,
        records: list[HealthCheckRecord],
        options: VisualizationOptions,
    ) -> dict[str, Any]:
        """Generate summary statistics.
        
        Args:
            records: Health check records
            options: Visualization options
            
        Returns:
            Health check summary as dictionary
        """
        total = len(records)
        available = sum(1 for r in records if r.available)
        unavailable = total - available
        availability_percentage = (available / total * 100) if total > 0 else 0.0
        
        return {
            "total_checks": total,
            "available_count": available,
            "unavailable_count": unavailable,
            "availability_percentage": round(availability_percentage, 2),
        }
    
    def _generate_trend(
        self,
        check_name: str,
        days: int,
    ) -> HealthCheckTrend:
        """Generate trend data for a health check.
        
        Args:
            check_name: Name of the health check
            days: Number of days to analyze
            
        Returns:
            Health check trend
        """
        # Get records for the check
        records = self.persistence.get_history(check_name, limit=1000)
        
        # Filter by time range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        records = [
            r for r in records
            if start_date <= datetime.fromisoformat(r.timestamp) <= end_date
        ]
        
        # Count available and unavailable
        available_count = sum(1 for r in records if r.available)
        unavailable_count = sum(1 for r in records if not r.available)
        
        # Determine trend
        if unavailable_count == 0:
            trend = "stable"
        elif available_count > unavailable_count:
            trend = "improving"
        elif available_count < unavailable_count:
            trend = "degrading"
        else:
            trend = "unstable"
        
        return HealthCheckTrend(
            check_name=check_name,
            available_count=available_count,
            unavailable_count=unavailable_count,
            trend=trend,
        )
    
    def generate_chart_data(
        self,
        options: VisualizationOptions,
    ) -> dict[str, Any]:
        """Generate chart data for visualization.
        
        Args:
            options: Visualization options
            
        Returns:
            Dictionary with chart data
        """
        records = self._get_records_for_visualization(options)
        
        # Group by check name
        if options.check_name:
            # Single check visualization
            chart_data = self._generate_single_check_chart(records, options)
        else:
            # Multiple checks visualization
            chart_data = self._generate_multiple_checks_chart(records, options)
        
        return chart_data
    
    def _generate_single_check_chart(
        self,
        records: list[HealthCheckRecord],
        options: VisualizationOptions,
    ) -> dict[str, Any]:
        """Generate chart data for a single check.
        
        Args:
            records: Health check records
            options: Visualization options
            
        Returns:
            Dictionary with chart data
        """
        # Group by time period
        time_periods = {}
        for record in records:
            timestamp = datetime.fromisoformat(record.timestamp)
            period = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            
            if period not in time_periods:
                time_periods[period] = {"available": 0, "unavailable": 0}
            
            if record.available:
                time_periods[period]["available"] += 1
            else:
                time_periods[period]["unavailable"] += 1
        
        # Sort by time
        sorted_periods = sorted(time_periods.items(), key=lambda x: x[0])
        
        labels = [p[0].isoformat() for p in sorted_periods]
        available_data = [p[1]["available"] for p in sorted_periods]
        unavailable_data = [p[1]["unavailable"] for p in sorted_periods]
        
        return {
            "type": "line",
            "title": f"Health Check: {options.check_name}",
            "labels": labels,
            "datasets": [
                {
                    "name": "Available",
                    "data": available_data,
                    "color": "#28a745",
                },
                {
                    "name": "Unavailable",
                    "data": unavailable_data,
                    "color": "#dc3545",
                },
            ],
        }
    
    def _generate_multiple_checks_chart(
        self,
        records: list[HealthCheckRecord],
        options: VisualizationOptions,
    ) -> dict[str, Any]:
        """Generate chart data for multiple checks.
        
        Args:
            records: Health check records
            options: Visualization options
            
        Returns:
            Dictionary with chart data
        """
        # Group by check name
        check_data = {}
        for record in records:
            if record.check_name not in check_data:
                check_data[record.check_name] = {"available": 0, "unavailable": 0}
            
            if record.available:
                check_data[record.check_name]["available"] += 1
            else:
                check_data[record.check_name]["unavailable"] += 1
        
        # Get latest status for each check
        latest_status = {}
        for check_name in check_data:
            history = self.persistence.get_history(check_name, limit=1)
            if history:
                latest_status[check_name] = history[0].available
        
        labels = list(check_data.keys())
        available_data = [check_data[name]["available"] for name in labels]
        unavailable_data = [check_data[name]["unavailable"] for name in labels]
        latest_status_data = [latest_status[name] for name in labels]
        
        if not labels:
            # Return empty chart if no data
            return {
                "type": "bar",
                "title": "Health Check Summary",
                "labels": [],
                "datasets": [
                    {
                        "name": "Available",
                        "data": [],
                        "color": "#28a745",
                    },
                    {
                        "name": "Unavailable",
                        "data": [],
                        "color": "#dc3545",
                    },
                ],
                "latest_status": [],
            }
        
        return {
            "type": "bar",
            "title": "Health Check Summary",
            "labels": labels,
            "datasets": [
                {
                    "name": "Available",
                    "data": available_data,
                    "color": "#28a745",
                },
                {
                    "name": "Unavailable",
                    "data": unavailable_data,
                    "color": "#dc3545",
                },
            ],
            "latest_status": latest_status_data,
        }
    
    def generate_dashboard(
        self,
        options: VisualizationOptions,
    ) -> dict[str, Any]:
        """Generate a complete dashboard with multiple visualizations.
        
        Args:
            options: Visualization options
            
        Returns:
            Dictionary with dashboard data
        """
        records = self._get_records_for_visualization(options)
        
        dashboard = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "time_range_days": options.time_range_days,
            },
            "summary": self._generate_summary(records, options),
            "records": [record.to_dict() for record in records],
        }
        
        # Generate charts
        if options.check_name:
            dashboard["trend_chart"] = self.generate_chart_data(options)
        else:
            dashboard["check_charts"] = []
            for check_name in {r.check_name for r in records}:
                check_options = VisualizationOptions(
                    check_name=check_name,
                    time_range_days=options.time_range_days,
                    include_trend=False,
                    include_summary=False,
                    include_details=False,
                )
                chart_data = self.generate_chart_data(check_options)
                dashboard["check_charts"].append({
                    "check_name": check_name,
                    "chart": chart_data,
                })
        
        return dashboard
    
    def export_visualization(
        self,
        options: VisualizationOptions,
        output_path: str | Path,
    ) -> None:
        """Export visualization data to JSON.
        
        Args:
            options: Visualization options
            output_path: Path to the output file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        visualization = self.visualize(options)
        
        with open(output_path, "w") as f:
            json.dump(visualization, f, indent=2)
    
    def generate_markdown_report(
        self,
        options: VisualizationOptions,
    ) -> str:
        """Generate a Markdown report for health checks.
        
        Args:
            options: Visualization options
            
        Returns:
            Markdown report string
        """
        records = self._get_records_for_visualization(options)
        summary = self._generate_summary(records, options)
        
        markdown = f"""# Health Check Report

**Generated:** {datetime.utcnow().isoformat()}
**Time Range:** Last {options.time_range_days} days
**Check Name:** {options.check_name or "All Checks"}

## Summary

- **Total Checks:** {summary["total_checks"]}
- **Available:** {summary["available_count"]} ({summary["availability_percentage"]}%)
- **Unavailable:** {summary["unavailable_count"]} ({100 - summary["availability_percentage"]}%)

## Health Check History

| Timestamp | Check Name | Available | Version | Detail |
|-----------|------------|-----------|---------|--------|
"""
        
        for record in records[:50]:  # Limit to 50 records
            available_text = "✓ Yes" if record.available else "✗ No"
            markdown += f"| {record.timestamp} | {record.check_name} | {available_text} | {record.version or '-'} | {record.detail[:100]} |\n"
        
        if len(records) > 50:
            markdown += f"\n*... and {len(records) - 50} more records*\n"
        
        return markdown
    
    def export_markdown_report(
        self,
        options: VisualizationOptions,
        output_path: str | Path,
    ) -> None:
        """Export a Markdown report for health checks.
        
        Args:
            options: Visualization options
            output_path: Path to the output file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        markdown = self.generate_markdown_report(options)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)
