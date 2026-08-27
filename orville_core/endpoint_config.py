"""Portable provider and local-model configuration schemas."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class EndpointConfigError(ValueError):
    pass


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

    def redacted(self) -> dict[str, Any]:
        return {"provider_id": self.provider_id, "display_name": self.display_name, "provider_type": self.provider_type, "endpoint_url": self.endpoint_url, "model_identifier": self.model_identifier, "protocol": self.protocol, "api_key_reference": self.api_key_reference, "capabilities": list(self.capabilities), "timeout_seconds": self.timeout_seconds, "enabled": self.enabled}


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

    def __post_init__(self) -> None:
        if not self.model_id.strip() or not self.checksum_sha256.strip() or not self.file_format.strip():
            raise EndpointConfigError("local model ID, checksum, and format must be non-empty")
        if len(self.checksum_sha256) != 64 or any(char not in "0123456789abcdefABCDEF" for char in self.checksum_sha256):
            raise EndpointConfigError("checksum_sha256 must be a 64-character hexadecimal digest")
        if self.validation_status not in {"unvalidated", "valid", "invalid", "active", "inactive"}:
            raise EndpointConfigError("unsupported local model validation status")

    def redacted(self) -> dict[str, Any]:
        return {"model_id": self.model_id, "source_path": str(self.source_path), "checksum_sha256": self.checksum_sha256, "file_format": self.file_format, "architecture": self.architecture, "quantization": self.quantization, "runtime": self.runtime, "capabilities": list(self.capabilities), "license_name": self.license_name, "validation_status": self.validation_status, "user_owned": self.user_owned}
