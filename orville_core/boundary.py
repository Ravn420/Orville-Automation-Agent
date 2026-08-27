"""Shared validation and sanitization primitives for external boundaries."""

from __future__ import annotations

import re
from collections.abc import Mapping
from urllib.parse import urlparse


class BoundaryValidationError(ValueError):
    """Raised when untrusted boundary input violates a bounded contract."""


SENSITIVE_KEYS = frozenset({
    "api_key", "apikey", "authorization", "bearer", "cookie", "credential", "password",
    "private_key", "prompt", "objective", "secret", "token", "access_token", "refresh_token",
})


def validate_bounded_text(value: object, *, field: str, max_length: int, required: bool = True) -> str:
    """Validate text input with whitespace normalization and a strict size bound."""
    if not isinstance(value, str):
        raise BoundaryValidationError(f"{field} must be text")
    normalized = value.strip()
    if required and not normalized:
        raise BoundaryValidationError(f"{field} must not be empty")
    if len(normalized) > max_length:
        raise BoundaryValidationError(f"{field} exceeds the maximum length")
    return normalized


def validate_identifier(value: object, *, field: str = "identifier", max_length: int = 200) -> str:
    """Validate a non-secret identifier suitable for correlation and routing."""
    normalized = validate_bounded_text(value, field=field, max_length=max_length)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]*", normalized):
        raise BoundaryValidationError(f"{field} contains unsupported characters")
    return normalized


def validate_external_url(value: object, *, field: str = "url", allow_local: bool = False) -> str:
    """Validate an HTTP(S) URL and reject embedded credentials by default."""
    normalized = validate_bounded_text(value, field=field, max_length=500)
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
        raise BoundaryValidationError(f"{field} must be an HTTP(S) URL without embedded credentials")
    if not allow_local and parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
        raise BoundaryValidationError(f"{field} local endpoints require explicit permission")
    return normalized


def sanitize_external_output(value: object, *, key: str | None = None, max_items: int = 80, max_text: int = 4_000) -> object:
    """Project untrusted output into a bounded, secret-safe structure."""
    if key and key.lower() in SENSITIVE_KEYS:
        return "[redacted]"
    if isinstance(value, Mapping):
        return {str(item_key): sanitize_external_output(item_value, key=str(item_key), max_items=max_items, max_text=max_text) for item_key, item_value in list(value.items())[:max_items]}
    if isinstance(value, (list, tuple)):
        return [sanitize_external_output(item, max_items=max_items, max_text=max_text) for item in list(value)[:max_items]]
    if isinstance(value, str):
        text = value[:max_text]
        text = re.sub(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]+", "Bearer [redacted]", text)
        text = re.sub(r"(?i)(?:sk|key|token)[-_][A-Za-z0-9._-]{8,}", "[redacted-secret]", text)
        if ":\\" in text or "/Users/" in text or "/home/" in text or text.startswith("\\\\"):
            return "[redacted-local-path]"
        return text
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return str(value)[:max_text]
