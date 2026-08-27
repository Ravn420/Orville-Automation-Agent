"""Test-only reversible protection for synthetic connector credentials.

This module is intentionally located under ``tests`` and is injected explicitly by
individual tests. Production stores continue to use the default Windows DPAPI
protector and never import or select this implementation.
"""

from __future__ import annotations

import base64

_PREFIX = b"orville-test-protector:"


def protect(value: str) -> str:
    """Wrap a synthetic test credential without persisting its plaintext."""
    return base64.urlsafe_b64encode(_PREFIX + value.encode("utf-8")).decode("ascii")


def unprotect(value: str) -> str:
    """Recover a test-only synthetic credential and reject other envelopes."""
    raw = base64.urlsafe_b64decode(value.encode("ascii"))
    if not raw.startswith(_PREFIX):
        raise ValueError("invalid test-only credential envelope")
    return raw[len(_PREFIX):].decode("utf-8")
