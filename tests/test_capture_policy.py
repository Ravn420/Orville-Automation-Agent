from datetime import UTC, datetime, timedelta

import pytest

from orville_core.capture_policy import CapturePolicy, CaptureStore
from orville_core.security import SecurityViolation


NOW = datetime(2026, 8, 28, 12, 0, tzinfo=UTC)


def test_capture_is_opt_in_and_redacted():
    disabled = CaptureStore(CapturePolicy())
    assert disabled.capture("run-1", "prompt", "secret", actor="owner", now=NOW) is None

    store = CaptureStore(CapturePolicy(enabled=True, allowed_readers=frozenset({"owner"}), retention_seconds=60))
    record = store.capture(
        "run-1",
        "tool_arguments",
        {"api_key": "real-secret", "nested": {"token": "tok_secret123"}},
        actor="owner",
        now=NOW,
    )
    assert record is not None
    assert record.payload == {"api_key": "[REDACTED]", "nested": {"token": "[REDACTED]"}}
    assert store.read(actor="owner", now=NOW) == (record,)


def test_capture_requires_access_and_supported_kind():
    store = CaptureStore(CapturePolicy(enabled=True, allowed_readers=frozenset({"owner"}), retention_seconds=60))
    with pytest.raises(SecurityViolation):
        store.capture("run-1", "prompt", "text", actor="intruder", now=NOW)
    with pytest.raises(SecurityViolation):
        store.read(actor="intruder", now=NOW)
    with pytest.raises(ValueError):
        store.capture("run-1", "unknown", "text", actor="owner", now=NOW)


def test_capture_is_bounded_and_expires():
    store = CaptureStore(
        CapturePolicy(enabled=True, allowed_readers=frozenset({"owner"}), retention_seconds=60, max_payload_chars=5)
    )
    record = store.capture("run-1", "completion", "123456789", actor="owner", now=NOW)
    assert record is not None
    assert record.payload == "12345...[truncated]"
    assert store.read(actor="owner", now=NOW + timedelta(seconds=59)) == (record,)
    assert store.read(actor="owner", now=NOW + timedelta(seconds=60)) == ()


def test_enabled_policy_requires_reader_and_retention():
    with pytest.raises(ValueError):
        CaptureStore(CapturePolicy(enabled=True, allowed_readers=frozenset(), retention_seconds=60))
    with pytest.raises(ValueError):
        CaptureStore(CapturePolicy(enabled=True, allowed_readers=frozenset({"owner"}), retention_seconds=0))
