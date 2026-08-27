# M13.10 Canary Controller and Health-Evaluator Architecture

**Status:** Design draft; local policy contract available, deployment mutations not implemented.
**Scope:** Deterministic, restart-safe canary advancement, pause, rollback, and quarantine.

## Components

| Component | Responsibility | Invariant |
|---|---|---|
| Policy loader | Parse and validate `CanaryPolicy` before deployment | Invalid, unbounded, non-monotonic, or rollback-less policies never enter execution. |
| Durable controller | Persist state, cohort index, release, rollback target, attempts, and event cursor | Every transition is atomic, idempotent, and recoverable after restart. |
| Deployment adapter | Deploy, split traffic, pause, restore traffic, quarantine, and report status | Mutations are dry-run capable, approval-gated, and never contain secrets in state. |
| Health evaluator | Evaluate a fresh metric window against policy thresholds | Insufficient samples never pass; critical security findings always fail. |
| Rollback manager | Execute bounded rollback to the known-good target | Missing target, timeout, or exhausted attempts yields a blocked failure, never success. |
| Audit emitter | Record decisions and mutations | Every event contains release, cohort, actor/policy, timestamp, reason, and outcome. |

## Durable state machine

```text
planned -> deploying -> observing -> advancing -> observing
                         |             |
                         v             v
                       paused      rolled_back -> failed|completed
                         |
                         v
                    rolled_back
```

The controller stores `state_version`, `release_id`, `rollback_target`, `cohort_index`, `traffic_percent`, `observation_started_at`, `last_health_decision_id`, `rollback_attempts`, `quarantined`, and an idempotency key for the latest mutation. A restart reloads the last committed state and resumes from the same cohort without repeating a completed mutation.

## Health decision contract

A health window is evaluated only after both the cohort hold period and the minimum sample requirement are satisfied. The evaluator returns `pass`, `pause`, or `rollback`, plus a stable reason list and the metric window used.

Rollback or pause is triggered when any of the following is true:

- sample count is below the effective minimum;
- error rate exceeds `max_error_rate`;
- p95 or p99 latency exceeds its configured limit;
- saturation exceeds `max_saturation_ratio`;
- business health falls below `min_business_health` when configured;
- critical security findings exceed the configured maximum;
- the deployment, worker, or health provider reports a crash or unavailable status;
- the health result is stale or does not correspond to the current release and cohort.

A critical security finding should immediately pause traffic and initiate rollback when policy permits. A sparse or unavailable metric window must never be treated as healthy.

## Transition algorithm

1. Validate the policy and verify a known-good rollback target.
2. Deploy the candidate without changing production traffic.
3. Move to the first cohort and persist the mutation result.
4. Observe until both the hold period and minimum samples are satisfied.
5. Request one fresh health decision bound to release, cohort, and metric window.
6. On pass, advance only to the next larger cohort and persist the new idempotency key.
7. On pause, stop advancement and require the configured approval or operator decision.
8. On rollback, reset traffic, restore the known-good release, quarantine the candidate, and write an incident event.
9. If rollback fails, retry only up to `max_attempts`; then enter `failed` and expose an actionable blocked state.
10. Mark completed only after the final 100% cohort passes its own health window.

## Required tests

The implementation must test successful progression, duplicate events, restart recovery, stale health decisions, insufficient samples, error-rate breach, latency breach, saturation breach, business-health breach, critical security findings, deployment crash, rollback timeout, rollback retry exhaustion, unavailable rollback target, and idempotent quarantine. Every test must assert durable state and audit output, not only the return value.

## Relationship to M13.8

`orville_core/canary_policy.py` supplies the validated policy and threshold inputs. M13.10 should consume the policy without reimplementing its validation. M13.11 should own metric-window evaluation, while M13.12 should own rollback and quarantine mutations.
