# M14.8 Local Contract — Non-Production Canary and Rollback Drill

**Milestone:** M14.8
**Status:** Local contract complete; approved non-production execution pending
**Date:** 2026-10-16

## Contract Scope

This document defines the complete local contract for M14.8 — the non-production canary and rollback drill milestone. It specifies the implemented components, their boundaries, and the remaining deployment-owned work required for full milestone acceptance.

## Local Implementation Status

### ✅ Completed Local Components

| Component | Location | Evidence | Status |
|-----------|----------|----------|--------|
| Canary Policy Schema | `orville_core/canary_policy.py` | `config/canary-policy.example.json` | ✅ Complete |
| Durable Controller | `orville_core/canary.py` | `CanaryController`, `CanaryStateStore` | ✅ Complete |
| Health Evaluator | `orville_core/canary.py` | `CanaryHealthEvaluator` | ✅ Complete |
| Synthetic Adapter | `orville_core/canary.py` | `SyntheticDeploymentAdapter` | ✅ Complete |
| Reviewed Provider Adapter | `orville_core/reviewed_deployment_provider.py` | `ReviewedDeploymentAdapter` | ✅ Complete |
| Fault Injection Runner | `tools/m13_12_fault_runner.py` | `artifacts/m13_12_fault_injection.json` | ✅ Complete |
| Rollback Recovery | `orville_core/recovery.py` | `tests/test_rollback_recovery.py` | ✅ Complete |
| Production Metrics | `orville_core/production_metrics.py` | `tests/test_production_metrics.py` | ✅ Complete |

### 📋 Completed Documentation

| Document | Purpose | Location |
|----------|---------|----------|
| Drill Runbook | Controlled procedure for live drill | `docs/M14_8_NONPRODUCTION_CANARY_ROLLBACK_DRILL_RUNBOOK.md` |
| Evidence Template | Per-run acceptance record | `artifacts/templates/M14_8_CANARY_ROLLBACK_ACCEPTANCE_EVIDENCE_TEMPLATE.md` |
| Controller Operation Guide | Operational interface and procedures | `docs/M14_8_CANARY_CONTROLLER_OPERATION_GUIDE.md` |
| Health Evaluation Procedures | Health observation evaluation | `docs/M14_8_HEALTH_EVALUATION_PROCEDURES.md` |
| Rollback Decision Matrix | Rollback triggers and procedures | `docs/M14_8_ROLLBACK_DECISION_MATRIX.md` |
| Evidence Collection Procedures | Evidence retention and verification | `docs/M14_8_EVIDENCE_COLLECTION_PROCEDURES.md` |
| Fault Injection Summary | 18-scenario baseline results | `artifacts/M14_8_FAULT_INJECTION_SUMMARY.md` |
| This Contract | Complete M14.8 local contract | `docs/M14_8_LOCAL_CONTRACT.md` |

## Implementation Boundaries

### What Is Local (Implemented)

1. **Policy Validation**
   - Versioned policy schema
   - Monotonic cohort validation
   - Threshold bounds checking
   - Rollback limit enforcement

2. **Controller State Machine**
   - SQLite-backed durable state
   - Transactional transitions
   - Restart recovery
   - Idempotent operations

3. **Health Evaluation**
   - Fail-closed threshold comparison
   - Minimum sample enforcement
   - Security finding handling
   - Freshness validation

4. **Synthetic Testing**
   - 18-scenario fault injection
   - Deterministic adapter
   - Automated verification
   - Evidence generation

5. **Adapter Contract**
   - Dry-run mode default
   - Bounded operations
   - Status redaction
   - Credential reference validation

### What Is Deployment-Owned (Pending)

1. **Live Provider Backend**
   - Provider-specific deployment API
   - Workload identity integration
   - Provider-side idempotency
   - Live traffic control

2. **Non-Production Environment**
   - Approved target environment
   - Isolation from production
   - Named environment owner
   - Change approval workflow

3. **Live Health Sources**
   - Production monitoring backend
   - Tenant/cohort-scoped metrics
   - Real-time alerting
   - Business health source

4. **Rollback Drill Execution**
   - Approved non-production drill
   - Independent verification
   - Evidence retention
   - Sign-off by all roles

## 18-Scenario Fault Injection Baseline

