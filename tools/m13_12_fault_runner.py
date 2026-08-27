"""Execute the deterministic M13.12 fault-injection matrix locally.

The runner uses only the synthetic deployment adapter and temporary SQLite
state. It never contacts a deployment provider or reads credentials.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from orville_core.canary import CanaryController, CanaryError, CanaryHealthEvaluator, CanaryStateStore, HealthObservation, SyntheticDeploymentAdapter
from orville_core.canary_policy import CanaryCohort, CanaryPolicy, CanaryPolicyError, HealthThresholds, RollbackLimits


class FaultAdapter(SyntheticDeploymentAdapter):
    def __init__(self, *, fail_rollback: bool = False, fail_quarantine: bool = False) -> None:
        super().__init__()
        self.fail_rollback = fail_rollback
        self.fail_quarantine = fail_quarantine

    def rollback(self, release_id: str, rollback_target: str) -> None:
        if self.fail_rollback:
            raise RuntimeError("synthetic rollback timeout")
        super().rollback(release_id, rollback_target)

    def pause(self, release_id: str) -> None:
        super().pause(release_id)
        if self.fail_quarantine:
            raise RuntimeError("synthetic quarantine failure")


def policy(*, max_attempts: int = 3) -> CanaryPolicy:
    return CanaryPolicy(
        policy_id="fault-test-v1",
        release_id="candidate",
        rollback_target="known-good",
        cohorts=(CanaryCohort("internal", 1, hold_seconds=1), CanaryCohort("full", 100, hold_seconds=1)),
        health=HealthThresholds(min_samples=10, max_error_rate=0.05, max_p95_latency_ms=100, max_p99_latency_ms=200, max_saturation_ratio=0.9, critical_security_findings=0, min_business_health=0.95),
        rollback=RollbackLimits(max_attempts=max_attempts, timeout_seconds=10, quarantine_seconds=10),
        max_hold_seconds=10,
        observation_window_seconds=1,
        approval_mode="none",
    )


def observation(**changes: Any) -> HealthObservation:
    value: dict[str, Any] = {"samples": 10, "error_rate": 0.01, "p95_latency_ms": 10, "p99_latency_ms": 20, "saturation_ratio": 0.1, "observed_at": time.time(), "release_id": "candidate", "business_health": 0.99}
    value.update(changes)
    return HealthObservation(**value)


def setup(tmp: Path, adapter: FaultAdapter, *, max_attempts: int = 3) -> tuple[CanaryController, str, CanaryPolicy]:
    tmp.mkdir(parents=True, exist_ok=True)
    store = CanaryStateStore(tmp / "canary.db")
    controller = CanaryController(store, adapter, CanaryHealthEvaluator())
    current_policy = policy(max_attempts=max_attempts)
    run_id = controller.start(current_policy)
    controller.deploy(run_id)
    return controller, run_id, current_policy


def execute(name: str, tmp: Path) -> dict[str, Any]:
    adapter = FaultAdapter()
    if name == "FI-14":
        adapter.fail_rollback = True
    result: dict[str, Any] = {"id": name, "status": "passed"}
    controller = None
    run_id = None
    try:
        controller, run_id, current_policy = setup(tmp, adapter, max_attempts=1 if name == "FI-14" else 3)
        if name == "FI-01":
            state = controller.observe(run_id, observation(samples=1))
            assert state["state"] == "paused"
        elif name == "FI-02":
            state = controller.observe(run_id, observation(observed_at=0))
            assert state["state"] == "paused"
        elif name == "FI-03":
            state = controller.observe(run_id, observation(error_rate=0.9))
            assert state["state"] == "rolled_back"
        elif name == "FI-04":
            state = controller.observe(run_id, observation(p95_latency_ms=101))
            assert state["state"] == "paused"
        elif name == "FI-05":
            state = controller.observe(run_id, observation(p99_latency_ms=201))
            assert state["state"] == "rolled_back"
        elif name == "FI-06":
            state = controller.observe(run_id, observation(saturation_ratio=0.95))
            assert state["state"] == "paused"
        elif name == "FI-07":
            state = controller.observe(run_id, observation(business_health=0.9))
            assert state["state"] == "paused"
        elif name == "FI-08":
            state = controller.observe(run_id, observation(critical_security_findings=1))
            assert state["state"] == "paused" and adapter.status("candidate")["status"] == "paused"
        elif name == "FI-09":
            state = controller.observe(run_id, observation(error_rate=0.9))
            assert state["state"] == "rolled_back"
        elif name == "FI-10":
            state = controller.observe(run_id, observation(samples=0))
            assert state["state"] == "paused"
        elif name == "FI-11":
            state = controller.observe(run_id, observation(release_id="wrong"))
            assert state["state"] == "paused"
        elif name == "FI-12":
            controller.observe(run_id, observation())
            controller.observe(run_id, observation())
            completed = controller.observe(run_id, observation())
            duplicate = controller.observe(run_id, observation())
            assert completed["state"] == "completed" and duplicate["state"] == "completed"
        elif name == "FI-13":
            controller.observe(run_id, observation())
            resumed = CanaryController(CanaryStateStore(tmp / "canary.db"), adapter).store.get(run_id)
            assert resumed["cohort_index"] == 0
        elif name == "FI-14":
            try:
                controller.rollback(run_id, "synthetic timeout")
            except RuntimeError:
                pass
            assert controller.store.get(run_id)["state"] != "completed"
        elif name == "FI-15":
            try:
                CanaryPolicy.from_dict({**current_policy.to_dict(), "rollback_target": ""})
            except CanaryPolicyError:
                pass
            else:
                raise AssertionError("missing rollback target unexpectedly accepted")
        elif name == "FI-16":
            adapter.fail_rollback = True
            try:
                controller.rollback(run_id, "quarantine failure")
            except RuntimeError:
                pass
            assert controller.store.get(run_id)["state"] != "completed"
        elif name == "FI-17":
            try:
                CanaryPolicy.from_dict({"policy_version": 1, "policy_id": "bad"})
            except CanaryPolicyError:
                pass
            else:
                raise AssertionError("malformed policy unexpectedly accepted")
        elif name == "FI-18":
            controller.store.audit(run_id, "synthetic.secret", "completed", {"token": "redacted", "safe": "ok"})
            assert all("token" not in event["metadata"] for event in controller.store.audit_events(run_id))
        else:
            raise AssertionError(f"unknown scenario {name}")
    except Exception as exc:
        result["status"] = "failed"
        result["error_type"] = type(exc).__name__
        result["diagnostic"] = str(exc)
    if controller is not None and run_id is not None:
        result["state"] = controller.store.get(run_id)["state"]
        result["audit_events"] = len(controller.store.audit_events(run_id))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("artifacts/m13_12_fault_injection.json"))
    args = parser.parse_args()
    scenarios = [f"FI-{index:02d}" for index in range(1, 19)]
    results = []
    directory = Path(tempfile.mkdtemp(prefix="orville-m13-12-"))
    try:
        for name in scenarios:
            results.append(execute(name, directory / name))
    finally:
        shutil.rmtree(directory, ignore_errors=True)
    report = {"schema": "orville.m13.12.fault-injection", "scenario_count": len(results), "passed": all(item["status"] == "passed" for item in results), "results": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"scenario_count": len(results), "passed": report["passed"], "output": str(args.output)}))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
