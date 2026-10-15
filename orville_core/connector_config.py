"""Connector configuration management with validation and versioning.

This module provides:
- Connector configuration file format (JSON/YAML)
- Configuration loader and validator
- Dependency management
- Versioning support
"""

from __future__ import annotations

import json
import re
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar

import yaml

from .connector_connections import ConnectorConnection
from .connector_defaults import ConnectorDefaultsStore


class ConnectorStatus(str, Enum):
    """Connector status states."""
    CONFIGURATION_REQUIRED = "configuration_required"
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class ConnectorAuthType(str, Enum):
    """Supported authentication types."""
    API_KEY = "api_key"
    BEARER = "bearer"
    OAUTH2 = "oauth2"


class ConnectorRiskClass(str, Enum):
    """Risk classification for connector operations."""
    READ = "read"
    WRITE = "write"
    SENSITIVE = "sensitive"
    CRITICAL = "critical"


@dataclass
class ConnectorOperation:
    """Represents a connector operation with schema and risk."""
    name: str
    method: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    returns: dict[str, Any] = field(default_factory=dict)
    risk_class: ConnectorRiskClass = ConnectorRiskClass.READ
    sensitive: bool = False
    deprecated: bool = False
    version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "method": self.method,
            "description": self.description,
            "parameters": self.parameters,
            "returns": self.returns,
            "risk_class": self.risk_class.value,
            "sensitive": self.sensitive,
            "deprecated": self.deprecated,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConnectorOperation:
        """Create from dictionary representation."""
        return cls(
            name=data["name"],
            method=data["method"],
            description=data["description"],
            parameters=data.get("parameters", {}),
            returns=data.get("returns", {}),
            risk_class=ConnectorRiskClass(data.get("risk_class", "read")),
            sensitive=data.get("sensitive", False),
            deprecated=data.get("deprecated", False),
            version=data.get("version", "1.0.0"),
        )


@dataclass
class ConnectorManifest:
    """Connector manifest with identity, capabilities, and metadata."""
    uid: str
    display_name: str
    version: str
    description: str
    status: ConnectorStatus = ConnectorStatus.CONFIGURATION_REQUIRED
    auth_type: ConnectorAuthType | None = None
    base_url: str | None = None
    scopes: list[str] = field(default_factory=list)
    operations: list[ConnectorOperation] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    risk_class: ConnectorRiskClass = ConnectorRiskClass.READ
    owner_id: str = "local"
    task_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    # Validation
    _uid_regex: ClassVar[re.Pattern] = re.compile(r'^[a-z0-9]([a-z0-9-_.]*[a-z0-9])?$')
    _display_name_regex: ClassVar[re.Pattern] = re.compile(r'^[a-zA-Z0-9\s\-_\.]+$')
    _version_regex: ClassVar[re.Pattern] = re.compile(r'^\d+\.\d+\.\d+$')

    def validate(self) -> list[str]:
        """Validate the manifest. Returns list of error messages."""
        errors = []

        if not self._uid_regex.match(self.uid):
            errors.append(f"Invalid connector UID: {self.uid}. Must match pattern: {self._uid_regex.pattern}")

        if not self._display_name_regex.match(self.display_name):
            errors.append(f"Invalid display name: {self.display_name}. Must contain only letters, numbers, spaces, hyphens, underscores, and dots")

        if not self._version_regex.match(self.version):
            errors.append(f"Invalid version: {self.version}. Must match semver pattern X.Y.Z")

        if not self.description.strip():
            errors.append("Description is required")

        if self.status == ConnectorStatus.OPERATIONAL:
            if not self.base_url:
                errors.append("Operational connectors must have a base_url")
            if not self.auth_type:
                errors.append("Operational connectors must have an auth_type")

        # Check for duplicate operation names
        operation_names = [op.name for op in self.operations]
        duplicates = [name for name in operation_names if operation_names.count(name) > 1]
        if duplicates:
            errors.append(f"Duplicate operation names: {', '.join(set(duplicates))}")

        # Check for circular dependencies
        if self.dependencies:
            cycle = self._find_circular_dependency(self.uid, set())
            if cycle:
                errors.append(f"Circular dependency detected: {' -> '.join(cycle)}")

        return errors

    def _find_circular_dependency(self, current: str, visited: set[str]) -> list[str] | None:
        """Find circular dependencies in the dependency graph."""
        if current in visited:
            return [current]
        visited.add(current)

        for dep in self.dependencies:
            if dep == current:
                return [dep]
            # This is a simplified check - in a real implementation,
            # you'd need to check the full dependency graph
            if dep in self.operations:
                continue

        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "uid": self.uid,
            "display_name": self.display_name,
            "version": self.version,
            "description": self.description,
            "status": self.status.value,
            "auth_type": self.auth_type.value if self.auth_type else None,
            "base_url": self.base_url,
            "scopes": self.scopes,
            "operations": [op.to_dict() for op in self.operations],
            "dependencies": self.dependencies,
            "risk_class": self.risk_class.value,
            "owner_id": self.owner_id,
            "task_id": self.task_id,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConnectorManifest:
        """Create from dictionary representation."""
        return cls(
            uid=data["uid"],
            display_name=data["display_name"],
            version=data["version"],
            description=data["description"],
            status=ConnectorStatus(data.get("status", "configuration_required")),
            auth_type=ConnectorAuthType(data.get("auth_type")) if data.get("auth_type") else None,
            base_url=data.get("base_url"),
            scopes=data.get("scopes", []),
            operations=[ConnectorOperation.from_dict(op) for op in data.get("operations", [])],
            dependencies=data.get("dependencies", []),
            risk_class=ConnectorRiskClass(data.get("risk_class", "read")),
            owner_id=data.get("owner_id", "local"),
            task_id=data.get("task_id"),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
        )


