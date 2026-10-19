# M14.8 Health Evaluation Procedures

**Milestone:** M14.8 — Non-production canary and rollback drill
**Component:** `orville_core.canary.CanaryHealthEvaluator`
**Status:** Local contract complete; live drill pending

## Purpose

This document defines the procedures for evaluating canary health observations against policy thresholds. The health evaluator is fail-closed: any missing, stale, or out-of-bounds observation results in a negative decision that pauses or rolls back promotion.

## Health Observation Schema

```python
@dataclass(frozen=True)
class HealthObservation:
    samples: int                          # Number of observations in window
    error_rate: float                     # 0.0 to 1.0
    p95_latency_ms: float                 # 95th percentile latency
    p99_latency_ms: float                 # 99th percentile latency
    saturation_ratio: float               # 0.0 to 1.0 (resource utilization)
    critical_security_findings: int = 0   # Count of critical security issues
    business_health: float | None = None  # 0.0 to 1.0 (optional business metric)
    observed_at: float = 0.0              # Unix timestamp
    release_id: str = ""                  # Must match policy release_id
```

## Health Thresholds Schema

```python
@dataclass(frozen=True)
class HealthThresholds:
    min_samples: int = 100                # Minimum observations required
    max_error_rate: float = 0.02          # Maximum acceptable error rate (2%)
    max_p95_latency_ms: float = 1000.0    # Maximum p95 latency in milliseconds
    max_p99_latency_ms: float = 2000.0    # Maximum p99 latency in milliseconds
    max_saturation_ratio: float = 0.90    # Maximum resource saturation (90%)
    critical_security_findings: int = 0   # Maximum acceptable security findings
    min_business_health: float | None = 0.95  # Minimum business health score
    confidence_level: float = 0.95        # Statistical confidence (for reporting)
```

## Evaluation Procedure

### Step 1: Validate Observation Completeness

**Check:** All required fields present and valid

| Field | Validation | Failure Action |
|-------|------------|----------------|
| `samples` | `samples >= 1` | Reject with `insufficient_samples` |
| `error_rate` | `0.0 <= error_rate <= 1.0` | Reject with `invalid_observation` |
| `p95_latency_ms` | `p95_latency_ms > 0` | Reject with `invalid_observation` |
| `p99_latency_ms` | `p99_latency_ms >= p95_latency_ms` | Reject with `invalid_observation` |
| `saturation_ratio` | `0.0 <= saturation_ratio <= 1.0` | Reject with `invalid_observation` |
| `observed_at` | `observed_at > 0` | Reject with `observation_timestamp_missing` |
| `release_id` | Non-empty string | Reject with `observation_release_mismatch` |

### Step 2: Validate Sample Count

**Check:** `observation.samples >= policy.health.min_samples`

```python
if observation.samples < policy.health.min_samples:
    reasons.append("insufficient_samples")
    # Decision: FAILED (pause)
```

**Evidence required:**
- Actual sample count
- Required minimum from policy
- Observation timestamp

### Step 3: Validate Error Rate

**Check:** `observation.error_rate <= policy.health.max_error_rate`

```python
if observation.error_rate > policy.health.max_error_rate:
    reasons.append("error_rate_exceeded")
    # Decision: FAILED (rollback - SEVERE)
```

**Severity:** SEVERE → triggers rollback

**Evidence required:**
- Observed error rate (percentage)
- Threshold from policy
- Time window of observation

### Step 4: Validate Latency Percentiles

**Check p95:** `observation.p95_latency_ms <= policy.health.max_p95_latency_ms`

```python
if observation.p95_latency_ms > policy.health.max_p95_latency_ms:
    reasons.append("p95_latency_exceeded")
    # Decision: FAILED (pause)
```

**Check p99:** `observation.p99_latency_ms <= policy.health.max_p99_latency_ms`

```python
if observation.p99_latency_ms > policy.health.max_p99_latency_ms:
    reasons.append("p99_latency_exceeded")
    # Decision: FAILED (rollback - SEVERE)
```

**Severity:** p99 exceeds threshold → SEVERE → triggers rollback

**Evidence required:**
- Observed p95/p99 values (ms)
- Thresholds from policy
- Sample distribution (if available)

### Step 5: Validate Saturation

**Check:** `observation.saturation_ratio <= policy.health.max_saturation_ratio`

```python
if observation.saturation_ratio > policy.health.max_saturation_ratio:
    reasons.append("saturation_exceeded")
    # Decision: FAILED (pause)
```

**Evidence required:**
- Observed saturation ratio
- Threshold from policy
- Resource type (CPU, memory, etc.)

### Step 6: Validate Security Findings

**Check:** `observation.critical_security_findings <= policy.health.critical_security_findings`

```python
if observation.critical_security_findings > policy.health.critical_security_findings:
    reasons.append("critical_security_findings")
    # Decision: FAILED (pause, then rollback if configured)
```

**Behavior:**
- If `policy.rollback.pause_on_critical_security=True`: Pause first, then rollback
- If `policy.rollback.pause_on_critical_security=False`: Rollback immediately

**Evidence required:**
- Count of critical findings
- Finding types (redacted)
- Security scan timestamp

### Step 7: Validate Business Health

**Check:** `observation.business_health >= policy.health.min_business_health`

```python
if policy.health.min_business_health is not None:
    if observation.business_health is None:
        reasons.append("business_health_missing")
    elif observation.business_health < policy.health.min_business_health:
        reasons.append("business_health_below_minimum")
    # Decision: FAILED (pause)
```

