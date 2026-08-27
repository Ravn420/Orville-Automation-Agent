# Health Monitoring, Structured Logs, and Operational Runbooks

## Scope and decision

Orville uses bounded, structured operational events and health summaries as the shared interface between runtime components and operators. The local reference sources are `orville_core.production_metrics`, `orville_core.usage_health`, `orville_core.readiness`, and the secret-safe audit primitives. This contract is standalone-capable and does not require a hosted monitoring vendor.

## Health model

Health is evaluated by component and projected into stable states: `healthy`, `degraded`, `blocked`, `offline`, and `unknown`. A health observation contains a component identifier, tenant/cohort/release scope where applicable, observation time in UTC, freshness, status, error rate, latency, saturation, dependency state, and a safe reason code. It never contains prompts, credentials, bearer tokens, raw provider responses, or high-cardinality payloads.

| Signal | Purpose | Initial operator threshold |
|---|---|---|
| Availability | Detect unreachable local API, model runtime, storage, or connector | Any required dependency unavailable for two consecutive observations. |
| Error rate | Detect failed workflow or provider operations | Alert when the configured rolling threshold is exceeded for two windows. |
| Latency | Detect slow request, task, or provider behavior | Alert on sustained breach of the configured percentile target. |
| Saturation | Detect worker, queue, storage, or rate-limit pressure | Alert before bounded capacity is exhausted. |
| Freshness | Detect stale metrics or heartbeat | Mark `unknown` when the freshness window expires. |
| Security findings | Surface secret, policy, or integrity failures | Treat high-severity findings as blocking until reviewed. |
| Release quality | Correlate validation and canary outcomes | Block promotion when required gates fail. |

Threshold values are configuration, not code constants. Alerts must identify component, scope, status, reason code, first-seen time, last-seen time, and suggested runbook; they must not include raw exception text or secret-bearing context.

## Structured operational event schema

Each event is a single JSON object written to the configured sanitized log sink or append-only audit store. Required fields are `event_id`, `event_type`, `event_version`, `occurred_at`, `severity`, `component`, `status`, `correlation_id`, `scope`, and `reason_code`. Optional fields include bounded `duration_ms`, `attempt`, `safe_reference`, `affected_path_count`, `validation_result`, `approval_state`, `artifact_reference`, and `recovery_action`.

| Rule | Requirement |
|---|---|
| Format | One JSON object per event; no multiline secrets or unbounded payloads. |
| Correlation | Use run/task/execution identifiers that are safe to display. |
| Redaction | Apply `SecretScanner`/audit redaction before persistence or display. |
| Severity | Use `debug`, `info`, `warning`, `error`, or `critical`; critical requires review. |
| Retention | Retain events according to incident, audit, and release evidence policy. |
| Access | Apply least-privilege access and never expose raw log storage to the GUI. |
| Failure | Logging failure must not silently change workflow truth; emit a bounded fallback signal. |

## Operator runbooks

### Service unavailable or stale health

Confirm the local API/process and required runtime state, review the latest safe health reason code, and preserve the affected run and checkpoint identifiers. Do not paste credentials or raw provider responses into the incident record. Restart only through the approved service procedure, then verify authenticated health, dependency status, and recovery reconciliation before resuming work.

### Elevated workflow or provider failures

Confirm scope, time window, release, and correlation IDs. Check retry budget, circuit state, rate-limit status, and recent deployment changes. Pause or block new work when safety or idempotency cannot be established. Retry only through the bounded workflow policy; record the outcome and escalate terminal failures with the safe reason code.

### Queue, worker, or storage saturation

Inspect bounded queue depth, active leases, checkpoint age, storage health, and artifact retention pressure. Do not delete active runtime state. Reduce admission or pause schedules through authorized controls, recover stale leases only after the lease policy permits it, and verify that checkpoint and artifact references remain readable before resuming.

### Security or integrity finding

Treat secret exposure, invalid signature, policy violation, checksum mismatch, or attestation failure as a blocking condition. Preserve sanitized evidence, revoke or rotate affected credentials through the approved secret boundary, stop the impacted operation, and require an authorized review before resuming. Never include the suspected secret in the event or runbook record.

### Release or canary failure

Stop promotion, preserve the release/canary identifiers and validation results, compare health summaries against the previous approved release, and execute the approval-gated rollback procedure. Verify service health, state durability, artifact integrity, and notification delivery after rollback. Production actions require the deployment-owned approval gates.

## Ownership and escalation

The runtime component owns event emission, the health evaluator owns status projection, the audit/logging boundary owns redaction and persistence, and the operator owns review and approved recovery actions. The GUI presents bounded summaries and runbook links; it does not become the monitoring source of truth. External notification and hosted monitoring adapters are optional integrations subject to connector and approval policy.

## Acceptance checks and limits

A conforming implementation emits valid bounded structured events, redacts sensitive values, reports component health with freshness and stable reason codes, links alerts to runbooks, preserves correlation and recovery references, and provides standalone commands for local inspection. Focused tests cover the contract and secret-safe wording. Live alert delivery, hosted dashboards, load thresholds calibrated to production, retention enforcement, and operator tabletop exercises remain deployment-owned gates.
