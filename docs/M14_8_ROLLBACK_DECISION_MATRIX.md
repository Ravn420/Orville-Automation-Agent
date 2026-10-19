# M14.8 Rollback Decision Matrix

**Milestone:** M14.8 — Non-production canary and rollback drill
**Component:** `orville_core.canary.CanaryController.rollback()`
**Status:** Local contract complete; live drill pending

## Purpose

This document defines the decision matrix for canary rollback operations. Rollback is the controlled restoration of traffic to a known-good release when health evaluation fails or operator intervention is required.

## Rollback Triggers

### Automatic Triggers (Health-Based)

| Trigger | Condition | Severity | Immediate Action |
|---------|-----------|----------|------------------|
| **Error Rate Exceeded** | `error_rate > max_error_rate` | SEVERE | Rollback |
| **p99 Latency Exceeded** | `p99_latency_ms > max_p99_latency_ms` | SEVERE | Rollback |
| **Candidate Crash** | Worker exit / deployment crash | SEVERE | Rollback |
| **Critical Security** | `critical_security_findings > 0` + `pause_on_critical_security=False` | SEVERE | Rollback |

### Pause-Then-Rollback Triggers

| Trigger | Condition | Initial Action | Secondary Action |
|---------|-----------|----------------|------------------|
| **Critical Security (Pause First)** | `critical_security_findings > 0` + `pause_on_critical_security=True` | Pause | Rollback after hold |

### Manual Triggers (Operator-Initiated)

| Trigger | Condition | Authorization Required |
|---------|-----------|------------------------|
| **Operator Rollback** | Manual decision by operator | Rollback authority approval |
| **Policy Override** | Emergency stop decision | Named rollback authority |
| **External Alert** | Monitoring/alerting system | Incident commander approval |

## Rollback Decision Matrix

### Health Decision → Controller Action

```
┌─────────────────────────────────────────────────────────────────┐
│                    Health Evaluation                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │    PASS     │  │    PAUSE    │  │        FAIL             │  │
│  │  (no reasons)│  │(non-severe) │  │    (severe reasons)     │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │
│         │                │                      │                │
│         ▼                ▼                      ▼                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Advance   │  │    Pause    │  │       Rollback          │  │
│  │  to next    │  │  promotion  │  │  to known-good target   │  │
│  │   cohort    │  │             │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Detailed Decision Flow

```
Health Observation Received
           │
           ▼
    ┌──────────────┐
    │ Valid obs?   │──No──▶ Pause (invalid_observation)
    └──────┬───────┘
           │ Yes
           ▼
    ┌──────────────┐
    │ Sufficient   │──No──▶ Pause (insufficient_samples)
    │   samples?   │
    └──────┬───────┘
           │ Yes
           ▼
    ┌──────────────┐
    │ Error rate   │──Yes──▶ Rollback (error_rate_exceeded)
    │   exceeded?  │
    └──────┬───────┘
           │ No
           ▼
    ┌──────────────┐
    │ p99 latency  │──Yes──▶ Rollback (p99_latency_exceeded)
    │   exceeded?  │
    └──────┬───────┘
           │ No
           ▼
    ┌──────────────┐
    │ p95 latency  │──Yes──▶ Pause (p95_latency_exceeded)
    │   exceeded?  │
    └──────┬───────┘
           │ No
           ▼
    ┌──────────────┐
    │ Saturation   │──Yes──▶ Pause (saturation_exceeded)
    │   exceeded?  │
    └──────┬───────┘
           │ No
           ▼
    ┌──────────────┐
    │ Security     │──Yes──▶ Pause/Rollback (critical_security_findings)
    │   findings?  │        │ (per pause_on_critical_security policy)
    └──────┬───────┘
           │ No
           ▼
    ┌──────────────┐
    │ Business     │──Yes──▶ Pause (business_health_below_minimum)
    │   health OK? │
    └──────┬───────┘
           │ Yes
           ▼
    ┌──────────────┐
    │ Release      │──No───▶ Pause (observation_release_mismatch)
    │   match?     │
    └──────┬───────┘
           │ Yes
           ▼
    ┌──────────────┐
    │ Advance to   │
    │   next cohort│
    │   or complete│
    └──────────────┘
```

## Rollback Limits

### RollbackLimits Configuration

```python
@dataclass(frozen=True)
class RollbackLimits:
    max_attempts: int = 3              # Maximum rollback attempts
    timeout_seconds: int = 300         # Timeout per attempt
    quarantine_seconds: int = 3600     # Quarantine duration for failed release
    require_known_good_target: bool = True  # Require explicit rollback target
    pause_on_critical_security: bool = True  # Pause before security rollback
```

### Attempt Bounding

| Attempt | Action | On Failure |
|---------|--------|------------|
| 1 | Execute rollback | Wait, retry if attempts remain |
| 2 | Retry rollback | Wait, retry if attempts remain |
| 3 | Final attempt | Mark as `failed` state, escalate |
| >3 | Not permitted | Blocked by policy |

### Timeout Handling

- Each attempt has `timeout_seconds` limit
- Timeout results in `rollback_timeout` audit event
- Controller state remains `paused` or `failed`
- No automatic retry without operator approval

## Rollback Procedure

### Step 1: Validate Preconditions

| Check | Validation | On Failure |
|-------|------------|------------|
| State | Not already `rolled_back` | Return current state |
| Target | `rollback_target` is non-empty | Raise `CanaryError` |
| Attempts | `attempt_count < max_attempts` | Set `failed` state |
| Approval | Rollback authority approved | Block, request approval |

### Step 2: Execute Rollback

```python
# Adapter call
adapter.rollback(release_id, rollback_target)