**Evidence required:**
- Observed business health score
- Minimum threshold from policy
- Business metric definition

### Step 8: Validate Release Identity

**Check:** `observation.release_id == policy.release_id`

```python
if observation.release_id and observation.release_id != policy.release_id:
    reasons.append("observation_release_mismatch")
    # Decision: FAILED (pause)
```

**Evidence required:**
- Observed release_id
- Expected release_id from policy
- Cohort assignment

### Step 9: Generate Decision

```python
@dataclass(frozen=True)
class HealthDecision:
    passed: bool                          # True if no reasons
    reasons: tuple[str, ...]             # List of failure reasons
    observed_at: float                   # Timestamp of observation
    release_id: str                      # Release being evaluated
```

**Decision rules:**
- `passed = True` if `reasons` is empty
- `passed = False` if any reason exists

## Decision-to-Action Mapping

| Decision | Reasons Present | Controller Action |
|----------|-----------------|-------------------|
| **PASS** | None | Advance to next cohort or complete |
| **PAUSE** | Non-severe only | Pause promotion, retain current cohort |
| **ROLLBACK** | Any severe reason | Rollback to known-good target |

### Severe vs Non-Severe Reasons

| Reason | Severity | Action |
|--------|----------|--------|
| `insufficient_samples` | Non-severe | Pause |
| `error_rate_exceeded` | **SEVERE** | Rollback |
| `p95_latency_exceeded` | Non-severe | Pause |
| `p99_latency_exceeded` | **SEVERE** | Rollback |
| `saturation_exceeded` | Non-severe | Pause |
| `critical_security_findings` | Configurable | Pause → Rollback |
| `business_health_below_minimum` | Non-severe | Pause |
| `observation_release_mismatch` | Non-severe | Pause |
| `observation_timestamp_missing` | Non-severe | Pause |

## Freshness Requirements

### Observation Window

- Observations must be within `policy.observation_window_seconds` of current time
- Stale observations are rejected with `observation_stale` reason
- Freshness is verified before threshold evaluation

### Minimum Sample Window

- Each cohort defines `min_samples` and `hold_seconds`
- Both must be satisfied before advancement
- Partial windows result in `observation_window_incomplete`

## Evidence Collection Checklist

For each health evaluation, collect:

- [ ] Observation timestamp (`observed_at`)
- [ ] Sample count (`samples`)
- [ ] All metric values (error_rate, latency, saturation, etc.)
- [ ] Release identity (`release_id`)
- [ ] Policy thresholds applied
- [ ] Decision result (`passed`/`failed`)
- [ ] Decision reasons (if failed)
- [ ] Evaluator version/identifier
- [ ] Cohort context (name, traffic_percent)

## Health Source Requirements

### Metric Scoping

All health observations must be scoped to:
- **Tenant**: The specific tenant being evaluated
- **Cohort**: The current traffic cohort
- **Release**: The specific release_id being canaried

### Cross-Scope Rejection

Observations that include data from:
- Other tenants
- Other releases
- Mixed cohorts

Must be rejected with `observation_scope_mismatch`.

### Health Source Availability

| Scenario | Behavior |
|----------|----------|
| Health source available | Normal evaluation |
| Health source unavailable | Pause with `health_source_unavailable` |
| Health source timeout | Pause with `health_source_timeout` |
| Partial data | Reject with `insufficient_samples` |

## Synthetic Test Scenarios

### FI-01: Samples Below Minimum
```python
observation = HealthObservation(samples=1, ...)  # min_samples=10
# Expected: paused, reason="insufficient_samples"
```

### FI-03: Error Rate Above Threshold
```python
observation = HealthObservation(error_rate=0.9, ...)  # max_error_rate=0.05
# Expected: rolled_back, reason="error_rate_exceeded"
```

### FI-04: p95 Latency Above Threshold
```python
observation = HealthObservation(p95_latency_ms=101, ...)  # max_p95=100
# Expected: paused, reason="p95_latency_exceeded"
```

### FI-05: p99 Latency Above Threshold
```python
observation = HealthObservation(p99_latency_ms=201, ...)  # max_p99=200
# Expected: rolled_back, reason="p99_latency_exceeded"
```

### FI-08: Critical Security Finding
```python
observation = HealthObservation(critical_security_findings=1, ...)  # max=0
# Expected: paused, reason="critical_security_findings"
```

## Operational Checklist

Before accepting a health decision:

- [ ] Observation is fresh (within window)
- [ ] Sample count meets minimum
- [ ] Metrics are within thresholds
- [ ] No critical security findings (or handled per policy)
- [ ] Release identity matches
- [ ] Observation is properly scoped
- [ ] Health source is available
- [ ] Decision is recorded in audit log

## Related Documentation

- [`M14_8_CANARY_CONTROLLER_OPERATION_GUIDE.md`](M14_8_CANARY_CONTROLLER_OPERATION_GUIDE.md) — Controller operations
- [`M14_8_ROLLBACK_DECISION_MATRIX.md`](M14_8_ROLLBACK_DECISION_MATRIX.md) — Rollback procedures
- [`M13_12_FAULT_INJECTION_AND_DEPLOYMENT_READINESS.md`](M13_12_FAULT_INJECTION_AND_DEPLOYMENT_READINESS.md) — Fault matrix
- [`M14_PRODUCTION_METRICS.md`](M14_PRODUCTION_METRICS.md) — Metric sourcing
