"""Tests for connector configuration management."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from orville_core.connector_config import (
    ConnectorConfig,
    ConnectorConfigError,
    ConnectorConfigLoader,
    ConnectorConfigManager,
    ConnectorManifest,
    ConnectorOperation,
    ConnectorRiskClass,
    ConnectorStatus,
    ConnectorAuthType,
)
from orville_core.connector_connections import ConnectorConnection, ConnectorConnectionStore


class TestConnectorOperation:
    """Test ConnectorOperation class."""

    def test_create_operation(self):
        """Test creating a basic operation."""
        op = ConnectorOperation(
            name="test_operation",
            method="GET",
            description="Test operation",
            parameters={"param1": {"type": "string"}},
            returns={"type": "object"},
        )
        assert op.name == "test_operation"
        assert op.method == "GET"
        assert op.risk_class == ConnectorRiskClass.READ

    def test_operation_to_dict(self):
        """Test converting operation to dictionary."""
        op = ConnectorOperation(
            name="test",
            method="POST",
            description="Test",
            risk_class=ConnectorRiskClass.SENSITIVE,
        )
        data = op.to_dict()
        assert data["name"] == "test"
        assert data["method"] == "POST"
        assert data["risk_class"] == "sensitive"

    def test_operation_from_dict(self):
        """Test creating operation from dictionary."""
        data = {
            "name": "test",
            "method": "GET",
            "description": "Test",
            "risk_class": "write",
            "sensitive": True,
        }
        op = ConnectorOperation.from_dict(data)
        assert op.name == "test"
        assert op.method == "GET"
        assert op.risk_class == ConnectorRiskClass.WRITE
        assert op.sensitive is True


class TestConnectorManifest:
    """Test ConnectorManifest class."""

    def test_create_valid_manifest(self):
        """Test creating a valid manifest."""
        manifest = ConnectorManifest(
            uid="test-connector",
            display_name="Test Connector",
            version="1.0.0",
            description="A test connector",
            base_url="https://api.example.com",
            auth_type=ConnectorAuthType.BEARER,
        )
        errors = manifest.validate()
        assert len(errors) == 0

    def test_invalid_uid(self):
        """Test that invalid UIDs are rejected."""
        manifest = ConnectorManifest(
            uid="Invalid UID!",
            display_name="Test",
            version="1.0.0",
            description="Test",
        )
        errors = manifest.validate()
        assert any("Invalid connector UID" in e for e in errors)

    def test_invalid_display_name(self):
        """Test that invalid display names are rejected."""
        manifest = ConnectorManifest(
            uid="test",
            display_name="Invalid Name!",
            version="1.0.0",
            description="Test",
        )
        errors = manifest.validate()
        assert any("Invalid display name" in e for e in errors)

    def test_invalid_version(self):
        """Test that invalid versions are rejected."""
        manifest = ConnectorManifest(
            uid="test",
            display_name="Test",
            version="invalid",
            description="Test",
        )
        errors = manifest.validate()
        assert any("Invalid version" in e for e in errors)

    def test_missing_description(self):
        """Test that missing descriptions are rejected."""
        manifest = ConnectorManifest(
            uid="test",
            display_name="Test",
            version="1.0.0",
            description="",  # Empty description should fail
        )
        errors = manifest.validate()
        assert any("Description is required" in e for e in errors)

    def test_operational_requires_base_url(self):
        """Test that operational status requires base_url."""
        manifest = ConnectorManifest(
            uid="test",
            display_name="Test",
            version="1.0.0",
            description="Test",
            status=ConnectorStatus.OPERATIONAL,
        )
        errors = manifest.validate()
        assert any("base_url" in e for e in errors)

    def test_duplicate_operation_names(self):
        """Test that duplicate operation names are rejected."""
        manifest = ConnectorManifest(
            uid="test",
            display_name="Test",
            version="1.0.0",
            description="Test",
            operations=[
                ConnectorOperation(name="op", method="GET", description="Op"),
                ConnectorOperation(name="op", method="POST", description="Op"),
            ],
        )
        errors = manifest.validate()
        assert any("Duplicate operation names" in e for e in errors)

    def test_to_dict(self):
        """Test converting manifest to dictionary."""
        manifest = ConnectorManifest(
            uid="test",
            display_name="Test",
            version="1.0.0",
            description="Test",
            auth_type=ConnectorAuthType.BEARER,
            operations=[
                ConnectorOperation(name="op1", method="GET", description="Op1"),
            ],
        )
        data = manifest.to_dict()
        assert data["uid"] == "test"
        assert data["auth_type"] == "bearer"
        assert len(data["operations"]) == 1

    def test_from_dict(self):
        """Test creating manifest from dictionary."""
        data = {
            "uid": "test",
            "display_name": "Test",
            "version": "1.0.0",
            "description": "Test",
            "auth_type": "bearer",
            "operations": [{"name": "op1", "method": "GET", "description": "Op1"}],
        }
        manifest = ConnectorManifest.from_dict(data)
        assert manifest.uid == "test"
        assert manifest.auth_type == ConnectorAuthType.BEARER
        assert len(manifest.operations) == 1


class TestConnectorConfig:
    """Test ConnectorConfig class."""

    def test_create_config(self):
        """Test creating a config."""
        config = ConnectorConfig()
        assert config.version == "1.0.0"
        assert len(config.manifests) == 0
        assert len(config.connections) == 0

    def test_add_manifest(self):
        """Test adding a manifest to config."""
        config = ConnectorConfig()
        manifest = ConnectorManifest(
            uid="test",
            display_name="Test",
            version="1.0.0",
            description="Test",
        )
        config.manifests["test"] = manifest
        assert "test" in config.manifests
        assert len(config.manifests) == 1

    def test_validate_config(self):
        """Test validating a config."""
        config = ConnectorConfig()
        errors = config.validate()
        assert len(errors) == 0
        # Empty config should be valid

    def test_validate_with_invalid_manifest(self):
        """Test that invalid manifests cause validation errors."""
        config = ConnectorConfig()
        manifest = ConnectorManifest(
            uid="test",
            display_name="Test",
            version="1.0.0",
            description="",  # Empty description should fail
        )
        config.manifests["test"] = manifest
        errors = config.validate()
        assert len(errors) > 0

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = ConnectorConfig()
        config.manifests["test"] = ConnectorManifest(
            uid="test",
            display_name="Test",
            version="1.0.0",
            description="Test",
        )
        data = config.to_dict()
        assert "manifests" in data
        assert "test" in data["manifests"]
        assert "connections" in data
        assert "defaults" in data

    def test_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "version": "1.0.0",
            "manifests": {
                "test": {
                    "uid": "test",
                    "display_name": "Test",
                    "version": "1.0.0",
                    "description": "Test",
                }
            },
            "connections": {},
            "defaults": {"user": {}, "project": {}, "task": {}},
        }
        config = ConnectorConfig.from_dict(data)
        assert "test" in config.manifests
        assert config.version == "1.0.0"
        assert len(config.connections) == 0


class TestConnectorConfigLoader:
    """Test ConnectorConfigLoader class."""

    def test_load_nonexistent_file(self):
        """Test loading a non-existent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = ConnectorConfigLoader(Path(tmpdir) / "nonexistent.json")
            config = loader.load()
            assert isinstance(config, ConnectorConfig)
            assert len(config.manifests) == 0
            assert len(config.connections) == 0

    def test_load_json_config(self):
        """Test loading a JSON config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_data = {
                "version": "1.0.0",
                "manifests": {
                    "test": {
                        "uid": "test",
                        "display_name": "Test",
                        "version": "1.0.0",
                        "description": "Test",
                    }
                },
                "connections": {},
                "defaults": {"user": {}, "project": {}, "task": {}},
            }
            config_path.write_text(json.dumps(config_data, indent=2))
            loader = ConnectorConfigLoader(config_path)
            config = loader.load()
            assert "test" in config.manifests
            assert config.version == "1.0.0"
            assert len(config.connections) == 0

    def test_load_yaml_config(self):
        """Test loading a YAML config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_data = {
                "version": "1.0.0",
                "manifests": {
                    "test": {
                        "uid": "test",
                        "display_name": "Test",
                        "version": "1.0.0",
                        "description": "Test",
                    }
                },
                "connections": {},
                "defaults": {"user": {}, "project": {}, "task": {}},
            }
            config_path.write_text(yaml.dump(config_data))
            loader = ConnectorConfigLoader(config_path)
            config = loader.load()
            assert "test" in config.manifests
            assert len(config.connections) == 0

    def test_save_json_config(self):
        """Test saving a JSON config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config = ConnectorConfig()
            config.manifests["test"] = ConnectorManifest(
                uid="test",
                display_name="Test",
                version="1.0.0",
                description="Test",
            )
            loader = ConnectorConfigLoader(config_path)
            loader.save(config)
            assert config_path.exists()
            loaded = json.loads(config_path.read_text())
            assert "test" in loaded["manifests"]
            assert "connections" in loaded
            assert "defaults" in loaded

    def test_save_yaml_config(self):
        """Test saving a YAML config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config = ConnectorConfig()
            config.manifests["test"] = ConnectorManifest(
                uid="test",
                display_name="Test",
                version="1.0.0",
                description="Test",
            )
            loader = ConnectorConfigLoader(config_path)
            loader.save(config)
            assert config_path.exists()
            loaded = yaml.safe_load(config_path.read_text())
            assert "test" in loaded["manifests"]
            assert "connections" in loaded
            assert "defaults" in loaded

    def test_load_invalid_json(self):
        """Test loading invalid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text("invalid json")
            loader = ConnectorConfigLoader(config_path)
            with pytest.raises(ConnectorConfigError):
                loader.load()

    def test_load_invalid_yaml(self):
        """Test loading invalid YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text("invalid: yaml: [")
            loader = ConnectorConfigLoader(config_path)
            with pytest.raises(ConnectorConfigError):
                loader.load()

    def test_validate_file(self):
        """Test validating a config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_data = {
                "version": "1.0.0",
                "manifests": {
                    "test": {
                        "uid": "test",
                        "display_name": "Test",
                        "version": "1.0.0",
                        "description": "Test",
                    }
                },
            }
            config_path.write_text(json.dumps(config_data, indent=2))
            loader = ConnectorConfigLoader(config_path)
            errors = loader.validate_file()
            assert len(errors) == 0

    def test_validate_invalid_file(self):
        """Test validating an invalid config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text("invalid")
            loader = ConnectorConfigLoader(config_path)
            errors = loader.validate_file()
            assert len(errors) > 0


