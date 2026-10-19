"""Portable provider and local-model configuration schemas with environment support."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class EndpointConfigError(ValueError):
    pass


class EnvironmentError(ValueError):
    """Raised when environment-specific configuration is invalid."""


@dataclass(frozen=True)
class EnvironmentConfig:
    """Environment-specific configuration for endpoints."""
    name: str
    allowed_hosts: tuple[str, ...] = ()
    allowed_ports: tuple[int, ...] = ()
    allow_private_network: bool = False
    timeout_multiplier: float = 1.0
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    enable_ssl_verification: bool = True
    custom_headers: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate environment configuration."""
        if not self.name:
            raise EnvironmentError("Environment name must be non-empty")
        if self.timeout_multiplier <= 0:
            raise EnvironmentError("timeout_multiplier must be positive")
        if self.max_retries < 0:
            raise EnvironmentError("max_retries must be non-negative")
        if self.retry_delay_seconds < 0:
            raise EnvironmentError("retry_delay_seconds must be non-negative")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnvironmentConfig:
        """Create EnvironmentConfig from dictionary."""
        return cls(
            name=data.get("name", "default"),
            allowed_hosts=tuple(data.get("allowed_hosts", [])),
            allowed_ports=tuple(data.get("allowed_ports", [])),
            allow_private_network=data.get("allow_private_network", False),
            timeout_multiplier=data.get("timeout_multiplier", 1.0),
            max_retries=data.get("max_retries", 3),
            retry_delay_seconds=data.get("retry_delay_seconds", 1.0),
            enable_ssl_verification=data.get("enable_ssl_verification", True),
            custom_headers=data.get("custom_headers", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "allowed_hosts": list(self.allowed_hosts),
            "allowed_ports": list(self.allowed_ports),
            "allow_private_network": self.allow_private_network,
            "timeout_multiplier": self.timeout_multiplier,
            "max_retries": self.max_retries,
            "retry_delay_seconds": self.retry_delay_seconds,
            "enable_ssl_verification": self.enable_ssl_verification,
            "custom_headers": self.custom_headers,
        }

    @classmethod
    def from_file(cls, path: Path) -> EnvironmentConfig:
        """Load EnvironmentConfig from JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_file(self, path: Path) -> None:
        """Save EnvironmentConfig to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def get_default(cls) -> EnvironmentConfig:
        """Get default environment configuration."""
        return cls(name="default")

    @classmethod
    def get_local(cls) -> EnvironmentConfig:
        """Get local development environment configuration."""
        return cls(
            name="local",
            allow_private_network=True,
            timeout_multiplier=0.5,
            max_retries=1,
        )

    @classmethod
    def get_staging(cls) -> EnvironmentConfig:
        """Get staging environment configuration."""
        return cls(
            name="staging",
            timeout_multiplier=1.0,
            max_retries=2,
        )

    @classmethod
    def get_production(cls) -> EnvironmentConfig:
        """Get production environment configuration."""
        return cls(
            name="production",
            timeout_multiplier=1.5,
            max_retries=3,
            enable_ssl_verification=True,
        )


@dataclass(frozen=True)
class ProviderEndpointSpec:
    provider_id: str
    display_name: str
    provider_type: str
    endpoint_url: str
    model_identifier: str
    protocol: str
    api_key_reference: str | None = None
    capabilities: tuple[str, ...] = ()
    timeout_seconds: float = 60.0
    enabled: bool = True
    environment: str = "default"
    environment_config: EnvironmentConfig | None = None

    @property
    def metadata(self) -> dict[str, Any]:
        """Return metadata from environment config if available."""
        if self.environment_config:
            return {
                "custom_headers": self.environment_config.custom_headers,
                "environment": self.environment_config.name,
            }
        return {}

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.provider_id, self.display_name, self.provider_type, self.endpoint_url, self.model_identifier, self.protocol)):
            raise EndpointConfigError("provider identity, endpoint, model, and protocol must be non-empty")
        parsed = urlparse(self.endpoint_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.fragment:
            raise EndpointConfigError("provider endpoint must be an HTTP(S) URL with a host and no fragment")
        if self.timeout_seconds <= 0:
            raise EndpointConfigError("provider timeout must be positive")
        if self.api_key_reference and any(secret in self.api_key_reference.lower() for secret in ("bearer ", "api_key", "apikey=", "sk-")):
            raise EndpointConfigError("api_key_reference must identify a secret, not contain its value")
        if self.environment is not None and not self.environment.strip():
            raise EndpointConfigError("environment must be non-empty")

    def get_effective_timeout(self) -> float:
        """Get effective timeout considering environment configuration."""
        if self.environment_config and self.environment == self.environment_config.name:
            return self.timeout_seconds * self.environment_config.timeout_multiplier
        return self.timeout_seconds

    def redacted(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "display_name": self.display_name,
            "provider_type": self.provider_type,
            "endpoint_url": self.endpoint_url,
            "model_identifier": self.model_identifier,
            "protocol": self.protocol,
            "api_key_reference": self.api_key_reference,
            "capabilities": list(self.capabilities),
            "timeout_seconds": self.timeout_seconds,
            "enabled": self.enabled,
            "environment": self.environment,
        }


@dataclass(frozen=True)
class LocalModelSpec:
    model_id: str
    source_path: Path
    checksum_sha256: str
    file_format: str
    architecture: str | None = None
    quantization: str | None = None
    runtime: str | None = None
    capabilities: tuple[str, ...] = ()
    license_name: str | None = None
    validation_status: str = "unvalidated"
    user_owned: bool = True
    environment: str = "default"
    environment_config: EnvironmentConfig | None = None

    def __post_init__(self) -> None:
        if not self.model_id.strip() or not self.checksum_sha256.strip() or not self.file_format.strip():
            raise EndpointConfigError("local model ID, checksum, and format must be non-empty")
        if len(self.checksum_sha256) != 64 or any(char not in "0123456789abcdefABCDEF" for char in self.checksum_sha256):
            raise EndpointConfigError("checksum_sha256 must be a 64-character hexadecimal digest")
        if self.validation_status not in {"unvalidated", "valid", "invalid", "active", "inactive"}:
            raise EndpointConfigError("unsupported local model validation status")
        if self.environment is not None and not self.environment.strip():
            raise EndpointConfigError("environment must be non-empty")

    def get_effective_timeout(self) -> float:
        """Get effective timeout considering environment configuration."""
        if self.environment_config:
            return 5.0 * self.environment_config.timeout_multiplier  # Base 5s timeout for local models
        return 5.0

    def redacted(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "source_path": self.source_path.as_posix(),
            "checksum_sha256": self.checksum_sha256,
            "file_format": self.file_format,
            "architecture": self.architecture,
            "quantization": self.quantization,
            "runtime": self.runtime,
            "capabilities": list(self.capabilities),
            "license_name": self.license_name,
            "validation_status": self.validation_status,
            "user_owned": self.user_owned,
            "environment": self.environment,
        }
