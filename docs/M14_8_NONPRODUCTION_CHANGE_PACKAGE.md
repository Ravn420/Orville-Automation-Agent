# M14.8 Non-Production Canary and Rollback Drill — Change Package

**Package ID:** `M14.8-NP-2026-08-27-01`
**Milestone:** M14.8 — Non-production canary and rollback drill
**Current state:** Prepared; not approved for execution
**Classification:** Internal operational planning; no production data, credentials, or raw operational logs permitted
**Primary owners:** Automation Agent and Verification Agent
**Required approvers:** Change owner, rollback authority, environment owner, security/identity reviewer
**Related procedure:** [`M14_8_NONPRODUCTION_CANARY_ROLLBACK_DRILL_RUNBOOK.md`](M14_8_NONPRODUCTION_CANARY_ROLLBACK_DRILL_RUNBOOK.md)

## 1. Change objective

Execute an approved, bounded **non-production** canary and rollback drill that demonstrates deterministic promotion control, restart recovery, duplicate-event idempotency, partial/injected-fault response, and rollback-failure handling. The drill must retain safe, independently reviewable evidence without representing a dry run, synthetic test, or local contract as live non-production execution.

> **Execution prohibition:** Do not execute this package until every entry gate is recorded as passed and the named rollback authority grants a current, single-use approval for the exact target, candidate, rollback target, cohort ceiling, and time window. A dry-run result is preparation evidence only and never satisfies the approval requirement.

## 2. Scope and boundaries

| In scope | Explicitly out of scope |
|---|---|
| Approved isolated non-production environment | Production environment, traffic, data, credentials, and rollback targets |
| Reviewed adapter preflight and bounded canary cohorts | Automatic production promotion, provider account setup, or unapproved connector actions |
| Candidate promotion, health observation, pause, rollback, quarantine, and recovery validation | Database migration, destructive data restoration, or deletion of evidence |
| Restart, duplicate-event, partial-failure, fault, and rollback-failure scenarios | Use of raw logs, tokens, cookies, private keys, or personal data in repository artifacts |
| Sanitized evidence collection and independent verification | Changing M14.8 to complete before independent acceptance |

## 3. Required roles and contacts

| Role | Named reference required before execution | Authority and responsibility |
|---|---|---|
| Change owner | `<role or approved identity reference>` | Opens/closes the change and confirms scope, time window, and evidence location |
| Automation operator | `<role or approved identity reference>` | Executes approved adapter actions and records only sanitized technical evidence |
| Verification reviewer | `<independent role or approved identity reference>` | Reconciles controller, adapter, health, and audit outcomes; issues acceptance recommendation |
| Rollback authority | `<role or approved identity reference>` | Approves traffic mutation, pause, rollback, and any post-failure retry |
| Security/identity reviewer | `<role or approved identity reference>` | Confirms target boundary, identity scope, secret handling, and audit retention |
| Environment owner | `<role or approved identity reference>` | Provides platform/monitoring support and owns incident escalation |
| Incident route | `<non-secret ticket/on-call reference>` | Receives failed-recovery or boundary-breach escalation |

No person may self-approve both the traffic mutation and the independent verification result.

## 4. Entry-gate checklist

The change owner must complete the companion entry-gate record before requesting approval. Any `fail`, `blocked`, missing evidence, or scope ambiguity prevents execution.

| Gate | Required pass condition | Evidence reference |
|---|---|---|
| Environment isolation | Target is explicitly non-production and has no production traffic, identity, data, credential, or rollback-target overlap | `<reference>` |
| Change control | Exact time window, drill scope, rollback authority, escalation route, and change identifier are recorded | `<reference>` |
| Candidate/target | Candidate and known-good rollback target are immutable, approved, compatible, and uniquely identified | `<reference>` |
| Adapter preflight | Reviewed deployment adapter passes approved dry-run/preflight without an external mutation or secret output | `<reference>` |
| Canary policy | Versioned policy specifies bounded cohorts, holds, fresh-health interval, sample floor, thresholds, quarantine, and rollback attempt limit | `<reference>` |
| Health sources | Error, latency, saturation, business-health, release/cohort identity, and security signals are fresh and target-scoped | `<reference>` |
| Durable control plane | Controller persistence, audit record, correlation IDs, and controlled restart procedure are available | `<reference>` |
| Recovery readiness | Known-good target passes baseline authenticated health, read-only state/checkpoint, and smoke-workflow checks | `<reference>` |
| Security/identity | Target-specific trust, identity, credential-reference, approval, and redaction boundaries are approved | `<reference>` |
| Evidence handling | Protected raw-evidence location and repository-safe sanitized location are access-controlled and recorded | `<reference>` |

## 5. Planned execution timeline

