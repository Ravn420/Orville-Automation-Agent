from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from orville_core.browser_approvals import approval_scope_digest, create_browser_approval


def test_approval_records_scope_without_field_values() -> None:
    record = create_browser_approval("approval-1", "browser-1", "form_submission", "https://example.test/submit", {"Email": "user@example.test", "Password": "secret"})
    payload = record.to_dict()
    assert payload["field_names"] == ["Email", "Password"]
    assert "secret" not in str(payload)
    assert len(approval_scope_digest(record)) == 64


def test_approval_expiry_and_repeated_decision_are_fail_closed() -> None:
    now = datetime.now(UTC)
    record = create_browser_approval("approval-1", "browser-1", "download", "https://example.test/file", now=now, ttl_seconds=10)
    record.validate(now + timedelta(seconds=11))
    assert record.status == "expired"
    with pytest.raises(ValueError, match="no longer pending"):
        record.decide(True)


@pytest.mark.parametrize("action", ["navigate", "takeover_request"])
def test_only_side_effecting_browser_actions_get_records(action: str) -> None:
    with pytest.raises(ValueError, match="unsupported"):
        create_browser_approval("approval-1", "browser-1", action, "https://example.test")
