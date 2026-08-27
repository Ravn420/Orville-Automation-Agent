"""Concurrency load test for provider controls.

Uses only local temporary state and synthetic providers. It measures atomic
rate-limit admission and catalog active-model switching under contention.
"""
from __future__ import annotations

import argparse
import json
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from orville_core.provider_features import DiscoveryCatalogStore, ProviderRateLimitStore


def run(workers: int, operations: int) -> dict[str, object]:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
        root = Path(directory)
        rate = ProviderRateLimitStore(root / "usage.db")
        rate.set_limit("synthetic", 60, max_calls=operations // 2, max_tokens=-1)
        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=workers) as pool:
            decisions = list(pool.map(lambda _: rate.admit("synthetic"), range(operations)))
        rate_elapsed = time.perf_counter() - started

        catalog = DiscoveryCatalogStore(root / "catalog.json")
        catalog.record("synthetic", {"provider_type": "openai-compatible", "models": [{"id": f"model-{i}"} for i in range(8)], "count": 8, "status": "ok"})
        started = time.perf_counter()
        with ThreadPoolExecutor(max_workers=workers) as pool:
            selected = list(pool.map(lambda i: catalog.set_active("synthetic", f"model-{i % 8}"), range(operations)))
        switch_elapsed = time.perf_counter() - started
        final = DiscoveryCatalogStore(root / "catalog.json").get("synthetic")
        accepted = sum(1 for allowed, _ in decisions if allowed)
        return {"workers": workers, "operations": operations, "rate_limit": {"accepted": accepted, "rejected": operations - accepted, "elapsed_seconds": round(rate_elapsed, 4), "snapshot": rate.snapshot("synthetic")}, "active_switching": {"completed": len(selected), "elapsed_seconds": round(switch_elapsed, 4), "final_active_model": final["active_model"] if final else None}}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--operations", type=int, default=200)
    parser.add_argument("--output", type=Path, default=Path("artifacts/provider_controls_load_test.json"))
    args = parser.parse_args()
    result = run(max(1, args.workers), max(1, args.operations))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