| Stage | Activity | Stop condition | Completion evidence |
|---|---|---|---|
| T-30 days to T-7 days | Confirm owners, target isolation, candidate/rollback releases, policy, monitoring, and evidence store | Missing owner, unsupported environment, or uncontrolled dependency | Completed entry-gate record |
| T-7 days to T-1 day | Run adapter dry-run/preflight; establish baseline health and controlled restart procedure | Preflight mutates target, baseline fails, or evidence cannot be retained safely | Sanitized preflight and baseline record |
| T-0 approval | Obtain single-use approval for exact run/step/scope | Rejected, expired, missing, or scope-mismatched approval | Approval reference and authorized scope |
| T-0 execution | Run bounded promotion, restart/idempotency, fault, rollback, and recovery scenarios | Unsafe advance, uncorrelated mutation, stale/cross-scoped health, or failed rollback | Controller/adaptor/health/audit correlation record |
| T+0 review | Independent review, redaction check, exception disposition, and M14.8 status decision | Incomplete evidence or unresolved failed recovery | Signed acceptance or blocked/failed record |

## 6. Scenario and acceptance matrix

| Scenario | Expected safe outcome | Mandatory evidence |
|---|---|---|
| Bounded clean progression | Advance only through policy-approved cohorts after fresh, scoped, sufficient health observations | Policy snapshot, decision IDs, controller states, holds, and matching adapter actions |
| Controlled restart during observation | Same run resumes with unchanged cohort/decision context; no duplicate action | Before/after state, idempotency context, audit sequence, and traffic allocation |
| Duplicate health event | No-op; no duplicate traffic or rollback mutation | Original/duplicate event IDs, state digests, and mutation counts |
| Partial failure or candidate crash | Promotion stops; pause/rollback/quarantine complies with policy | Fault reference, final state, adapter evidence, and escalation route |
| Threshold/security fault | No unsafe advance; controller pauses or rolls back as policy dictates | Fresh scoped observation, threshold decision, and traffic result |
| Successful rollback | Known-good target restored; health/state/smoke checks pass | Rollback target, bounded attempts, three recovery-check results, closure reference |
| Rollback timeout/missing target/quarantine failure | Bounded retries, explicit paused/failed state, preserved evidence, authority escalation | Attempt timeline, final state, safe diagnostics, and authority decision |
| Secret-bearing diagnostic input | Repository-safe evidence remains redacted | Redaction review and sanitized evidence reference |

## 7. Approval request text

> **Requested action:** Execute one bounded non-production canary and rollback drill for package `M14.8-NP-2026-08-27-01` against target `<target>`, using candidate `<candidate immutable ID>` and known-good rollback target `<rollback immutable ID>`. The maximum cohort is `<ceiling>` for `<window>`. The drill includes controlled restart, duplicate-event, partial-failure, health/security fault, rollback, and rollback-failure scenarios. All traffic changes are reversible to the identified known-good target. No production traffic, production data, production credentials, or destructive data restore is included. Approval is requested only for this run, scope, and time window.

## 8. Required evidence and retention

| Evidence category | Repository-safe record | Protected-system record |
|---|---|---|
| Approval/change control | ID, role, scope, timestamp, outcome | Full change-management record |
| Releases and adapter operations | Immutable IDs, cohort, operation IDs, decision outcome | Deployment/audit system history |
| Health and security | Aggregates, freshness, decision, sanitized diagnostic | Monitoring and security platforms |
| Controller persistence | State digest and event/decision IDs | Controller state/audit store |
| Recovery validation | Health/state/smoke results and rollback decision | Protected operational evidence store |
| Raw logs and sensitive information | Checksum or sanitized excerpt only | Access-controlled logging/incident platform |

Use the full per-run record at [`M14_8_CANARY_ROLLBACK_ACCEPTANCE_EVIDENCE_TEMPLATE.md`](../artifacts/templates/M14_8_CANARY_ROLLBACK_ACCEPTANCE_EVIDENCE_TEMPLATE.md). Do not commit completed evidence until a redaction reviewer confirms it is repository-safe.

## 9. Completion decision

M14.8 may remain `in-progress-local` after preparation or dry-run activity. It may change to completed only after the independent verification reviewer confirms that each required scenario produced the expected safe state; controller, adapter, health, and audit evidence reconcile; rollback recovery was verified; retained evidence is sanitized; and all exceptions are closed or formally dispositioned by the authorized owner.

## Related controls

| Control | Role in this package |
|---|---|
| [`APPROVAL_CHECKPOINTS.md`](APPROVAL_CHECKPOINTS.md) | Single-use, scope-bound approval and fail-closed execution rules |
| [`WORKFLOW_DRY_RUN.md`](WORKFLOW_DRY_RUN.md) | Preflight/dry-run boundary; preview is not approval or execution |
| [`M14_8_NONPRODUCTION_CANARY_ROLLBACK_DRILL_RUNBOOK.md`](M14_8_NONPRODUCTION_CANARY_ROLLBACK_DRILL_RUNBOOK.md) | Detailed operational drill procedure and failure handling |
| [`ROLLBACK_AND_RECOVERY_VERIFICATION.md`](ROLLBACK_AND_RECOVERY_VERIFICATION.md) | Approval-gated rollback and recovery verification requirements |
| [`M14_9_BACKUP_RECOVERY_EXECUTION_PLAN.md`](M14_9_BACKUP_RECOVERY_EXECUTION_PLAN.md) | Subsequent backup, restore, and disaster-recovery milestone plan |
