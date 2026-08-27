# M14.8 Non-Production Canary and Rollback Drill Runbook

**Milestone:** M14.8 — Non-production canary and rollback drill
**Status:** In progress — execution and evidence collection required
**Owners:** Automation Agent and Verification Agent
**Dependencies:** M14.2–M14.7 local contracts, an approved non-production environment, a reviewed deployment adapter, a known-good rollback target, approved health sources, and a named rollback authority
**Evidence template:** [`artifacts/templates/M14_8_CANARY_ROLLBACK_ACCEPTANCE_EVIDENCE_TEMPLATE.md`](../artifacts/templates/M14_8_CANARY_ROLLBACK_ACCEPTANCE_EVIDENCE_TEMPLATE.md)

## Purpose

This runbook provides a controlled procedure for demonstrating that Orville's non-production deployment controls promote a candidate release only when fresh, scoped health evidence meets policy; stop promotion on unsafe conditions; and restore a known-good release deterministically. It supplies the operational evidence required for M14.8 without representing local fixtures, dry runs, or source-level tests as a live deployment result.

> **Safety boundary:** This procedure is restricted to an approved non-production environment. It must not use production credentials, production traffic, customer data, or production-only rollback targets. Every traffic mutation, pause, rollback, and retry requires the environment's existing change approval and named rollback authority.

## Acceptance objective

M14.8 is accepted only when a retained, sanitized evidence record shows successful controlled promotion and deterministic recovery from a controller restart, duplicate event, partial failure, injected health fault, and rollback failure. The durable controller state, reviewed deployment-adapter mutation record, and audit history must agree for every scenario.

| Acceptance condition | Required evidence |
|---|---|
| A known-good release can be promoted or restored | Approved target identifier, immutable release reference, approved change record, and successful authenticated health, read-only state, and smoke-workflow checks |
| Canary promotion is policy-bound | Versioned policy, cohort and hold settings, fresh scoped health observations, sample count, decision identifier, and adapter mutation record |
| Restart recovery is durable | Pre-restart and post-restart controller state with the same run, cohort, decision cursor, and idempotency context |
| Duplicate events are idempotent | Duplicate event input, unchanged state, and proof that no duplicate traffic or rollback mutation occurred |
| Partial and injected failures fail safely | Fault record, policy decision, paused/rolled-back/failed state, quarantine result, and escalation route |
| Rollback is bounded and verified | Rollback target, attempt count not exceeding policy, final controller state, and successful recovery verification—or an explicit failed-recovery record |
| Evidence is safe to retain | Redaction check confirming that credentials, bearer tokens, cookies, private keys, personal data, and raw provider responses are absent |

## Roles and decision authority

| Role | Responsibility | May authorize |
|---|---|---|
| Change owner | Opens the approved non-production change, confirms scope and timing, and preserves the evidence index | Drill start and closeout submission |
| Automation operator | Executes only approved adapter actions, records commands and immutable release references, and stops on a safety gate | No independent override of rollback policy |
| Verification reviewer | Independently checks controller state, adapter mutations, health observations, rollback evidence, and redaction | Acceptance recommendation |
| Rollback authority | Authorizes traffic changes, emergency pause, rollback, and retry after a failed recovery | Traffic mutation, rollback, and retry |
| Security/identity reviewer | Confirms environment boundary, identity scope, secret reference handling, and audit retention | Use of the target environment |
| Environment owner | Escalation contact for platform, monitoring, storage, and incident recovery | Environment-level incident actions |

No person may self-approve a traffic mutation and its independent acceptance review.

## Entry gates

The change owner must record every entry gate in the evidence template before beginning. If a gate cannot be demonstrated, do not start the live drill; retain a blocked result and keep M14.8 in progress.

| Gate | Verification requirement |
|---|---|
| Environment | Target is demonstrably non-production, has a named owner, and is isolated from production identities, data, credentials, and traffic |
| Change control | Time window, drill scope, approval reference, rollback authority, and escalation path are recorded |
| Candidate and rollback target | Candidate and known-good releases are immutable, approved, compatible with the target data/schema state, and uniquely identified |
| Deployment control | Reviewed adapter is configured for the target, dry-run preflight succeeds, timeouts and idempotency limits are bounded, and no secret value is emitted |
| Canary policy | Version, cohort sequence, maximum traffic, hold period, minimum sample count, freshness bound, thresholds, quarantine rules, and rollback-attempt limit are approved |
| Health sources | Error, latency, saturation, business-health, release/cohort identity, and security findings are tenant/cohort/release scoped, fresh, and accessible to the verifier |
| State and audit | Controller persistence, audit storage, clock source, event correlation, and restart procedure are available; evidence locations are access-controlled |
| Recovery readiness | Read-only health, checkpoint/state, and smoke-workflow checks are defined for the rollback target; no destructive data restore is within this drill's scope |
| Security | Required trust-root, identity, credential-reference, and secret-redaction controls have an accepted local-contract status and target-specific approval |

