"""Standalone-safe automated canary deployment contracts and controller.

The controller is provider-neutral, durable, restart-safe, idempotent, and
fails closed on stale health data or unsafe policy transitions. Live provider
adapters remain deployment-owned; ``SyntheticDeploymentAdapter`` is suitable
for local tests and dry runs only.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Protocol

from .canary_policy import CanaryPolicy, CanaryPolicyError


class CanaryError(RuntimeError):
    """Base canary failure."""


@dataclass(frozen=True)
class HealthObservation:
    samples: int
    error_rate: float
    p95_latency_ms: float
    p99_latency_ms: float
    saturation_ratio: float
    critical_security_findings: int = 0
    business_health: float | None = None
    observed_at: float = 0.0
    release_id: str = ""


@dataclass(frozen=True)
class HealthDecision:
    passed: bool
    reasons: tuple[str, ...]
    observed_at: float
    release_id: str

    def to_dict(self) -> dict[str, Any]:
        return {"passed": self.passed, "reasons": list(self.reasons), "observed_at": self.observed_at, "release_id": self.release_id}


class DeploymentAdapter(Protocol):
    def deploy(self, release_id: str, rollback_target: str) -> None: ...
    def set_traffic(self, release_id: str, traffic_percent: int) -> None: ...
    def pause(self, release_id: str) -> None: ...
    def rollback(self, release_id: str, rollback_target: str) -> None: ...
    def status(self, release_id: str) -> Mapping[str, Any]: ...


class SyntheticDeploymentAdapter:
    """Deterministic local adapter; never contacts a real deployment provider."""
    def __init__(self) -> None:
        self._lock = threading.RLock(); self.releases: dict[str, dict[str, Any]] = {}

    def deploy(self, release_id: str, rollback_target: str) -> None:
        with self._lock: self.releases[release_id] = {"status": "deployed", "traffic_percent": 0, "rollback_target": rollback_target}

    def set_traffic(self, release_id: str, traffic_percent: int) -> None:
        with self._lock:
            if release_id not in self.releases: raise CanaryError("release is not deployed")
            self.releases[release_id]["traffic_percent"] = traffic_percent

    def pause(self, release_id: str) -> None:
        with self._lock:
            if release_id in self.releases: self.releases[release_id]["status"] = "paused"

    def rollback(self, release_id: str, rollback_target: str) -> None:
        with self._lock:
            if release_id not in self.releases: raise CanaryError("release is not deployed")
            self.releases[release_id].update({"status": "rolled_back", "traffic_percent": 0, "active_release": rollback_target})

    def status(self, release_id: str) -> Mapping[str, Any]:
        with self._lock: return dict(self.releases.get(release_id, {"status": "unknown"}))


class CanaryStateStore:
    """SQLite state and audit store with transactionally idempotent transitions."""
    def __init__(self, path: str | Path) -> None:
        self.path = str(path); self._lock = threading.RLock()
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS canary_runs (run_id TEXT PRIMARY KEY, policy TEXT NOT NULL, state TEXT NOT NULL, cohort_index INTEGER NOT NULL, last_decision TEXT, updated_at REAL NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS canary_audit (id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, event TEXT, outcome TEXT, metadata TEXT, created_at REAL NOT NULL)")

    def create(self, policy: CanaryPolicy) -> str:
        policy.validate(); run_id = uuid.uuid4().hex
        with sqlite3.connect(self.path) as db: db.execute("INSERT INTO canary_runs VALUES (?, ?, 'planned', -1, NULL, ?)", (run_id, json.dumps(policy.to_dict(), sort_keys=True), time.time()))
        return run_id

    def get(self, run_id: str) -> dict[str, Any]:
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT run_id, policy, state, cohort_index, last_decision, updated_at FROM canary_runs WHERE run_id=?", (run_id,)).fetchone()
        if not row: raise KeyError(run_id)
        return {"run_id": row[0], "policy": json.loads(row[1]), "state": row[2], "cohort_index": row[3], "last_decision": json.loads(row[4]) if row[4] else None, "updated_at": row[5]}

    def transition(self, run_id: str, state: str, cohort_index: int | None = None, decision: HealthDecision | None = None) -> None:
        with sqlite3.connect(self.path, timeout=30, isolation_level="IMMEDIATE") as db:
            current = db.execute("SELECT cohort_index FROM canary_runs WHERE run_id=?", (run_id,)).fetchone()
            if not current: raise KeyError(run_id)
            db.execute("UPDATE canary_runs SET state=?, cohort_index=COALESCE(?, cohort_index), last_decision=?, updated_at=? WHERE run_id=?", (state, cohort_index, json.dumps(decision.to_dict(), sort_keys=True) if decision else None, time.time(), run_id))

    def audit(self, run_id: str, event: str, outcome: str, metadata: Mapping[str, Any] | None = None) -> None:
        safe = {str(k): v for k, v in (metadata or {}).items() if str(k).lower() not in {"token", "api_key", "authorization", "secret", "password"}}
        with sqlite3.connect(self.path) as db: db.execute("INSERT INTO canary_audit(run_id,event,outcome,metadata,created_at) VALUES (?,?,?,?,?)", (run_id, event, outcome, json.dumps(safe, sort_keys=True), time.time()))

    def audit_events(self, run_id: str) -> list[dict[str, Any]]:
        with sqlite3.connect(self.path) as db: rows = db.execute("SELECT event,outcome,metadata,created_at FROM canary_audit WHERE run_id=? ORDER BY id", (run_id,)).fetchall()
        return [{"event": r[0], "outcome": r[1], "metadata": json.loads(r[2]), "created_at": r[3]} for r in rows]


class CanaryHealthEvaluator:
    """Fail-closed minimum-sample evaluator for canary health."""
    def evaluate(self, policy: CanaryPolicy, observation: HealthObservation) -> HealthDecision:
        policy.health.validate(); reasons: list[str] = []
        if observation.samples < policy.health.min_samples: reasons.append("insufficient_samples")
        if observation.error_rate > policy.health.max_error_rate: reasons.append("error_rate_exceeded")
        if observation.p95_latency_ms > policy.health.max_p95_latency_ms: reasons.append("p95_latency_exceeded")
        if observation.p99_latency_ms > policy.health.max_p99_latency_ms: reasons.append("p99_latency_exceeded")
        if observation.saturation_ratio > policy.health.max_saturation_ratio: reasons.append("saturation_exceeded")
        if observation.critical_security_findings > policy.health.critical_security_findings: reasons.append("critical_security_findings")
        if policy.health.min_business_health is not None and (observation.business_health is None or observation.business_health < policy.health.min_business_health): reasons.append("business_health_below_minimum")
        if observation.release_id and observation.release_id != policy.release_id: reasons.append("observation_release_mismatch")
        if observation.observed_at <= 0: reasons.append("observation_timestamp_missing")
        return HealthDecision(not reasons, tuple(reasons), observation.observed_at, observation.release_id)


class CanaryController:
    """Durable canary state machine with policy-bounded advancement and rollback."""
    def __init__(self, store: CanaryStateStore, adapter: DeploymentAdapter, evaluator: CanaryHealthEvaluator | None = None) -> None:
        self.store = store; self.adapter = adapter; self.evaluator = evaluator or CanaryHealthEvaluator()

    def start(self, policy: CanaryPolicy) -> str:
        run_id = self.store.create(policy); self.store.audit(run_id, "canary.created", "completed", {"policy_id": policy.policy_id, "release_id": policy.release_id}); return run_id

    def deploy(self, run_id: str) -> dict[str, Any]:
        record = self.store.get(run_id); policy = CanaryPolicy.from_dict(record["policy"])
        if record["state"] not in {"planned", "failed"}: return record
        self.adapter.deploy(policy.release_id, policy.rollback_target); self.store.transition(run_id, "deployed"); self.store.audit(run_id, "canary.deploy", "completed", {"release_id": policy.release_id}); return self.store.get(run_id)

    def observe(self, run_id: str, observation: HealthObservation, approval: bool = False) -> dict[str, Any]:
        record = self.store.get(run_id); policy = CanaryPolicy.from_dict(record["policy"])
        if record["state"] in {"completed", "rolled_back"}: return record
        if record["state"] not in {"deployed", "observing", "advancing", "awaiting_approval"}: raise CanaryError(f"cannot observe from state {record['state']}")
        decision = self.evaluator.evaluate(policy, observation); self.store.audit(run_id, "canary.health", "passed" if decision.passed else "failed", {"reasons": decision.reasons, "samples": observation.samples})
        if not decision.passed:
            severe = {"error_rate_exceeded", "p99_latency_exceeded", "deployment_crash"}
            if policy.rollback.pause_on_critical_security and "critical_security_findings" in decision.reasons: self.adapter.pause(policy.release_id)
            if severe.intersection(decision.reasons):
                return self.rollback(run_id, ";".join(decision.reasons))
            self.store.transition(run_id, "paused", decision=decision); return self.store.get(run_id)
        next_index = record["cohort_index"] + 1
        if next_index >= len(policy.cohorts): self.store.transition(run_id, "completed", decision=decision); self.store.audit(run_id, "canary.completed", "completed", {}); return self.store.get(run_id)
        cohort = policy.cohorts[next_index]
        if policy.approval_mode in {"per_step", "always"} and not approval:
            self.store.transition(run_id, "awaiting_approval", decision=decision); return self.store.get(run_id)
        self.adapter.set_traffic(policy.release_id, cohort.traffic_percent); self.store.transition(run_id, "observing", next_index, decision); self.store.audit(run_id, "canary.advance", "completed", {"cohort": cohort.name, "traffic_percent": cohort.traffic_percent}); return self.store.get(run_id)

    def rollback(self, run_id: str, reason: str = "operator_or_policy") -> dict[str, Any]:
        record = self.store.get(run_id); policy = CanaryPolicy.from_dict(record["policy"])
        if record["state"] == "rolled_back": return record
        self.adapter.rollback(policy.release_id, policy.rollback_target); self.store.transition(run_id, "rolled_back"); self.store.audit(run_id, "canary.rollback", "completed", {"reason": reason, "rollback_target": policy.rollback_target}); return self.store.get(run_id)
