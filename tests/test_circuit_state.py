from __future__ import annotations

import time
from pathlib import Path

import pytest

from orville_core import (
    LLMRequest,
    LLMResponse,
    ProviderConfig,
    ProviderError,
    ProviderRegistry,
    ProviderRouter,
    RoutingRequest,
    SQLiteCircuitStateStore,
)


class AlwaysFailingProvider:
    def __init__(self, provider_id: str = "provider") -> None:
        self.config = ProviderConfig(provider_id, "ollama", "model", "http://localhost")
        self.calls = 0

    def generate(self, request: LLMRequest) -> LLMResponse:
        self.calls += 1
        raise ProviderError("temporary upstream outage")


def test_sqlite_state_is_visible_to_independent_store_instances(tmp_path: Path) -> None:
    database = tmp_path / "state.sqlite3"
    first = SQLiteCircuitStateStore(database)
    second = SQLiteCircuitStateStore(database)

    assert first.record_failure("shared", now=100.0) == 1
    assert second.record_failure("shared", now=101.0) == 2
    assert first.failure_count("shared") == 2
    assert second.state("shared", failure_threshold=2, cooldown_seconds=30, now=110.0) == "open"
    assert first.state("shared", failure_threshold=2, cooldown_seconds=30, now=132.0) == "half_open"

    second.record_success("shared")
    assert first.state("shared", failure_threshold=2, cooldown_seconds=30, now=132.0) == "closed"


def test_router_instances_share_open_circuit_state(tmp_path: Path) -> None:
    database = tmp_path / "state.sqlite3"
    provider = AlwaysFailingProvider("shared")
    registry = ProviderRegistry()
    registry.register(provider)
    request = LLMRequest([{"role": "user", "content": "hello"}])

    router_one = ProviderRouter(
        registry,
        circuit_store=SQLiteCircuitStateStore(database),
        failure_threshold=1,
        retry_attempts=0,
    )
    with pytest.raises(ProviderError):
        router_one.generate(request)
    assert provider.calls == 1

    router_two = ProviderRouter(
        registry,
        circuit_store=SQLiteCircuitStateStore(database),
        failure_threshold=1,
        cooldown_seconds=30,
        retry_attempts=0,
    )
    assert router_two.circuit_state("shared") == "open"
    assert router_two.candidates(RoutingRequest()) == []
    assert provider.calls == 1


def test_sqlite_store_recovers_after_cooldown_and_success_clears_state(tmp_path: Path) -> None:
    database = tmp_path / "state.sqlite3"
    store = SQLiteCircuitStateStore(database)
    store.record_failure("recover", now=time.time() - 60)
    assert store.state("recover", failure_threshold=1, cooldown_seconds=30) == "half_open"
    store.record_success("recover")
    assert store.failure_count("recover") == 0
