# M14.8 Canary Controller Operation Guide

**Milestone:** M14.8 — Non-production canary and rollback drill
**Component:** `orville_core.canary`
**Status:** Local contract complete; live drill pending

## Overview

The canary controller provides a durable, restart-safe, idempotent state machine for controlled release promotion. It operates on a versioned policy, evaluates health observations against thresholds, advances traffic through monotonic cohorts, and fails closed on unsafe conditions.

This guide documents the controller's operational interface, state transitions, and procedures for operators and verification reviewers.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  CanaryPolicy   │────▶│ CanaryController │────▶│ DeploymentAdapter│
│  (validation)   │     │  (state machine) │     │  (provider ops)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
           │                       │
           ▼                       ▼
┌─────────────────┐     ┌──────────────────┐
│HealthThresholds │     │  CanaryStateStore│
│  (evaluation)   │     │ (SQLite durable) │
└─────────────────┘     └──────────────────┘
```

## Core Components

### 1. CanaryPolicy (`orville_core.canary_policy`)

Immutable, versioned policy defining:
- **Cohorts**: Monotonic traffic steps (e.g., 1% → 10% → 100%)
- **Health thresholds**: Minimum samples, error rate, latency bounds, saturation, security findings
- **Rollback limits**: Max attempts, timeout, quarantine period
- **Approval mode**: `none`, `initial`, `per_step`, `always`

**Validation rules:**
- Cohort percentages must increase monotonically
- Final cohort must reach 100%
- All holds bounded by `max_hold_seconds`
- Fresh health decisions are mandatory
- Known-good rollback target is required

### 2. CanaryStateStore (`orville_core.canary.CanaryStateStore`)

SQLite-backed durable storage with:
- **canary_runs**: Run ID, policy JSON, state, cohort index, last decision, timestamp
- **canary_audit**: Event log with automatic secret redaction

**Idempotency guarantees:**
- Transactional state transitions
- Duplicate event detection via idempotency context
- Restart recovery preserves run ID, cohort, and decision cursor

### 3. CanaryHealthEvaluator (`orville_core.canary.CanaryHealthEvaluator`)

Fail-closed evaluator that rejects observations with:
- Insufficient samples (`samples < min_samples`)
- Error rate above threshold
- Latency (p95/p99) above threshold
- Saturation above threshold
- Critical security findings
- Business health below minimum
- Release/cohort mismatch
- Missing timestamp

### 4. CanaryController (`orville_core.canary.CanaryController`)

State machine with states:

| State | Description | Transitions |
|-------|-------------|-------------|
| `planned` | Run created, not yet deployed | `deploy()` → `deployed` |
| `deployed` | Candidate deployed, no traffic | `observe()` → `observing`/`paused`/`rolled_back` |
| `observing` | Health observation in progress | `observe()` → `advancing`/`paused`/`rolled_back` |
| `advancing` | Traffic increase approved | Automatic → `observing`/`awaiting_approval` |
| `awaiting_approval` | Per-step approval required | `observe(approval=True)` → `observing` |
| `paused` | Health check failed, non-severe | Manual intervention or rollback |
| `rolled_back` | Rollback completed | Terminal state |
| `completed` | All cohorts passed | Terminal state |
| `failed` | Unrecoverable error | Terminal state |

## Operational Procedures

### Procedure 1: Initialize a Canary Run

```python
from orville_core.canary_policy import CanaryPolicy, CanaryCohort, HealthThresholds, RollbackLimits
from orville_core.canary import CanaryController, CanaryStateStore, SyntheticDeploymentAdapter

# 1. Define policy
policy = CanaryPolicy(
    policy_id="my-release-v1.2.3",
    release_id="v1.2.3-candidate",
    rollback_target="v1.2.2-known-good",
    cohorts=(
        CanaryCohort("internal", 1, hold_seconds=300, min_samples=100),
        CanaryCohort("canary", 10, hold_seconds=600, min_samples=1000),
        CanaryCohort("full", 100, hold_seconds=300, min_samples=5000),
    ),
    health=HealthThresholds(
        min_samples=100,
        max_error_rate=0.02,
        max_p95_latency_ms=1000.0,
        max_p99_latency_ms=2000.0,
        max_saturation_ratio=0.90,
        critical_security_findings=0,
        min_business_health=0.95,
    ),
    rollback=RollbackLimits(
        max_attempts=3,
        timeout_seconds=300,
        quarantine_seconds=3600,
        require_known_good_target=True,
        pause_on_critical_security=True,
    ),
    approval_mode="per_step",
)

# 2. Initialize controller
store = CanaryStateStore("/path/to/canary.db")
adapter = SyntheticDeploymentAdapter()  # Or reviewed provider adapter
controller = CanaryController(store, adapter)

# 3. Create run
run_id = controller.start(policy)
print(f"Run created: {run_id}")
```

**Verification:**
- Policy validates without errors
- Run ID is a valid UUID hex string
- Initial state is `planned`
- Audit event `canary.created` recorded

### Procedure 2: Deploy Candidate

```python
# Deploy the candidate release
state = controller.deploy(run_id)
assert state["state"] == "deployed"
```

**Verification:**
- Adapter `deploy()` called with release_id and rollback_target
- State transitions to `deployed`
- Audit event `canary.deploy` recorded

### Procedure 3: Submit Health Observation

```python
from orville_core.canary import HealthObservation
import time

observation = HealthObservation(
    samples=150,
    error_rate=0.01,
    p95_latency_ms=800.0,
    p99_latency_ms=1500.0,
    saturation_ratio=0.75,
    critical_security_findings=0,
    business_health=0.98,
    observed_at=time.time(),
    release_id="v1.2.3-candidate",
)