## Test sequence

The test order is deliberately conservative. Stop promotion before conducting fault tests, use the smallest configured non-production cohort, and return to the known-good target after every scenario that mutates traffic. The canonical local fault matrix is defined in [`M13_12_FAULT_INJECTION_AND_DEPLOYMENT_READINESS.md`](M13_12_FAULT_INJECTION_AND_DEPLOYMENT_READINESS.md); this runbook adds retained evidence requirements for the live non-production drill.

### 1. Open the drill and preserve the baseline

Record the approved change reference, operator and reviewer identities, environment identity, candidate and rollback-target references, policy version, adapter version, controller version, and evidence location. Capture pre-drill health, controller state, release/cohort identity, current traffic allocation, and a sanitized adapter status record. Confirm that the rollback target passes the defined health, read-only state, and smoke-workflow checks before altering traffic.

### 2. Run a clean, bounded canary progression

Execute the adapter's approved preflight or dry-run. Start the candidate at the smallest allowed cohort and wait for the approved observation hold. The verification reviewer must confirm that the health observations are fresh, complete, tenant/cohort/release scoped, and meet the policy's minimum sample and threshold requirements. Advance only to the next bounded cohort when the controller records an allowed decision and the adapter mutation matches it. Stop after the approved drill cohort; this activity must not be treated as production promotion.

### 3. Exercise restart recovery

During an observation hold, perform the approved controller restart or equivalent controlled interruption. On recovery, compare the persisted run ID, candidate, rollback target, cohort, decision cursor, idempotency context, hold timing, and audit sequence with the pre-restart record. Resume only if the restored state is complete and policy-valid. A newly created run, duplicate traffic shift, lost audit event, or broadened cohort fails this scenario.

### 4. Exercise duplicate-event handling

Submit or replay the same approved health event using its existing event identity or idempotency key. Confirm that state, traffic allocation, rollback attempt count, and adapter mutation count remain unchanged. Retain the duplicate-event diagnostic and the before/after state digests.

### 5. Exercise partial-failure and injected-fault response

Inject each approved fault using a synthetic adapter, reviewed provider stub, or non-production fault mechanism. At minimum, cover sparse or stale health evidence, threshold breach, security finding, candidate crash/worker exit, health-source unavailability, release/cohort mismatch, and malformed policy rejection. Confirm that the controller pauses, rolls back, or fails closed exactly as the current policy requires, with no unauthorized advancement.

### 6. Exercise rollback success and rollback failure recovery

Trigger a policy-valid rollback from a bounded cohort and verify that promotion stops, the candidate is quarantined where required, traffic returns to the known-good target, and the three recovery checks succeed. Separately inject a rollback timeout, unavailable rollback target, or quarantine failure. Confirm bounded retries, an explicit `paused` or `failed` state, preserved diagnostics, no false completion, and escalation to the environment owner. Do not retry a failed rollback until the rollback authority records a new approval.

### 7. Verify evidence and close the drill

The verification reviewer compares the controller state timeline, adapter mutation history, health observations, approval records, and audit sequence for every scenario. Run the repository's applicable local validation suites, including the existing synthetic fault-injection coverage, without treating those tests as a substitute for the live drill. Perform a redaction review of all retained material. Classify the result as accepted, conditionally accepted with approved remediation, failed, or blocked. Only an accepted result with all required evidence can change M14.8 from `in-progress-local` to completed.

## Scenario matrix