All scenarios pass with synthetic adapter:

| ID | Scenario | Expected | Actual | Status |
|----|----------|----------|--------|--------|
| FI-01 | Samples below minimum | Pause | paused | ✅ |
| FI-02 | Observation window incomplete | Pause | paused | ✅ |
| FI-03 | Error rate above threshold | Rollback | rolled_back | ✅ |
| FI-04 | p95 latency above threshold | Pause | paused | ✅ |
| FI-05 | p99 latency above threshold | Rollback | rolled_back | ✅ |
| FI-06 | Saturation above threshold | Pause | paused | ✅ |
| FI-07 | Business health below minimum | Pause | paused | ✅ |
| FI-08 | Critical security finding | Pause | paused | ✅ |
| FI-09 | Candidate crash/worker exit | Rollback | rolled_back | ✅ |
| FI-10 | Health provider unavailable | Pause | paused | ✅ |
| FI-11 | Release/cohort mismatch | Pause | paused | ✅ |
| FI-12 | Duplicate health event | No-op | completed | ✅ |
| FI-13 | Controller restart recovery | Resume | observing | ✅ |
| FI-14 | Rollback adapter timeout | Retry/Failed | deployed | ✅ |
| FI-15 | Rollback target unavailable | Fail closed | deployed | ✅ |
| FI-16 | Quarantine operation fails | Fail closed | deployed | ✅ |
| FI-17 | Malformed policy | Reject | deployed | ✅ |
| FI-18 | Secret-bearing metadata | Redacted | deployed | ✅ |

**Pass Rate:** 18/18 (100%)

**Evidence:** `artifacts/m13_12_fault_injection.json`

## Test Coverage

### Unit Tests

```
tests/test_canary.py::CanaryTests::test_controller_is_durable_approval_gated_and_idempotent PASSED
tests/test_canary.py::CanaryTests::test_health_evaluator_fails_closed_for_sparse_or_security_bad_data PASSED
tests/test_canary.py::CanaryTests::test_mismatched_release_is_rejected_and_critical_security_pauses PASSED

tests/test_rollback_recovery.py::test_rollback_plan_requires_explicit_target_and_approval PASSED
tests/test_rollback_recovery.py::test_recovery_verification_requires_matching_backup_and_all_checks PASSED
tests/test_rollback_recovery.py::test_failed_recovery_evidence_is_not_success PASSED
tests/test_rollback_recovery.py::test_missing_backup_fails_closed_without_restoration PASSED

tests/test_reviewed_deployment_provider.py::test_dry_run_never_calls_backend_and_is_idempotent PASSED
tests/test_reviewed_deployment_provider.py::test_live_backend_operations_are_bounded_and_idempotent PASSED
tests/test_reviewed_deployment_provider.py::test_rejects_raw_credential_like_reference_and_invalid_traffic PASSED
tests/test_reviewed_deployment_provider.py::test_timeout_fails_closed PASSED
tests/test_reviewed_deployment_provider.py::test_status_is_redacted PASSED

tests/test_production_metrics.py - 12 tests PASSED
```

**Total:** 26+ tests passed

## Live Drill Requirements

For M14.8 completion, the following must be executed in an approved non-production environment:

### Required Scenarios

1. **Clean Bounded Progression**
   - Preflight/dry-run success
   - Cohort deployment and health observation
   - Decision recording and adapter mutation

2. **Restart Recovery**
   - Controller restart during observation hold
   - State restoration verification
   - Decision cursor preservation

3. **Duplicate Event Handling**
   - Replay of health event
   - Idempotency verification
   - No duplicate mutations

4. **Rollback Success**
   - Triggered rollback from bounded cohort
   - Known-good target restoration
   - Health/state/smoke verification

5. **Rollback Failure Recovery**
   - Injected rollback fault
   - Bounded retry handling
   - Escalation and explicit failed state

### Required Roles

| Role | Responsibility |
|------|----------------|
| Change Owner | Opens approved change, confirms scope |
| Automation Operator | Executes adapter actions, records commands |
| Verification Reviewer | Independently checks state and evidence |
| Rollback Authority | Authorizes traffic changes and rollback |
| Security Reviewer | Confirms environment boundary and redaction |

### Required Evidence

