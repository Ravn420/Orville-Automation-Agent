from __future__ import annotations

import pytest

from orville_core.usage_health import Budget, UsageHealthStore


def test_budget_enforcement_and_usage(tmp_path):
    store = UsageHealthStore(tmp_path / "usage.db")
    store.set_budget(Budget("task-1", max_units=10, max_input_tokens=100, max_output_tokens=100, max_calls=2))
    store.record(scope="task-1", category="model", units=4, input_tokens=20, output_tokens=30)
    assert store.usage("task-1")["calls"] == 1
    with pytest.raises(PermissionError, match="units budget"):
        store.record(scope="task-1", category="model", units=7)


def test_provider_health_opens_and_recovers(tmp_path):
    store = UsageHealthStore(tmp_path / "usage.db", failure_threshold=2, cooldown_seconds=0)
    assert store.provider_available("gemini")
    store.record_provider_result("gemini", success=False, message="timeout")
    degraded = store.record_provider_result("gemini", success=False, message="timeout again")
    assert degraded.status == "open"
    assert store.provider_available("gemini")
    recovered = store.record_provider_result("gemini", success=True)
    assert recovered.status == "closed"
    assert store.provider_available("gemini")
