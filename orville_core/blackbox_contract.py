"""Local validation contract for the documented Blackbox API-key boundary.

This module performs no network requests and never handles or serializes API-key
values. It validates only public endpoint, model, capability, and error-shape
metadata before a credential can be stored by an authorized caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


class BlackboxContractError(ValueError):
    """Raised when Blackbox API-key integration metadata is unsafe or unsupported."""


@dataclass(frozen=True)
class BlackboxApiKeyContract:
    base_url: str = "https://api.blackbox.ai"
    model: str = "blackboxai/openai/gpt-5.5"
    timeout_seconds: float = 60.0
    streaming: bool = True
    tool_calling: bool = True
    structured_output: bool = True

    def validate(self) -> str:
        raw = self.base_url.strip().rstrip("/")
        parsed = urlparse(raw)
        if parsed.scheme != "https" or parsed.username or parsed.password or parsed.fragment or not parsed.hostname:
            raise BlackboxContractError("Blackbox API base URL must be HTTPS without credentials or fragments")
        if parsed.hostname.lower() not in {"api.blackbox.ai", "enterprise.blackbox.ai"}:
            raise BlackboxContractError("Blackbox API base URL must use api.blackbox.ai or enterprise.blackbox.ai")
        if self.timeout_seconds <= 0:
            raise BlackboxContractError("Blackbox API timeout must be positive")
        if not self.model.strip() or len(self.model) > 200 or any(char in self.model for char in "\r\n"):
            raise BlackboxContractError("Blackbox model identifier is invalid")
        if not any((self.streaming, self.tool_calling, self.structured_output)):
            raise BlackboxContractError("at least one documented Blackbox request capability must be enabled")
        return raw

    def public(self) -> dict[str, object]:
        return {
            "base_url": self.base_url.rstrip("/"),
            "endpoint_family": "enterprise" if urlparse(self.base_url).hostname == "enterprise.blackbox.ai" else "public",
            "model": self.model,
            "timeout_seconds": self.timeout_seconds,
            "streaming": self.streaming,
            "tool_calling": self.tool_calling,
            "structured_output": self.structured_output,
            "credential_configured": False,
        }


def validate_blackbox_error_payload(payload: object) -> str:
    """Normalize documented error envelopes without retaining response bodies."""
    if not isinstance(payload, dict):
        raise BlackboxContractError("Blackbox error response must be an object")
    error = payload.get("error")
    if isinstance(error, dict):
        code = error.get("code") or error.get("type") or "provider_error"
        return str(code)[:80]
    if isinstance(error, str) and error.strip():
        return "provider_error"
    raise BlackboxContractError("Blackbox error response must contain an error envelope")