| Scenario | Expected safe result | Mandatory retained proof |
|---|---|---|
| Clean bounded progression | Promotion advances only through approved cohorts | Policy version, fresh observations, decision IDs, holds, controller states, and matching adapter calls |
| Controller restart during observation | Same run resumes without duplicated action | Before/after state, decision cursor, idempotency context, audit continuity, and traffic allocation |
| Duplicate health event | No-op with unchanged state | Original and duplicate event identities, state digests, and adapter mutation counts |
| Partial failure or candidate crash | Promotion stops; policy pauses or rolls back | Fault injection record, state, quarantine/rollback evidence, and escalation record |
| Health-threshold or critical-security fault | No unsafe advance; pause/rollback as policy requires | Scoped observations, threshold comparison, decision, and traffic result |
| Health-source unavailable or stale | Fail closed without success decision | Availability/staleness diagnostic, preserved cohort, and bounded retry handling |
| Rollback succeeds | Known-good target restored and verified | Rollback target, attempt count, health/state/smoke evidence, and closure record |
| Rollback timeout, missing target, or quarantine failure | Bounded retry then explicit failed/paused state | Attempt timeline, final state, no false completion, and authority escalation |
| Secret-bearing test metadata | Retained records remain redacted | Redaction review result and safe replacement diagnostics |

## Failure handling and stop conditions

Immediately stop promotion, preserve evidence, and notify the rollback authority and environment owner if the target is not non-production, an approval is missing or expired, a rollback target is unknown, health evidence is stale or cross-scoped, an identity/secret boundary fails, controller persistence is unavailable, or the adapter reports an uncorrelated traffic mutation. Do not delete logs, backups, release records, controller state, or audit material while the drill is unresolved.

A failed recovery must remain explicitly open. The next permitted action is a recorded decision by the rollback authority: an approved bounded retry, an operator-led infrastructure recovery, or abandonment of the candidate. The general recovery procedure and evidence requirements are defined in [`ROLLBACK_AND_RECOVERY_VERIFICATION.md`](ROLLBACK_AND_RECOVERY_VERIFICATION.md).

## Evidence retention and acceptance record

Create one completed evidence template per drill run. Retain only sanitized metadata, checksums, references, structured decisions, and approved excerpts in the repository or approved evidence store. Store raw logs, credentials, private keys, cookies, personal data, and provider responses only in the environment's protected logging and retention system; never place them in source control.

| Evidence class | Repository-safe representation | Protected-system location |
|---|---|---|
| Change and approval | Non-secret reference, scope, timestamp, role, and outcome | Change-management record |
| Release and deployment | Immutable identifier, digest, adapter version, cohort, and status | Deployment system audit trail |
| Health and security | Aggregates, decision inputs, freshness, and redacted diagnostics | Monitoring and security platforms |
| Controller and audit | State digest, event/decision identifiers, timestamps, and outcome | Controller persistence and audit store |
| Logs and incident data | Sanitized excerpt or checksum only | Access-controlled logging/incident store |
| Secrets and identities | Credential reference or role name only | Approved secret and identity systems |

## Completion criteria

The drill is complete when the change owner and verification reviewer complete the acceptance evidence template; all scenarios achieve their expected safe outcomes; restart, duplicate-event, partial-failure, and rollback-failure behavior is deterministic; recovery verification succeeds where applicable; no prohibited data is retained; and all exceptions have a named owner and disposition. Update `TODO.md`, `STATE.md`, and `TASK_GRAPH.md` only after that evidence has been independently reviewed.

## Related records

| Record | Purpose |
|---|---|
| [`docs/NEXT_MILESTONE_ENTERPRISE_PRODUCTION.md`](NEXT_MILESTONE_ENTERPRISE_PRODUCTION.md) | M14 objective, dependencies, and milestone acceptance gates |
| [`docs/M13_12_FAULT_INJECTION_AND_DEPLOYMENT_READINESS.md`](M13_12_FAULT_INJECTION_AND_DEPLOYMENT_READINESS.md) | Synthetic fault matrix and local safety baseline |
| [`docs/ROLLBACK_AND_RECOVERY_VERIFICATION.md`](ROLLBACK_AND_RECOVERY_VERIFICATION.md) | Approval-gated rollback and recovery evidence rules |
| [`docs/M14_REVIEWED_DEPLOYMENT_PROVIDER.md`](M14_REVIEWED_DEPLOYMENT_PROVIDER.md) | Reviewed adapter boundaries and dry-run controls |
| [`docs/M14_PRODUCTION_METRICS.md`](M14_PRODUCTION_METRICS.md) | Scoped health-source and metric-quality controls |
| [`artifacts/templates/M14_8_CANARY_ROLLBACK_ACCEPTANCE_EVIDENCE_TEMPLATE.md`](../artifacts/templates/M14_8_CANARY_ROLLBACK_ACCEPTANCE_EVIDENCE_TEMPLATE.md) | Per-drill acceptance evidence template |