class TestConnectorConfigManager:
    """Test ConnectorConfigManager class."""

    def test_get_manifest(self):
        """Test getting a manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConnectorConfigManager(Path(tmpdir) / "config.json")
            manifest = ConnectorManifest(
                uid="test",
                display_name="Test",
                version="1.0.0",
                description="Test",
            )
            manager.config.manifests["test"] = manifest
            manager.loader.save(manager.config)

            retrieved = manager.get_manifest("test")
            assert retrieved is not None
            assert retrieved.uid == "test"
            assert len(manager.config.manifests) == 1

    def test_list_manifests(self):
        """Test listing all manifests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConnectorConfigManager(Path(tmpdir) / "config.json")
            manager.config.manifests["test1"] = ConnectorManifest(
                uid="test1",
                display_name="Test 1",
                version="1.0.0",
                description="Test",
            )
            manager.config.manifests["test2"] = ConnectorManifest(
                uid="test2",
                display_name="Test 2",
                version="1.0.0",
                description="Test",
            )
            manager.loader.save(manager.config)

            manifests = manager.list_manifests()
            assert len(manifests) == 2
            assert manifests[0].display_name == "Test 1"
            assert manifests[1].display_name == "Test 2"
            assert len(manager.config.manifests) == 2

    def test_add_manifest(self):
        """Test adding a manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConnectorConfigManager(Path(tmpdir) / "config.json")
            manifest = ConnectorManifest(
                uid="new-test",
                display_name="New Test",
                version="1.0.0",
                description="Test",
            )
            errors = manager.add_manifest(manifest)
            assert len(errors) == 0
            assert "new-test" in manager.config.manifests
            assert len(manager.config.manifests) == 1

    def test_add_invalid_manifest(self):
        """Test adding an invalid manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConnectorConfigManager(Path(tmpdir) / "config.json")
            manifest = ConnectorManifest(
                uid="test",
                display_name="Test",
                version="1.0.0",
                description="",  # Empty description should fail
            )
            errors = manager.add_manifest(manifest)
            assert len(errors) > 0
            assert "test" not in manager.config.manifests

    def test_remove_manifest(self):
        """Test removing a manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConnectorConfigManager(Path(tmpdir) / "config.json")
            manifest = ConnectorManifest(
                uid="test",
                display_name="Test",
                version="1.0.0",
                description="Test",
            )
            manager.config.manifests["test"] = manifest
            manager.loader.save(manager.config)

            result = manager.remove_manifest("test")
            assert result is True
            assert "test" not in manager.config.manifests
            assert len(manager.config.manifests) == 0

    def test_remove_nonexistent_manifest(self):
        """Test removing a nonexistent manifest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConnectorConfigManager(Path(tmpdir) / "config.json")
            result = manager.remove_manifest("nonexistent")
            assert result is False

    def test_get_dependencies(self):
        """Test getting dependencies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConnectorConfigManager(Path(tmpdir) / "config.json")
            manager.config.manifests["dep1"] = ConnectorManifest(
                uid="dep1",
                display_name="Dependency 1",
                version="1.0.0",
                description="Test",
            )
            manager.config.manifests["dep2"] = ConnectorManifest(
                uid="dep2",
                display_name="Dependency 2",
                version="1.0.0",
                description="Test",
            )
            manager.config.manifests["main"] = ConnectorManifest(
                uid="main",
                display_name="Main",
                version="1.0.0",
                description="Test",
                dependencies=["dep1", "dep2"],
            )
            manager.loader.save(manager.config)

            deps = manager.get_dependencies("main")
            assert len(deps) == 2
            assert deps[0].uid == "dep1"
            assert deps[1].uid == "dep2"
            assert len(manager.config.manifests) == 3

    def test_resolve_dependencies(self):
        """Test resolving dependencies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConnectorConfigManager(Path(tmpdir) / "config.json")
            manager.config.manifests["dep1"] = ConnectorManifest(
                uid="dep1",
                display_name="Dependency 1",
                version="1.0.0",
                description="Test",
            )
            manager.config.manifests["main"] = ConnectorManifest(
                uid="main",
                display_name="Main",
                version="1.0.0",
                description="Test",
                dependencies=["dep1"],
            )
            manager.loader.save(manager.config)

            resolved = manager.resolve_dependencies(["main"])
            assert len(resolved) == 2
            assert "main" in [m.uid for m in resolved]
            assert "dep1" in [m.uid for m in resolved]
            assert len(manager.config.manifests) == 2

    def test_get_version_info(self):
        """Test getting version information."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConnectorConfigManager(Path(tmpdir) / "config.json")
            manifest = ConnectorManifest(
                uid="test",
                display_name="Test",
                version="1.0.0",
                description="Test",
                base_url="https://api.example.com",
                auth_type=ConnectorAuthType.BEARER,
            )
            manager.config.manifests["test"] = manifest
            manager.loader.save(manager.config)

            info = manager.get_version_info("test")
            assert info["uid"] == "test"
            assert info["version"] == "1.0.0"
            assert info["base_url"] == "https://api.example.com"
            assert info["auth_type"] == "bearer"

    def test_get_all_version_info(self):
        """Test getting version info for all connectors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConnectorConfigManager(Path(tmpdir) / "config.json")
            manager.config.manifests["test1"] = ConnectorManifest(
                uid="test1",
                display_name="Test 1",
                version="1.0.0",
                description="Test",
            )
            manager.config.manifests["test2"] = ConnectorManifest(
                uid="test2",
                display_name="Test 2",
                version="1.0.0",
                description="Test",
            )
            manager.loader.save(manager.config)

            infos = manager.get_all_version_info()
            assert len(infos) == 2
            assert infos[0]["uid"] == "test1"
            assert infos[1]["uid"] == "test2"

    def test_update_status(self):
        """Test updating connector status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConnectorConfigManager(Path(tmpdir) / "config.json")
            manifest = ConnectorManifest(
                uid="test",
                display_name="Test",
                version="1.0.0",
                description="Test",
            )
            manager.config.manifests["test"] = manifest
            manager.loader.save(manager.config)

            result = manager.update_status("test", ConnectorStatus.OPERATIONAL)
            assert result is True
            assert manager.config.manifests["test"].status == ConnectorStatus.OPERATIONAL
            assert len(manager.config.manifests) == 1

    def test_update_nonexistent_status(self):
        """Test updating status of nonexistent connector."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConnectorConfigManager(Path(tmpdir) / "config.json")
            result = manager.update_status("nonexistent", ConnectorStatus.OPERATIONAL)
            assert result is False

    def test_validate_all(self):
        """Test validating all manifests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ConnectorConfigManager(Path(tmpdir) / "config.json")
            manager.config.manifests["valid"] = ConnectorManifest(
                uid="valid",
                display_name="Valid",
                version="1.0.0",
                description="Test",
            )
            manager.config.manifests["invalid"] = ConnectorManifest(
                uid="invalid",
                display_name="Invalid",
                version="1.0.0",
                description="",  # Empty description should fail
            )
            manager.loader.save(manager.config)

            errors = manager.validate_all()
            assert len(errors) > 0
            assert any("Description is required" in e for e in errors)
            assert len(manager.config.manifests) == 2
