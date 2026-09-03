"""Fail-closed validation for production API boundary configuration."""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class ProductionBoundaryConfig:
    identity_issuer: str
    authorization_scopes: frozenset[str]
    tls_enabled: bool
    cors_origins: tuple[str, ...]
    secret_reference: str
    audit_sink: str

    def validate(self) -> None:
        if not self.identity_issuer or urlparse(self.identity_issuer).scheme != "https":
            raise ValueError("identity_issuer must be an HTTPS URL")
        if not self.authorization_scopes:
            raise ValueError("authorization_scopes must not be empty")
        if not self.tls_enabled:
            raise ValueError("TLS must be enabled for production")
        if not self.cors_origins or any(origin == "*" for origin in self.cors_origins):
            raise ValueError("CORS origins must be explicit and non-wildcard")
        if not self.secret_reference or any(marker in self.secret_reference.lower() for marker in ("sk-", "token", "password", "secret-value")):
            raise ValueError("secret_reference must be an opaque deployment reference, not a credential")
        if not self.audit_sink:
            raise ValueError("audit_sink is required")
