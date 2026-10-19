"""Health check result export for Orville deployments.

This module provides functionality to export health check results to various formats
including JSON, CSV, and other formats for external systems and reporting.
"""

from __future__ import annotations

import csv
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

from orville_core.health_persistence import HealthCheckPersistence, HealthCheckRecord


class ExportFormat(Enum):
    """Supported export formats."""
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    MARKDOWN = "markdown"


@dataclass
class ExportOptions:
    """Options for health check export."""
    format: ExportFormat
    output_path: str | Path
    include_history: bool = True
    include_summary: bool = True
    include_details: bool = True
    date_range_start: datetime | None = None
    date_range_end: datetime | None = None
    check_names: list[str] | None = None
    limit: int = 1000


class HealthCheckExporter:
    """Export health check results to various formats."""
    
    def __init__(self, db_path: str | Path = ".orville/health.db") -> None:
        """Initialize the health check exporter.
        
        Args:
            db_path: Path to the health check database
        """
        self.db_path = Path(db_path)
        self.persistence = HealthCheckPersistence(db_path)
    
    def export(
        self,
        options: ExportOptions,
    ) -> None:
        """Export health check results.
        
        Args:
            options: Export options
        """
        # Get records to export
        records = self._get_records_to_export(options)
        
        # Export based on format
        if options.format == ExportFormat.JSON:
            self._export_json(records, options)
        elif options.format == ExportFormat.CSV:
            self._export_csv(records, options)
        elif options.format == ExportFormat.HTML:
            self._export_html(records, options)
        elif options.format == ExportFormat.MARKDOWN:
            self._export_markdown(records, options)
    
    def _get_records_to_export(self, options: ExportOptions) -> list[HealthCheckRecord]:
        """Get health check records to export.
        
        Args:
            options: Export options
            
        Returns:
            List of health check records
        """
        # Get all records
        if options.check_names:
            # Filter by check names
            records = []
            for check_name in options.check_names:
                history = self.persistence.get_history(check_name, limit=options.limit)
                records.extend(history)
        else:
            # Get all unique check names first
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT check_name FROM health_checks")
                check_names = [row[0] for row in cursor.fetchall()]
            
            # Get history for all check names
            records = []
            for check_name in check_names:
                history = self.persistence.get_history(check_name, limit=options.limit)
                records.extend(history)
        
        # Filter by date range
        if options.date_range_start or options.date_range_end:
            start = options.date_range_start or datetime.min
            end = options.date_range_end or datetime.max
            
            records = [
                r for r in records
                if start <= datetime.fromisoformat(r.timestamp) <= end
            ]
        
        # Sort by timestamp descending
        records.sort(key=lambda r: r.timestamp, reverse=True)
        
        return records
    
    def _export_json(
        self,
        records: list[HealthCheckRecord],
        options: ExportOptions,
    ) -> None:
        """Export records to JSON format.
        
        Args:
            records: Records to export
            options: Export options
        """
        output_path = Path(options.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build export data
        export_data = {}
        
        if options.include_summary:
            export_data["summary"] = self.persistence.get_summary()
        
        if options.include_history:
            export_data["records"] = [record.to_dict() for record in records]
        
        # Always include export metadata
        export_data["export_metadata"] = {
            "exported_at": datetime.utcnow().isoformat(),
            "export_format": "json",
            "total_records": len(records),
            "check_names": list({r.check_name for r in records}),
        }
        
        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)
    
    def _export_csv(
        self,
        records: list[HealthCheckRecord],
        options: ExportOptions,
    ) -> None:
        """Export records to CSV format.
        
        Args:
            records: Records to export
            options: Export options
        """
        output_path = Path(options.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Define CSV fields
        fieldnames = [
            "timestamp",
            "check_name",
            "available",
            "version",
            "detail",
            "required",
            "integration_name",
            "error",
        ]
        
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for record in records:
                writer.writerow({
                    "timestamp": record.timestamp,
                    "check_name": record.check_name,
                    "available": "yes" if record.available else "no",
                    "version": record.version or "",
                    "detail": record.detail[:1000],  # Truncate to prevent overflow
                    "required": "yes" if record.required else "no",
                    "integration_name": record.integration_name or "",
                    "error": record.error or "",
                })
    
    def _export_html(
        self,
        records: list[HealthCheckRecord],
        options: ExportOptions,
    ) -> None:
        """Export records to HTML format.
        
        Args:
            records: Records to export
            options: Export options
        """
        output_path = Path(options.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build HTML content
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Health Check Export</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }}
        .summary {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #007bff;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .available {{
            color: #28a745;
            font-weight: bold;
        }}
        .unavailable {{
            color: #dc3545;
            font-weight: bold;
        }}
        .metadata {{
            margin-top: 30px;
            padding: 15px;
            background-color: #e9ecef;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Health Check Export</h1>
        <p>Exported on: {datetime.utcnow().isoformat()}</p>
        <p>Total records: {len(records)}</p>
        
        <div class="summary">
            <h2>Summary</h2>
            {self._get_html_summary()}
        </div>
        
        <h2>Health Check History</h2>
        <table>
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Check Name</th>
                    <th>Available</th>
                    <th>Version</th>
                    <th>Detail</th>
                    <th>Integration</th>
                    <th>Error</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for record in records:
            available_class = "available" if record.available else "unavailable"
            available_text = "Yes" if record.available else "No"
            
            html += f"""
                <tr>
                    <td>{record.timestamp}</td>
                    <td>{record.check_name}</td>
                    <td class="{available_class}">{available_text}</td>
                    <td>{record.version or "-"}</td>
                    <td>{record.detail[:100]}</td>
                    <td>{record.integration_name or "-"}</td>
                    <td>{record.error or "-"}</td>
                </tr>
"""
        
        html += f"""
            </tbody>
        </table>
        
        <div class="metadata">
            <h2>Export Metadata</h2>
            <p>Format: HTML</p>
            <p>Total Records: {len(records)}</p>
            <p>Check Names: {', '.join({r.check_name for r in records})}</p>
        </div>
    </div>
</body>
</html>
"""
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
    
    def _get_html_summary(self) -> str:
        """Get HTML summary of health checks.
        
        Returns:
            HTML summary string
        """
        summary = self.persistence.get_summary()
        
        return f"""
        <p><strong>Total Checks:</strong> {summary['total_checks']}</p>
        <p><strong>Available:</strong> {summary['available']}</p>
        <p><strong>Unavailable:</strong> {summary['unavailable']}</p>
        <p><strong>Required Available:</strong> {summary['required_available']}</p>
        <p><strong>Required Unavailable:</strong> {summary['required_unavailable']}</p>
        <p><strong>Overall Status:</strong> {summary['overall_status']}</p>
        """
    
    def _export_markdown(
        self,
        records: list[HealthCheckRecord],
        options: ExportOptions,
    ) -> None:
        """Export records to Markdown format.
        
        Args:
            records: Records to export
            options: Export options
        """
        output_path = Path(options.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build Markdown content
        markdown = f"""# Health Check Export

**Exported on:** {datetime.utcnow().isoformat()}
**Total records:** {len(records)}

## Summary

{self._get_markdown_summary()}

## Health Check History

| Timestamp | Check Name | Available | Version | Detail | Integration | Error |
|-----------|------------|-----------|---------|--------|-------------|-------|
"""
        
        for record in records:
            available_text = "✓ Yes" if record.available else "✗ No"
            
            markdown += f"| {record.timestamp} | {record.check_name} | {available_text} | {record.version or '-'} | {record.detail[:100]} | {record.integration_name or '-'} | {record.error or '-'} |\n"
        
        markdown += f"""
## Export Metadata

- **Format:** Markdown
- **Total Records:** {len(records)}
- **Check Names:** {', '.join({r.check_name for r in records})}
"""
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)
    
    def _get_markdown_summary(self) -> str:
        """Get Markdown summary of health checks.
        
        Returns:
            Markdown summary string
        """
        summary = self.persistence.get_summary()
        
        return f"""
- **Total Checks:** {summary['total_checks']}
- **Available:** {summary['available']}
- **Unavailable:** {summary['unavailable']}
- **Required Available:** {summary['required_available']}
- **Required Unavailable:** {summary['required_unavailable']}
- **Overall Status:** {summary['overall_status']}
"""
    
    def export_latest(
        self,
        output_path: str | Path,
        format: ExportFormat = ExportFormat.JSON,
    ) -> None:
        """Export the latest health check results.
        
        Args:
            output_path: Path to the output file
            format: Export format
        """
        options = ExportOptions(
            format=format,
            output_path=output_path,
            include_history=True,
            include_summary=True,
            include_details=True,
        )
        self.export(options)
    
    def export_by_check(
        self,
        check_name: str,
        output_path: str | Path,
        format: ExportFormat = ExportFormat.JSON,
    ) -> None:
        """Export health check history for a specific check.
        
        Args:
            check_name: Name of the health check
            output_path: Path to the output file
            format: Export format
        """
        options = ExportOptions(
            format=format,
            output_path=output_path,
            check_names=[check_name],
            include_history=True,
            include_summary=True,
            include_details=True,
        )
        self.export(options)
    
    def export_summary(
        self,
        output_path: str | Path,
        format: ExportFormat = ExportFormat.JSON,
    ) -> None:
        """Export health check summary statistics.
        
        Args:
            output_path: Path to the output file
            format: Export format
        """
        options = ExportOptions(
            format=format,
            output_path=output_path,
            include_history=False,
            include_summary=True,
            include_details=True,
        )
        self.export(options)