# State transition
store.transition(run_id, "rolled_back")

# Audit record
store.audit(run_id, "canary.rollback", "completed", {
    "reason": reason,
    "rollback_target": rollback_target,
    "attempt": attempt_count
})
```

### Step 3: Verify Recovery

| Verification | Method | Success Criteria |
|--------------|--------|------------------|
| **Health Check** | Authenticated endpoint | Returns 200 OK, healthy status |
| **State Check** | Read-only checkpoint | State matches expected known-good |
| **Smoke Test** | Representative workflow | Critical path executes successfully |

### Step 4: Handle Rollback Failure

| Failure Mode | Detection | Response |
|--------------|-----------|----------|
| **Adapter timeout** | `timeout_seconds` exceeded | Increment attempts, pause, alert |
| **Target unavailable** | Adapter raises exception | Mark `failed`, quarantine, escalate |
| **Quarantine failure** | Exception during quarantine | Mark `failed`, preserve diagnostics |
| **Verification failure** | Health/state/smoke fails | Keep `failed`, incident response |

## Rollback States

| State | Description | Exit Condition |
|-------|-------------|----------------|
| `rolling_back` | Rollback in progress | Success → `rolled_back`, Failure → `rollback_failed` |
| `rolled_back` | Rollback completed successfully | Terminal state |
| `rollback_failed` | Rollback failed, attempts exhausted | Manual intervention required |
| `quarantined` | Failed release quarantined | Operator review and clearance |

## Quarantine Procedures

### When to Quarantine

- Rollback completed (successful or failed)
- Critical security findings detected
- Candidate crash confirmed
- Manual operator decision

### Quarantine Actions

1. Mark release as `quarantined` in audit
2. Prevent further deployment of release_id
3. Preserve all diagnostics and logs
4. Notify security/operations team
5. Await operator review

### Quarantine Clearance

Requires:
- Security review completion
- Root cause analysis
- Fix verification
- Explicit operator approval

## Evidence Requirements

### Rollback Evidence Checklist

- [ ] Rollback trigger (health failure, operator, alert)
- [ ] Rollback target identifier
- [ ] Attempt count and timestamps
- [ ] Adapter mutation record
- [ ] Success/failure outcome
- [ ] Verification results (health, state, smoke)
- [ ] Quarantine status (if applicable)
- [ ] Escalation record (if failed)

### Audit Events

| Event | Outcome | Metadata |
|-------|---------|----------|
| `canary.rollback` | `started` | reason, target, attempt |
| `canary.rollback` | `completed` | target, duration |
| `canary.rollback` | `failed` | error, attempt, next_action |
| `canary.quarantine` | `completed` | release_id, reason |

## Rollback Failure Recovery

### Failed Rollback Decision Tree

```
Rollback Failed
       │
       ▼
┌──────────────┐
│ Attempts <   │──Yes──▶ Wait, Alert, Retry with approval
│   max?       │
└──────┬───────┘
       │ No
       ▼
┌──────────────┐
│ Quarantine   │──Yes──▶ Quarantine candidate, Escalate
│   possible?  │
└──────┬───────┘
       │ No
       ▼
┌──────────────┐
│ Set failed   │
│   state,     │
│   preserve   │
│   evidence,  │
│   escalate   │
└──────────────┘
```

### Escalation Path

1. **Immediate**: Notify rollback authority and environment owner
2. **Within 15 minutes**: Incident commander assigned
3. **Within 30 minutes**: Decision on manual recovery or extended incident
4. **Documentation**: All actions recorded in incident system

## Safety Boundaries

1. **No silent rollback**: All rollbacks logged and audited
2. **Bounded attempts**: Never exceed `max_attempts`
3. **Known-good required**: Rollback without target is rejected
4. **Verification mandatory**: Recovery must pass all checks
5. **Quarantine enforced**: Failed releases cannot redeploy automatically
6. **Approval gated**: Manual rollbacks require rollback authority

## Testing

### Synthetic Rollback Scenarios

| Scenario | ID | Expected Result |
|----------|-----|-----------------|
| Clean rollback | FI-03 | `rolled_back`, target restored |
| Rollback timeout | FI-14 | `paused`, attempts bounded |
| Missing target | FI-15 | `failed`, explicit error |
| Quarantine failure | FI-16 | `failed`, diagnostics preserved |

### Test Execution

```bash
# Run fault injection tests
python tools/m13_12_fault_runner.py

# Run rollback-specific tests
python -m pytest tests/test_rollback_recovery.py -v
```

## Related Documentation

- [`M14_8_NONPRODUCTION_CANARY_ROLLBACK_DRILL_RUNBOOK.md`](M14_8_NONPRODUCTION_CANARY_ROLLBACK_DRILL_RUNBOOK.md) — Live drill procedure
- [`M14_8_CANARY_CONTROLLER_OPERATION_GUIDE.md`](M14_8_CANARY_CONTROLLER_OPERATION_GUIDE.md) — Controller operations
- [`M14_8_HEALTH_EVALUATION_PROCEDURES.md`](M14_8_HEALTH_EVALUATION_PROCEDURES.md) — Health evaluation
- [`ROLLBACK_AND_RECOVERY_VERIFICATION.md`](ROLLBACK_AND_RECOVERY_VERIFICATION.md) — Recovery verification