@dataclass
class ConnectorConfig:
    """Complete connector configuration with manifests and connections."""
    version: str = "1.0.0"
    manifests: dict[str, ConnectorManifest] = field(default_factory=dict)
    connections: dict[str, ConnectorConnection] = field(default_factory=dict)
    defaults: ConnectorDefaultsStore | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def __post_init__(self):
        """Initialize defaults after dataclass init."""
        if self.defaults is None:
            self.defaults = ConnectorDefaultsStore(":memory:")

    def validate(self) -> list[str]:
        """Validate the complete configuration."""
        errors = []

        # Validate all manifests
        for uid, manifest in self.manifests.items():
            errors.extend(manifest.validate())

        # Check for manifest-connection consistency
        for uid in self.connections:
            if uid not in self.manifests:
                errors.append(f"Connection for UID '{uid}' has no corresponding manifest")

        # Check for dependency resolution
        for manifest in self.manifests.values():
            for dep in manifest.dependencies:
                if dep not in self.manifests:
                    errors.append(f"Manifest '{manifest.uid}' depends on '{dep}' which is not defined")

        return errors

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "version": self.version,
            "manifests": {uid: manifest.to_dict() for uid, manifest in self.manifests.items()},
            "connections": {uid: connection.public() for uid, connection in self.connections.items()},
            "defaults": self.defaults.list(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ConnectorConfig:
        """Create from dictionary representation."""
        config = cls(
            version=data.get("version", "1.0.0"),
            manifests={uid: ConnectorManifest.from_dict(m) for uid, m in data.get("manifests", {}).items()},
            connections={uid: ConnectorConnection(**{k: v for k, v in c.items() if k != "_secret"}) for uid, c in data.get("connections", {}).items()},
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
        )
        return config


class ConnectorConfigError(RuntimeError):
    """Raised for invalid connector configuration operations."""


class ConnectorConfigLoader:
    """Load and validate connector configurations from files."""

    SUPPORTED_FORMATS: ClassVar[set[str]] = {"json", "yaml", "yml"}

    def __init__(self, config_path: str | Path):
        self.config_path = Path(config_path)
        self._lock = threading.RLock()

    def load(self) -> ConnectorConfig:
        """Load configuration from file."""
        if not self.config_path.exists():
            return ConnectorConfig()

        try:
            with self.config_path.open("r", encoding="utf-8") as f:
                content = f.read()
        except OSError as exc:
            raise ConnectorConfigError(f"Failed to read config file: {exc}") from exc

        try:
            if self.config_path.suffix.lower() in {".yaml", ".yml"}:
                data = yaml.safe_load(content) or {}
            else:
                data = json.loads(content)
        except (yaml.YAMLError, json.JSONDecodeError) as exc:
            raise ConnectorConfigError(f"Failed to parse config file: {exc}") from exc

        config = ConnectorConfig.from_dict(data)
        errors = config.validate()
        if errors:
            raise ConnectorConfigError("Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

        return config

    def save(self, config: ConnectorConfig) -> None:
        """Save configuration to file."""
        with self._lock:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            data = config.to_dict()
            if self.config_path.suffix.lower() in {".yaml", ".yml"}:
                with self.config_path.open("w", encoding="utf-8") as f:
                    yaml.dump(data, f, default_flow_style=False, sort_keys=False)
            else:
                with self.config_path.open("w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            config.updated_at = time.time()

    def load_or_create(self) -> ConnectorConfig:
        """Load existing config or create a new one."""
        if self.config_path.exists():
            return self.load()
        return ConnectorConfig()

    def validate_file(self) -> list[str]:
        """Validate the config file without loading it."""
        if not self.config_path.exists():
            return ["Config file does not exist"]

        try:
            with self.config_path.open("r", encoding="utf-8") as f:
                content = f.read()
        except OSError as exc:
            return [f"Failed to read config file: {exc}"]

        try:
            if self.config_path.suffix.lower() in {".yaml", ".yml"}:
                data = yaml.safe_load(content) or {}
            else:
                data = json.loads(content)
        except (yaml.YAMLError, json.JSONDecodeError) as exc:
            return [f"Failed to parse config file: {exc}"]

        config = ConnectorConfig.from_dict(data)
        return config.validate()


class ConnectorConfigManager:
    """Manage connector configurations with dependency resolution and versioning."""

    def __init__(self, config_path: str | Path):
        self.loader = ConnectorConfigLoader(config_path)
        self.config = self.loader.load_or_create()

    def get_manifest(self, uid: str) -> ConnectorManifest | None:
        """Get a manifest by UID."""
        return self.config.manifests.get(uid)

    def list_manifests(self) -> list[ConnectorManifest]:
        """List all manifests."""
        return sorted(self.config.manifests.values(), key=lambda m: m.display_name.lower())

    def add_manifest(self, manifest: ConnectorManifest) -> list[str]:
        """Add or update a manifest."""
        errors = manifest.validate()
        if errors:
            return errors

        with self.loader._lock:
            self.config.manifests[manifest.uid] = manifest
            self.config.updated_at = time.time()
            self.loader.save(self.config)
            return []

    def remove_manifest(self, uid: str) -> bool:
        """Remove a manifest."""
        if uid not in self.config.manifests:
            return False

        with self.loader._lock:
            del self.config.manifests[uid]
            self.config.updated_at = time.time()
            self.loader.save(self.config)
            return True

    def get_dependencies(self, uid: str) -> list[ConnectorManifest]:
        """Get all dependencies for a manifest."""
        manifest = self.config.manifests.get(uid)
        if not manifest:
            return []

        dependencies = []
        for dep_uid in manifest.dependencies:
            dep_manifest = self.config.manifests.get(dep_uid)
            if dep_manifest:
                dependencies.append(dep_manifest)
                dependencies.extend(self.get_dependencies(dep_uid))

        return list({m.uid: m for m in dependencies}.values())

    def resolve_dependencies(self, uids: list[str]) -> list[ConnectorManifest]:
        """Resolve all dependencies for a list of UIDs."""
        all_manifests = []
        for uid in uids:
            manifest = self.config.manifests.get(uid)
            if manifest:
                all_manifests.append(manifest)
                all_manifests.extend(self.get_dependencies(uid))

        return list({m.uid: m for m in all_manifests}.values())

    def get_version_info(self, uid: str) -> dict[str, Any]:
        """Get version information for a connector."""
        manifest = self.config.manifests.get(uid)
        if not manifest:
            return {"uid": uid, "error": "Manifest not found"}

        connection = self.config.connections.get(uid)

        return {
            "uid": manifest.uid,
            "display_name": manifest.display_name,
            "version": manifest.version,
            "status": manifest.status.value,
            "auth_type": manifest.auth_type.value if manifest.auth_type else None,
            "base_url": manifest.base_url,
            "has_connection": connection is not None,
            "connection_status": connection.status if connection else None,
            "operation_count": len(manifest.operations),
            "dependency_count": len(manifest.dependencies),
            "created_at": manifest.created_at,
            "updated_at": manifest.updated_at,
        }

    def get_all_version_info(self) -> list[dict[str, Any]]:
        """Get version information for all connectors."""
        return [self.get_version_info(uid) for uid in self.config.manifests]

    def update_status(self, uid: str, status: ConnectorStatus) -> bool:
        """Update the status of a manifest."""
        if uid not in self.config.manifests:
            return False

        with self.loader._lock:
            self.config.manifests[uid].status = status
            self.config.manifests[uid].updated_at = time.time()
            self.loader.save(self.config)
            return True

    def validate_all(self) -> list[str]:
        """Validate all manifests and return errors."""
        errors = []
        for manifest in self.config.manifests.values():
            errors.extend(manifest.validate())
        return errors
