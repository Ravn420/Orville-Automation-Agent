"""Integration health checks for Orville deployments.

This module provides health checks for external integrations such as:
- Manus MCP server
- External API gateway
- Database connectivity
- Artifact storage

All checks are secret-safe and non-blocking.
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from orville_core.health_models import HealthCheck


@dataclass
class IntegrationHealthResult:
    """Result of an integration health check."""
    integration_name: str
    available: bool
    version: str | None = None
    detail: str = ""
    last_checked_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "integration_name": self.integration_name,
            "available": self.available,
            "version": self.version,
            "detail": self.detail,
            "last_checked_at": self.last_checked_at,
            "error": self.error,
        }


class IntegrationHealthChecker:
    """Check health of external integrations."""
    
    def __init__(
        self,
        *,
        enable_manus_mcp: bool = True,
        enable_api_gateway: bool = True,
        enable_database: bool = True,
        enable_artifact_storage: bool = True,
        timeout: float = 5.0,
    ) -> None:
        """Initialize the integration health checker.
        
        Args:
            enable_manus_mcp: Whether to check Manus MCP server
            enable_api_gateway: Whether to check external API gateway
            enable_database: Whether to check database connectivity
            enable_artifact_storage: Whether to check artifact storage
            timeout: Timeout for each check in seconds
        """
        self.enable_manus_mcp = enable_manus_mcp
        self.enable_api_gateway = enable_api_gateway
        self.enable_database = enable_database
        self.enable_artifact_storage = enable_artifact_storage
        self.timeout = timeout
    
    def check_manus_mcp_server(self) -> IntegrationHealthResult:
        """Check Manus MCP server health.
        
        Returns:
            IntegrationHealthResult with availability status
        """
        result = IntegrationHealthResult(
            integration_name="manus-mcp-server",
            available=False,
        )
        
        # Check for Manus MCP CLI presence
        manus_mcp_path = os.getenv("MANUS_MCP_CLI_PATH", "manus-mcp-cli")
        if not os.path.exists(manus_mcp_path):
            result.detail = "Manus MCP CLI not found in PATH or MANUS_MCP_CLI_PATH"
            return result
        
        # Try to get version (non-blocking)
        try:
            import subprocess
            result = subprocess.run(
                [manus_mcp_path, "--version"],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
            if result.returncode == 0:
                version = (result.stdout or result.stderr).strip().splitlines()[0][:160]
                result.available = True
                result.version = version
                result.detail = f"Manus MCP server available: {version}"
            else:
                result.detail = f"Manus MCP CLI returned error: {result.stderr.strip()[:200]}"
        except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired) as exc:
            result.detail = f"Manus MCP server check failed: {str(exc)[:200]}"
        
        return result
    
    def check_api_gateway(self) -> IntegrationHealthResult:
        """Check external API gateway health.
        
        Returns:
            IntegrationHealthResult with availability status
        """
        result = IntegrationHealthResult(
            integration_name="api-gateway",
            available=False,
        )
        
        # Check for API gateway URL
        api_gateway_url = os.getenv("ORVILLE_API_BASE_URL", "http://localhost:8000")
        
        # Check if URL is accessible
        try:
            import urllib.error
            import urllib.request
            
            # Use HEAD request for minimal overhead
            req = urllib.request.Request(
                api_gateway_url,
                method="HEAD",
                headers={"User-Agent": "Orville-HealthCheck/1.0"},
            )
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                if response.status < 500:
                    result.available = True
                    result.version = f"HTTP {response.status}"
                    result.detail = f"API gateway accessible: {api_gateway_url}"
                else:
                    result.detail = f"API gateway returned error: HTTP {response.status}"
        except urllib.error.URLError as exc:
            result.detail = f"API gateway unreachable: {str(exc)[:200]}"
        except (TimeoutError, OSError) as exc:
            result.detail = f"API gateway check timeout: {str(exc)[:200]}"
        except Exception as exc:
            result.detail = f"API gateway check failed: {str(exc)[:200]}"
        
        return result
    
    def check_database(self) -> IntegrationHealthResult:
        """Check database connectivity.
        
        Returns:
            IntegrationHealthResult with availability status
        """
        result = IntegrationHealthResult(
            integration_name="database",
            available=False,
        )
        
        # Get database path from environment or default
        db_path = os.getenv(
            "ORVILLE_DB_PATH",
            os.path.join(os.getcwd(), ".orville", "orville.db"),
        )
        
        # Check if database file exists
        if not os.path.exists(db_path):
            result.detail = f"Database file not found: {db_path}"
            return result
        
        # Try to connect and query
        try:
            conn = sqlite3.connect(db_path, timeout=5.0)
            cursor = conn.cursor()
            
            # Simple query to test connectivity
            cursor.execute("SELECT 1")
            cursor.fetchone()
            
            conn.close()
            result.available = True
            result.version = "SQLite"
            result.detail = f"Database accessible: {db_path}"
        except sqlite3.Error as exc:
            result.detail = f"Database connection failed: {str(exc)[:200]}"
        except Exception as exc:
            result.detail = f"Database check failed: {str(exc)[:200]}"
        
        return result
    
    def check_artifact_storage(self) -> IntegrationHealthResult:
        """Check artifact storage health.
        
        Returns:
            IntegrationHealthResult with availability status
        """
        result = IntegrationHealthResult(
            integration_name="artifact-storage",
            available=False,
        )
        
        # Check for artifact storage directory
        artifact_dir = os.getenv(
            "ORVILLE_ARTIFACT_DIR",
            os.path.join(os.getcwd(), "artifacts"),
        )
        
        # Check if directory exists and is writable
        if not os.path.exists(artifact_dir):
            result.detail = f"Artifact directory not found: {artifact_dir}"
            return result
        
        if not os.path.isdir(artifact_dir):
            result.detail = f"Artifact path is not a directory: {artifact_dir}"
            return result
        
        # Try to create a test file
        test_file = os.path.join(artifact_dir, ".health_check_test")
        try:
            with open(test_file, "w") as f:
                f.write("test")
            
            # Clean up
            os.remove(test_file)
            
            result.available = True
            result.version = "local"
            result.detail = f"Artifact storage accessible: {artifact_dir}"
        except OSError as exc:
            result.detail = f"Artifact storage check failed: {str(exc)[:200]}"
        except Exception as exc:
            result.detail = f"Artifact storage check failed: {str(exc)[:200]}"
        
        return result
    
    def run_all(self) -> list[IntegrationHealthResult]:
        """Run all enabled integration health checks.
        
        Returns:
            List of IntegrationHealthResult objects
        """
        results: list[IntegrationHealthResult] = []
        
        if self.enable_manus_mcp:
            results.append(self.check_manus_mcp_server())
        
        if self.enable_api_gateway:
            results.append(self.check_api_gateway())
        
        if self.enable_database:
            results.append(self.check_database())
        
        if self.enable_artifact_storage:
            results.append(self.check_artifact_storage())
        
        return results


def create_health_check_from_integration_result(
    integration_result: IntegrationHealthResult,
) -> HealthCheck:
    """Create a HealthCheck from an IntegrationHealthResult.
    
    Args:
        integration_result: The integration health result
        
    Returns:
        A HealthCheck object
    """
    return HealthCheck(
        name=integration_result.integration_name,
        available=integration_result.available,
        version=integration_result.version,
        detail=integration_result.detail,
        required=False,  # Integration checks are optional
    )
