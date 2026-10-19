"""Health check result persistence for Orville deployments.

This module provides persistent storage for health check results,
including history tracking and query capabilities.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class HealthCheckRecord:
    """A single health check record."""
    check_name: str
    available: bool
    version: str | None = None
    detail: str = ""
    required: bool = True
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    integration_name: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "check_name": self.check_name,
            "available": self.available,
            "version": self.version,
            "detail": self.detail,
            "required": self.required,
            "timestamp": self.timestamp,
            "integration_name": self.integration_name,
            "error": self.error,
        }


@dataclass
class HealthCheckHistory:
    """Health check history with query capabilities."""
    records: list[HealthCheckRecord] = field(default_factory=list)
    
    def add_record(self, record: HealthCheckRecord) -> None:
        """Add a health check record.
        
        Args:
            record: The health check record to add
        """
        self.records.append(record)
    
    def get_latest(self, check_name: str) -> HealthCheckRecord | None:
        """Get the latest record for a specific check.
        
        Args:
            check_name: The name of the check
            
        Returns:
            The latest record or None if not found
        """
        records = [r for r in self.records if r.check_name == check_name]
        if not records:
            return None
        return max(records, key=lambda r: r.timestamp)
    
    def get_history(
        self,
        check_name: str,
        limit: int = 100,
    ) -> list[HealthCheckRecord]:
        """Get history for a specific check.
        
        Args:
            check_name: The name of the check
            limit: Maximum number of records to return
            
        Returns:
            List of health check records
        """
        import sys
        print(f"DEBUG: get_history called with check_name={check_name}, limit={limit}, db_path={self.db_path}", file=sys.stderr)
        
        # Get records from database
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if check_name:
                    cursor.execute("""
                        SELECT check_name, available, version, detail, required,
                               timestamp, integration_name, error
                        FROM health_checks
                        WHERE check_name = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (check_name, limit))
                else:
                    cursor.execute("""
                        SELECT check_name, available, version, detail, required,
                               timestamp, integration_name, error
                        FROM health_checks
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (limit,))
                
                db_records = []
                for row in cursor.fetchall():
                    db_records.append(HealthCheckRecord(
                        check_name=row[0],
                        available=bool(row[1]),
                        version=row[2],
                        detail=row[3],
                        required=bool(row[4]),
                        timestamp=row[5],
                        integration_name=row[6],
                        error=row[7],
                    ))
        except Exception as e:
            import sys
            print(f"DEBUG: Error querying database: {e}", file=sys.stderr)
            db_records = []
        
        # Merge with in-memory records (in-memory takes precedence)
        all_records = self.records + db_records
        
        # Filter by check name
        if check_name:
            records = [r for r in all_records if r.check_name == check_name]
        else:
            records = all_records
        
        # Sort by timestamp (newest first)
        records.sort(key=lambda r: r.timestamp, reverse=True)
        
        # Apply limit
        result = records[-limit:] if limit else records
        
        # Debug output
        import sys
        if len(db_records) > 0:
            print(f"DEBUG: get_history({check_name}, {limit}) returned {len(result)} records from database", file=sys.stderr)
        
        return result
    
    def get_summary(self) -> dict[str, Any]:
        """Get a summary of all health checks.
        
        Returns:
            Dictionary with summary statistics
        """
        total = len(self.records)
        available = sum(1 for r in self.records if r.available)
        unavailable = total - available
        required_available = sum(1 for r in self.records if r.required and r.available)
        required_unavailable = sum(1 for r in self.records if r.required and not r.available)
        
        return {
            "total_checks": total,
            "available": available,
            "unavailable": unavailable,
            "required_available": required_available,
            "required_unavailable": required_unavailable,
            "overall_status": "ok" if required_available == required_unavailable else "degraded",
        }


class HealthCheckPersistence:
    """Persistent storage for health check results."""
    
    def __init__(self, db_path: str | Path = ".orville/health.db") -> None:
        """Initialize the health check persistence.
        
        Args:
            db_path: Path to the SQLite database
        """
        self.db_path = Path(db_path)
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize the database schema."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create health_checks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS health_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    check_name TEXT NOT NULL,
                    available INTEGER NOT NULL,
                    version TEXT,
                    detail TEXT,
                    required INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    integration_name TEXT,
                    error TEXT
                )
            """)
            
            # Create index on check_name for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_check_name
                ON health_checks(check_name)
            """)
            
            # Create index on timestamp for time-based queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON health_checks(timestamp DESC)
            """)
            
            conn.commit()
    
    def save_record(self, record: HealthCheckRecord) -> None:
        """Save a health check record.
        
        Args:
            record: The health check record to save
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO health_checks (
                    check_name, available, version, detail, required,
                    timestamp, integration_name, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.check_name,
                1 if record.available else 0,
                record.version,
                record.detail[:1000],  # Truncate to prevent overflow
                1 if record.required else 0,
                record.timestamp,
                record.integration_name,
                record.error,
            ))
            
            conn.commit()
    
    def get_latest_record(self, check_name: str) -> HealthCheckRecord | None:
        """Get the latest record for a specific check.
        
        Args:
            check_name: The name of the check
            
        Returns:
            The latest record or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT check_name, available, version, detail, required,
                       timestamp, integration_name, error
                FROM health_checks
                WHERE check_name = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (check_name,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return HealthCheckRecord(
                check_name=row[0],
                available=bool(row[1]),
                version=row[2],
                detail=row[3],
                required=bool(row[4]),
                timestamp=row[5],
                integration_name=row[6],
                error=row[7],
            )
    
    def get_history(
        self,
        check_name: str,
        limit: int = 100,
    ) -> list[HealthCheckRecord]:
        """Get history for a specific check.
        
        Args:
            check_name: The name of the check
            limit: Maximum number of records to return
            
        Returns:
            List of health check records
        """
        # Get records from database
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if check_name:
                    cursor.execute("""
                        SELECT check_name, available, version, detail, required,
                               timestamp, integration_name, error
                        FROM health_checks
                        WHERE check_name = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (check_name, limit))
                else:
                    cursor.execute("""
                        SELECT check_name, available, version, detail, required,
                               timestamp, integration_name, error
                        FROM health_checks
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (limit,))
                
                rows = cursor.fetchall()
                db_records = [
                    HealthCheckRecord(
                        check_name=row[0],
                        available=bool(row[1]),
                        version=row[2],
                        detail=row[3],
                        required=bool(row[4]),
                        timestamp=row[5],
                        integration_name=row[6],
                        error=row[7],
                    )
                    for row in rows
                ]
        except Exception:
            db_records = []
        
        # Filter by check name
        if check_name:
            records = [r for r in db_records if r.check_name == check_name]
        else:
            records = db_records
        
        # Sort by timestamp (newest first)
        records.sort(key=lambda r: r.timestamp, reverse=True)
        
        # Apply limit
        return records[-limit:] if limit else records
    
    def get_summary(self) -> dict[str, Any]:
        """Get a summary of all health checks.
        
        Returns:
            Dictionary with summary statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get total count
            cursor.execute("SELECT COUNT(*) FROM health_checks")
            total = cursor.fetchone()[0]
            
            # Get available count
            cursor.execute("SELECT COUNT(*) FROM health_checks WHERE available = 1")
            available = cursor.fetchone()[0]
            
            # Get required available count
            cursor.execute("SELECT COUNT(*) FROM health_checks WHERE required = 1 AND available = 1")
            required_available = cursor.fetchone()[0]
            
            # Get required unavailable count
            cursor.execute("SELECT COUNT(*) FROM health_checks WHERE required = 1 AND available = 0")
            required_unavailable = cursor.fetchone()[0]
            
            return {
                "total_checks": total,
                "available": available,
                "unavailable": total - available,
                "required_available": required_available,
                "required_unavailable": required_unavailable,
                "overall_status": "ok" if required_unavailable == 0 else "degraded",
            }
    
    def export_to_json(self, output_path: str | Path) -> None:
        """Export all health check records to JSON.
        
        Args:
            output_path: Path to the output JSON file
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT check_name, available, version, detail, required,
                       timestamp, integration_name, error
                FROM health_checks
                ORDER BY timestamp DESC
            """)
            
            rows = cursor.fetchall()
            records = [
                {
                    "check_name": row[0],
                    "available": bool(row[1]),
                    "version": row[2],
                    "detail": row[3],
                    "required": bool(row[4]),
                    "timestamp": row[5],
                    "integration_name": row[6],
                    "error": row[7],
                }
                for row in rows
            ]
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(records, f, indent=2)
    
    def clear_history(self) -> None:
        """Clear all health check history."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM health_checks")
            conn.commit()