state = controller.observe(run_id, observation, approval=False)
print(f"State: {state['state']}, Cohort: {state['cohort_index']}")
```

**Decision outcomes:**
- `passed` → Advances to next cohort or `completed`
- `failed` (non-severe) → `paused` state
- `failed` (severe: error_rate, p99_latency, crash) → `rolled_back`

**Verification:**
- Health decision recorded in `last_decision`
- Audit event `canary.health` recorded with reasons
- Traffic percentage matches cohort if advanced

### Procedure 4: Handle Approval-Gated Advancement

```python
# When approval_mode is "per_step" or "always"
state = controller.observe(run_id, observation, approval=False)
if state["state"] == "awaiting_approval":
    # Operator reviews evidence and approves
    state = controller.observe(run_id, observation, approval=True)
```

**Verification:**
- State `awaiting_approval` when approval required
- Advancement only occurs with `approval=True`
- Audit event `canary.advance` records cohort and traffic percent

### Procedure 5: Execute Rollback

```python
# Manual rollback trigger
state = controller.rollback(run_id, reason="operator_initiated")
assert state["state"] == "rolled_back"
```

**Automatic rollback triggers:**
- Error rate above threshold
- p99 latency above threshold
- Candidate crash/worker exit

**Verification:**
- Adapter `rollback()` called with rollback_target
- Traffic reset to known-good target
- State `rolled_back`
- Audit event `canary.rollback` recorded with reason

### Procedure 6: Restart Recovery

```python
# Controller restart - state automatically recovered
new_controller = CanaryController(
    CanaryStateStore("/path/to/canary.db"),
    adapter
)

# Resume from stored state
state = new_controller.store.get(run_id)
assert state["state"] in {"observing", "paused", "awaiting_approval"}
```

**Verification:**
- Same run_id, cohort_index, and decision cursor
- No duplicate traffic mutations
- Audit sequence continues from last event

## Health Evaluation Reference

### Threshold Comparison Matrix

| Metric | Operator | Default | Pause Trigger | Rollback Trigger |
|--------|----------|---------|---------------|------------------|
| Samples | `<` | 100 | `samples < min_samples` | — |
| Error rate | `>` | 0.02 (2%) | — | `error_rate > max_error_rate` |
| p95 latency | `>` | 1000ms | `p95 > max_p95` | — |
| p99 latency | `>` | 2000ms | — | `p99 > max_p99` |
| Saturation | `>` | 0.90 (90%) | `saturation > max_saturation` | — |
| Security findings | `>` | 0 | Pause (configurable) | If `pause_on_critical_security=False` |
| Business health | `<` | 0.95 | `business_health < min_business_health` | — |

### Decision Reason Codes

| Code | Description | Action |
|------|-------------|--------|
| `insufficient_samples` | Observation below minimum sample count | Pause |
| `error_rate_exceeded` | Error rate above threshold | Rollback |
| `p95_latency_exceeded` | p95 latency above threshold | Pause |
| `p99_latency_exceeded` | p99 latency above threshold | Rollback |
| `saturation_exceeded` | Saturation above threshold | Pause |
| `critical_security_findings` | Security findings detected | Pause/Rollback |
| `business_health_below_minimum` | Business health below threshold | Pause |
| `observation_release_mismatch` | Release ID doesn't match policy | Pause |
| `observation_timestamp_missing` | Missing observation timestamp | Pause |

## Audit and Evidence

### Audit Event Schema

```json
{
  "event": "canary.health",
  "outcome": "passed|failed",
  "metadata": {
    "reasons": ["insufficient_samples"],
    "samples": 50
  },
  "created_at": 1699999999.0
}
```

### Secret Redaction

The following keys are automatically redacted from audit metadata:
- `token`
- `api_key`
- `authorization`
- `secret`
- `password`

### Evidence Collection

For each canary run, retain:
1. Run ID and policy JSON
2. State transition timeline
3. Health decisions with observations
4. Adapter mutation records
5. Audit event log (redacted)

## Safety Boundaries

1. **No automatic production deployment**: Controller requires explicit adapter calls
2. **Fresh health mandatory**: Stale observations rejected
3. **Monotonic cohorts only**: No traffic reduction without rollback
4. **Bounded rollback**: Max attempts and timeout enforced
5. **Known-good target required**: Rollback without target is rejected
6. **Secret-free audit**: Credentials never persisted in state or audit

## Testing

### Run Synthetic Fault Injection

```bash
python tools/m13_12_fault_runner.py --output artifacts/m13_12_fault_injection.json
```

### Run Unit Tests

```bash
python -m pytest tests/test_canary.py -v
python -m pytest tests/test_rollback_recovery.py -v
```

## Related Documentation

- [`M14_8_NONPRODUCTION_CANARY_ROLLBACK_DRILL_RUNBOOK.md`](M14_8_NONPRODUCTION_CANARY_ROLLBACK_DRILL_RUNBOOK.md) — Live drill procedure
- [`M13_12_FAULT_INJECTION_AND_DEPLOYMENT_READINESS.md`](M13_12_FAULT_INJECTION_AND_DEPLOYMENT_READINESS.md) — Fault matrix
- [`ROLLBACK_AND_RECOVERY_VERIFICATION.md`](ROLLBACK_AND_RECOVERY_VERIFICATION.md) — Rollback procedures
- [`M14_REVIEWED_DEPLOYMENT_PROVIDER.md`](M14_REVIEWED_DEPLOYMENT_PROVIDER.md) — Adapter contract
