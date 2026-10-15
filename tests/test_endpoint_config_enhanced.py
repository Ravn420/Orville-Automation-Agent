"""Enhanced tests for endpoint configuration with environment support."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from orville_core import (
    EndpointConfigError,
    EnvironmentConfig,
    EnvironmentError,
    LocalModelSpec,
    ProviderEndpointSpec,
)


def test_environment_config_file_operations():
    """Test EnvironmentConfig file I/O."""
    config = EnvironmentConfig(
        name="test",
        timeout_multiplier=2.0,
        max_retries=5,
    )

    # Save to file
    config_path = Path(".orville/test_env_config.json")
    config.to_file(config_path)
    assert config_path.exists()

    # Load from file
    loaded_config = EnvironmentConfig.from_file(config_path)
    assert loaded_config.name == "test"
    assert loaded_config.timeout_multiplier == 2.0
    assert loaded_config.max_retries == 5

    # Clean up
    config_path.unlink(missing_ok=True)


def test_environment_config_custom_headers():
    """Test EnvironmentConfig with custom headers."""
    config = EnvironmentConfig(
        name="test",
        custom_headers={"User-Agent": "Orville/1.0", "X-Custom": "value"},
    )
    assert config.custom_headers["User-Agent"] == "Orville/1.0"
    assert config.custom_headers["X-Custom"] == "value"


def test_environment_config_allowed_ports():
    """Test EnvironmentConfig with allowed ports."""
    config = EnvironmentConfig(
        name="test",
        allowed_ports=(80, 443, 8080),
    )
    assert 80 in config.allowed_ports
    assert 443 in config.allowed_ports
    assert 8080 in config.allowed_ports


def test_environment_config_ssl_verification():
    """Test EnvironmentConfig SSL verification settings."""
    config = EnvironmentConfig(
        name="test",
        enable_ssl_verification=True,
    )
    assert config.enable_ssl_verification is True

    config2 = EnvironmentConfig(
        name="test",
        enable_ssl_verification=False,
    )
    assert config2.enable_ssl_verification is False


def test_provider_endpoint_spec_with_environment_config():
    """Test ProviderEndpointSpec with full environment configuration."""
    env_config = EnvironmentConfig(
        name="production",
        timeout_multiplier=1.5,
        max_retries=3,
        retry_delay_seconds=2.0,
        custom_headers={"X-Environment": "production"},
    )

    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
        environment="production",
        environment_config=env_config,
    )

    assert spec.environment == "production"
    assert spec.get_effective_timeout() == 90.0  # 60s * 1.5
    assert spec.metadata.get("custom_headers") == {"X-Environment": "production"}


def test_provider_endpoint_spec_environment_validation():
    """Test that ProviderEndpointSpec validates environment."""
    with pytest.raises(EndpointConfigError, match="environment must be non-empty"):
        ProviderEndpointSpec(
            provider_id="test",
            display_name="Test Provider",
            provider_type="cloud",
            endpoint_url="https://example.test/v1",
            model_identifier="model",
            protocol="openai",
            environment="",
        )


def test_provider_endpoint_spec_effective_timeout_without_config():
    """Test effective timeout when no environment config is provided."""
    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
    )
    assert spec.get_effective_timeout() == 60.0


def test_provider_endpoint_spec_effective_timeout_with_config():
    """Test effective timeout with environment config."""
    env_config = EnvironmentConfig(
        name="staging",
        timeout_multiplier=1.0,
    )
    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
        environment="staging",
        environment_config=env_config,
    )
    assert spec.get_effective_timeout() == 60.0  # 60s * 1.0


def test_local_model_spec_with_environment_config():
    """Test LocalModelSpec with full environment configuration."""
    env_config = EnvironmentConfig(
        name="local",
        timeout_multiplier=0.5,
        allow_private_network=True,
    )

    spec = LocalModelSpec(
        model_id="test-model",
        source_path=Path("/models/test.gguf"),
        checksum_sha256="a" * 64,
        file_format="gguf",
        environment="local",
        environment_config=env_config,
    )

    assert spec.environment == "local"
    assert spec.get_effective_timeout() == 2.5  # 5s * 0.5


def test_local_model_spec_environment_validation():
    """Test that LocalModelSpec validates environment."""
    with pytest.raises(EndpointConfigError, match="environment must be non-empty"):
        LocalModelSpec(
            model_id="test-model",
            source_path=Path("/models/test.gguf"),
            checksum_sha256="a" * 64,
            file_format="gguf",
            environment="",
        )


def test_local_model_spec_effective_timeout_without_config():
    """Test effective timeout when no environment config is provided."""
    spec = LocalModelSpec(
        model_id="test-model",
        source_path=Path("/models/test.gguf"),
        checksum_sha256="a" * 64,
        file_format="gguf",
    )
    assert spec.get_effective_timeout() == 5.0


def test_local_model_spec_effective_timeout_with_config():
    """Test effective timeout with environment config."""
    env_config = EnvironmentConfig(
        name="production",
        timeout_multiplier=1.5,
    )
    spec = LocalModelSpec(
        model_id="test-model",
        source_path=Path("/models/test.gguf"),
        checksum_sha256="a" * 64,
        file_format="gguf",
        environment="production",
        environment_config=env_config,
    )
    assert spec.get_effective_timeout() == 7.5  # 5s * 1.5


def test_provider_endpoint_spec_redacted_with_environment():
    """Test that redacted output includes environment."""
    env_config = EnvironmentConfig(
        name="production",
        timeout_multiplier=1.5,
    )
    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
        environment="production",
        environment_config=env_config,
    )
    redacted = spec.redacted()
    assert redacted["environment"] == "production"
    assert redacted["timeout_seconds"] == 60.0


def test_local_model_spec_redacted_with_environment():
    """Test that redacted output includes environment."""
    env_config = EnvironmentConfig(
        name="local",
        timeout_multiplier=0.5,
    )
    spec = LocalModelSpec(
        model_id="test-model",
        source_path=Path("/models/test.gguf"),
        checksum_sha256="a" * 64,
        file_format="gguf",
        environment="local",
        environment_config=env_config,
    )
    redacted = spec.redacted()
    assert redacted["environment"] == "local"
    assert redacted["source_path"] == "/models/test.gguf"


def test_environment_config_from_dict_with_all_fields():
    """Test EnvironmentConfig from dict with all fields."""
    data = {
        "name": "custom",
        "allowed_hosts": ["example.com", "test.com"],
        "allowed_ports": [80, 443, 8080],
        "allow_private_network": True,
        "timeout_multiplier": 1.2,
        "max_retries": 4,
        "retry_delay_seconds": 1.5,
        "enable_ssl_verification": False,
        "custom_headers": {"X-Custom": "value"},
    }
    config = EnvironmentConfig.from_dict(data)
    assert config.name == "custom"
    assert config.allowed_hosts == ("example.com", "test.com")
    assert config.allowed_ports == (80, 443, 8080)
    assert config.allow_private_network is True
    assert config.timeout_multiplier == 1.2
    assert config.max_retries == 4
    assert config.retry_delay_seconds == 1.5
    assert config.enable_ssl_verification is False
    assert config.custom_headers == {"X-Custom": "value"}


def test_environment_config_to_dict_with_all_fields():
    """Test EnvironmentConfig to dict with all fields."""
    config = EnvironmentConfig(
        name="custom",
        allowed_hosts=("example.com", "test.com"),
        allowed_ports=(80, 443, 8080),
        allow_private_network=True,
        timeout_multiplier=1.2,
        max_retries=4,
        retry_delay_seconds=1.5,
        enable_ssl_verification=False,
        custom_headers={"X-Custom": "value"},
    )
    data = config.to_dict()
    assert data["name"] == "custom"
    assert data["allowed_hosts"] == ["example.com", "test.com"]
    assert data["allowed_ports"] == [80, 443, 8080]
    assert data["allow_private_network"] is True
    assert data["timeout_multiplier"] == 1.2
    assert data["max_retries"] == 4
    assert data["retry_delay_seconds"] == 1.5
    assert data["enable_ssl_verification"] is False
    assert data["custom_headers"] == {"X-Custom": "value"}


def test_environment_config_default_values():
    """Test EnvironmentConfig default values."""
    config = EnvironmentConfig(name="test")
    assert config.allowed_hosts == ()
    assert config.allowed_ports == ()
    assert config.allow_private_network is False
    assert config.timeout_multiplier == 1.0
    assert config.max_retries == 3
    assert config.retry_delay_seconds == 1.0
    assert config.enable_ssl_verification is True
    assert config.custom_headers == {}


def test_provider_endpoint_spec_environment_override():
    """Test that environment can be overridden."""
    env_config = EnvironmentConfig(
        name="production",
        timeout_multiplier=1.5,
    )
    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
        environment="staging",  # Override
        environment_config=env_config,
    )
    assert spec.environment == "staging"
    assert spec.get_effective_timeout() == 60.0  # Uses spec's timeout, not env config


def test_local_model_spec_environment_override():
    """Test that environment can be overridden."""
    env_config = EnvironmentConfig(
        name="production",
        timeout_multiplier=1.5,
    )
    spec = LocalModelSpec(
        model_id="test-model",
        source_path=Path("/models/test.gguf"),
        checksum_sha256="a" * 64,
        file_format="gguf",
        environment="staging",  # Override
        environment_config=env_config,
    )
    assert spec.environment == "staging"
    assert spec.get_effective_timeout() == 7.5  # 5s * 1.5


def test_environment_config_invalid_timeout_multiplier():
    """Test that invalid timeout_multiplier is rejected."""
    with pytest.raises(EnvironmentError, match="timeout_multiplier must be positive"):
        EnvironmentConfig(name="test", timeout_multiplier=0.0)

    with pytest.raises(EnvironmentError, match="timeout_multiplier must be positive"):
        EnvironmentConfig(name="test", timeout_multiplier=-1.0)


def test_environment_config_invalid_max_retries():
    """Test that invalid max_retries is rejected."""
    with pytest.raises(EnvironmentError, match="max_retries must be non-negative"):
        EnvironmentConfig(name="test", max_retries=-1)


def test_environment_config_invalid_retry_delay():
    """Test that invalid retry_delay_seconds is rejected."""
    with pytest.raises(EnvironmentError, match="retry_delay_seconds must be non-negative"):
        EnvironmentConfig(name="test", retry_delay_seconds=-1.0)


def test_environment_config_invalid_name():
    """Test that invalid name is rejected."""
    with pytest.raises(EnvironmentError, match="Environment name must be non-empty"):
        EnvironmentConfig(name="")


def test_provider_endpoint_spec_environment_config_none():
    """Test ProviderEndpointSpec with None environment config."""
    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
        environment="production",
        environment_config=None,
    )
    assert spec.environment_config is None
    assert spec.get_effective_timeout() == 60.0


def test_local_model_spec_environment_config_none():
    """Test LocalModelSpec with None environment config."""
    spec = LocalModelSpec(
        model_id="test-model",
        source_path=Path("/models/test.gguf"),
        checksum_sha256="a" * 64,
        file_format="gguf",
        environment="production",
        environment_config=None,
    )
    assert spec.environment_config is None
    assert spec.get_effective_timeout() == 5.0


def test_environment_config_file_not_found():
    """Test loading config from non-existent file."""
    config_path = Path(".orville/nonexistent.json")
    with pytest.raises(FileNotFoundError):
        EnvironmentConfig.from_file(config_path)


def test_environment_config_file_corrupted():
    """Test loading config from corrupted file."""
    config_path = Path(".orville/corrupted.json")
    with open(config_path, "w", encoding="utf-8") as f:
        f.write("{ invalid json }")

    with pytest.raises(json.JSONDecodeError):
        EnvironmentConfig.from_file(config_path)

    config_path.unlink(missing_ok=True)


def test_provider_endpoint_spec_environment_in_metadata():
    """Test that environment is included in redacted metadata."""
    env_config = EnvironmentConfig(
        name="production",
        timeout_multiplier=1.5,
    )
    spec = ProviderEndpointSpec(
        provider_id="test",
        display_name="Test Provider",
        provider_type="cloud",
        endpoint_url="https://example.test/v1",
        model_identifier="model",
        protocol="openai",
        environment="production",
        environment_config=env_config,
    )
    redacted = spec.redacted()
    assert "environment" in redacted
    assert redacted["environment"] == "production"


def test_local_model_spec_environment_in_metadata():
    """Test that environment is included in redacted metadata."""
    env_config = EnvironmentConfig(
        name="local",
        timeout_multiplier=0.5,
    )
    spec = LocalModelSpec(
        model_id="test-model",
        source_path=Path("/models/test.gguf"),
        checksum_sha256="a" * 64,
        file_format="gguf",
        environment="local",
        environment_config=env_config,
    )
    redacted = spec.redacted()
    assert "environment" in redacted
    assert redacted["environment"] == "local"