- Entry gates verification (10 gates)
- Synthetic baseline results (18 scenarios)
- Live drill evidence (5 scenario categories)
- Evidence retention checklist (6 classes)
- Redaction verification (6 checks)
- Signatures (5 roles)
- Completion statement

## Safety Boundaries

1. **Non-Production Only**: No production credentials, traffic, or data
2. **Approval Required**: Every traffic mutation requires rollback authority approval
3. **Known-Good Target**: Rollback requires explicit, verified rollback target
4. **Bounded Operations**: Timeouts, retry limits, and idempotency enforced
5. **Secret-Free Evidence**: No credentials, tokens, or keys in retained evidence
6. **Independent Review**: No self-approval of traffic mutations and acceptance

## Completion Criteria

M14.8 is complete when:

- [x] Local implementation passes all synthetic tests
- [x] 18-scenario fault injection baseline passes
- [x] Documentation is complete and consistent
- [ ] Live drill executed in approved non-production environment
- [ ] All 5 scenario categories demonstrate expected behavior
- [ ] Evidence collected and independently reviewed
- [ ] Redaction verified (no secrets in repository)
- [ ] All required signatures obtained
- [ ] TODO.md, STATE.md, and TASK_GRAPH.md updated

## Dependencies

### Required for M14.8

- M14.2 — Enterprise environment ownership
- M14.3 — Live Windows/Linux sandbox validation
- M14.4 — Enterprise identity and authorization
- M14.5 — Protected secret management
- M14.6 — Reviewed deployment-provider adapter
- M14.7 — Production metrics and health sources

### M14.8 Enables

- M14.9 — Backup, restore, and disaster recovery
- M14.10 — Production readiness and load gates
- M14.11 — Controlled production canary

## References

| Document | Description |
|----------|-------------|
| [`M14_8_NONPRODUCTION_CANARY_ROLLBACK_DRILL_RUNBOOK.md`](M14_8_NONPRODUCTION_CANARY_ROLLBACK_DRILL_RUNBOOK.md) | Live drill procedure |
| [`M14_8_CANARY_CONTROLLER_OPERATION_GUIDE.md`](M14_8_CANARY_CONTROLLER_OPERATION_GUIDE.md) | Controller operations |
| [`M14_8_HEALTH_EVALUATION_PROCEDURES.md`](M14_8_HEALTH_EVALUATION_PROCEDURES.md) | Health evaluation |
| [`M14_8_ROLLBACK_DECISION_MATRIX.md`](M14_8_ROLLBACK_DECISION_MATRIX.md) | Rollback decisions |
| [`M14_8_EVIDENCE_COLLECTION_PROCEDURES.md`](M14_8_EVIDENCE_COLLECTION_PROCEDURES.md) | Evidence procedures |
| [`artifacts/templates/M14_8_CANARY_ROLLBACK_ACCEPTANCE_EVIDENCE_TEMPLATE.md`](../artifacts/templates/M14_8_CANARY_ROLLBACK_ACCEPTANCE_EVIDENCE_TEMPLATE.md) | Evidence template |
| [`artifacts/M14_8_FAULT_INJECTION_SUMMARY.md`](../artifacts/M14_8_FAULT_INJECTION_SUMMARY.md) | Baseline results |
| [`M13_12_FAULT_INJECTION_AND_DEPLOYMENT_READINESS.md`](M13_12_FAULT_INJECTION_AND_DEPLOYMENT_READINESS.md) | Fault matrix |
| [`ROLLBACK_AND_RECOVERY_VERIFICATION.md`](ROLLBACK_AND_RECOVERY_VERIFICATION.md) | Recovery procedures |
| [`M14_REVIEWED_DEPLOYMENT_PROVIDER.md`](M14_REVIEWED_DEPLOYMENT_PROVIDER.md) | Adapter contract |
| [`M14_PRODUCTION_METRICS.md`](M14_PRODUCTION_METRICS.md) | Metric sourcing |

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Local Contract Author | | | |
| Implementation Reviewer | | | |
| Documentation Reviewer | | | |

---

**Note:** This local contract documents the implemented components and their boundaries. Full M14.8 milestone acceptance requires execution of the live drill procedure in an approved non-production environment with independently reviewed evidence.
