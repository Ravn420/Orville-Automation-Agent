# M14.8 Non-Production Canary and Rollback Drill — Acceptance Evidence

**Template version:** 1.0
**Use:** Create one completed copy per approved non-production drill. Retain this template unmodified as the repository baseline.
**Classification:** Internal operational evidence; sanitization required before repository storage
**Related runbook:** [`docs/M14_8_NONPRODUCTION_CANARY_ROLLBACK_DRILL_RUNBOOK.md`](../../docs/M14_8_NONPRODUCTION_CANARY_ROLLBACK_DRILL_RUNBOOK.md)

> Do not include credentials, bearer tokens, private keys, cookies, personal data, raw provider responses, raw logs, or production-only identifiers in this record. Use approved evidence references, immutable IDs, checksums, and redacted summaries.

## 1. Drill identity and approvals

| Field | Recorded value |
|---|---|
| Drill ID | `<M14.8-YYYYMMDD-sequence>` |
| Date and UTC start/end | `<YYYY-MM-DDThh:mm:ssZ>` / `<YYYY-MM-DDThh:mm:ssZ>` |
| Target environment | `<approved non-production environment identifier>` |
| Environment owner | `<role or approved identity reference>` |
| Change / approval reference | `<non-secret change record reference>` |
| Change owner | `<role or approved identity reference>` |
| Automation operator | `<role or approved identity reference>` |
| Verification reviewer | `<independent role or approved identity reference>` |
| Rollback authority | `<role or approved identity reference>` |
| Security / identity reviewer | `<role or approved identity reference>` |
| Escalation route | `<non-secret incident or on-call reference>` |
| Evidence-store location | `<approved protected location>` |
| Repository-safe evidence path | `<path to sanitized retained record>` |

## 2. Scope and entry-gate attestation

| Gate | Result (`pass` / `fail` / `blocked`) | Evidence reference or sanitized finding | Reviewer |
|---|---|---|---|
| Target is approved non-production and isolated from production traffic, data, identities, and credentials | `<result>` | `<reference>` | `<role>` |
| Change window, scope, rollback authority, and escalation route are approved | `<result>` | `<reference>` | `<role>` |
| Candidate release is immutable, approved, and uniquely identified | `<result>` | `<reference>` | `<role>` |
| Known-good rollback target is immutable, compatible, and independently healthy | `<result>` | `<reference>` | `<role>` |
| Reviewed deployment adapter preflight/dry-run succeeds without secret output | `<result>` | `<reference>` | `<role>` |
| Versioned policy defines bounded cohorts, holds, samples, thresholds, and rollback attempts | `<result>` | `<reference>` | `<role>` |
| Health sources are fresh and tenant/cohort/release scoped | `<result>` | `<reference>` | `<role>` |
| Controller persistence, event correlation, and audit retention are available | `<result>` | `<reference>` | `<role>` |
| Recovery health, read-only state, and smoke checks are defined | `<result>` | `<reference>` | `<role>` |
| Identity, trust-root, credential-reference, and redaction controls are approved for target scope | `<result>` | `<reference>` | `<role>` |

**Entry-gate disposition:** `<all-pass / blocked / cancelled>`
**Authorization to begin recorded by:** `<role and approval reference>`

## 3. Configuration and baseline

| Item | Recorded value |
|---|---|
| Candidate release identifier and digest | `<immutable identifier; no credential>` |
| Known-good rollback target and digest | `<immutable identifier; no credential>` |
| Deployment adapter and version | `<adapter identifier/version>` |
| Controller version / state-store schema | `<version>` |
| Canary policy identifier and digest | `<version/digest>` |
| Cohort sequence and maximum drill traffic | `<bounded cohort plan>` |
| Hold period and freshness bound | `<configured values>` |
| Minimum sample count and health thresholds | `<sanitized policy summary>` |
| Rollback maximum attempts and timeout | `<configured values>` |
| Initial controller state digest | `<checksum or immutable state reference>` |
| Initial traffic allocation | `<sanitized allocation>` |
| Baseline health result | `<pass/fail and evidence reference>` |
| Baseline authenticated health / read-only state / smoke checks | `<three result references>` |

## 4. Scenario evidence

Complete one row for every scenario executed. Attach only sanitized excerpts or references. Any unexpected result requires an incident or exception record.

| Scenario ID | Scenario | Injection or procedure reference | Expected safe result | Actual controller state | Actual adapter mutation result | Evidence references | Redaction reviewed | Verifier result |
|---|---|---|---|---|---|---|---|---|
| CP-01 | Clean bounded progression | `<reference>` | Advances only through approved cohorts | `<state>` | `<result>` | `<references>` | `<yes/no>` | `<pass/fail>` |
| CP-02 | Controller restart during observation | `<reference>` | Same run resumes; no duplicate action | `<state>` | `<result>` | `<references>` | `<yes/no>` | `<pass/fail>` |
| CP-03 | Duplicate health event | `<reference>` | No-op; state and traffic unchanged | `<state>` | `<result>` | `<references>` | `<yes/no>` | `<pass/fail>` |
| CP-04 | Sparse, stale, unavailable, or mismatched health evidence | `<reference>` | Fails closed; no unsafe advance | `<state>` | `<result>` | `<references>` | `<yes/no>` | `<pass/fail>` |
| CP-05 | Threshold breach or critical security finding | `<reference>` | Pauses or rolls back per policy | `<state>` | `<result>` | `<references>` | `<yes/no>` | `<pass/fail>` |
| CP-06 | Candidate crash or partial failure | `<reference>` | Promotion stops; candidate quarantined or rolled back | `<state>` | `<result>` | `<references>` | `<yes/no>` | `<pass/fail>` |
| CP-07 | Successful rollback | `<reference>` | Known-good target restored and verified | `<state>` | `<result>` | `<references>` | `<yes/no>` | `<pass/fail>` |
| CP-08 | Rollback timeout, missing target, or quarantine failure | `<reference>` | Bounded retry; explicit paused/failed state and escalation | `<state>` | `<result>` | `<references>` | `<yes/no>` | `<pass/fail>` |
| CP-09 | Secret-bearing adapter metadata | `<reference>` | State and audit records remain redacted | `<state>` | `<result>` | `<references>` | `<yes/no>` | `<pass/fail>` |

## 5. Restart, idempotency, and rollback verification

| Control | Required comparison | Result | Evidence reference |
|---|---|---|---|
| Restart recovery | Run ID, candidate, rollback target, cohort, decision cursor, idempotency context, hold timing, and audit sequence match the pre-restart record | `<pass/fail>` | `<reference>` |
| Duplicate-event idempotency | Original and duplicate event IDs map to one decision; state digest, traffic allocation, rollback attempt count, and mutation count are unchanged | `<pass/fail>` | `<reference>` |
| Successful rollback | Promotion stopped; known-good target restored; candidate quarantined as required; recovery checks pass | `<pass/fail>` | `<reference>` |
| Failed rollback handling | Attempt count did not exceed policy; no false completion; final paused/failed state and escalation are explicit | `<pass/fail>` | `<reference>` |
| Recovery checks | Authenticated health, read-only state/checkpoint, and representative smoke workflow all pass against the rollback target | `<pass/fail>` | `<reference>` |

## 6. Audit, security, and evidence-retention review

| Review item | Result | Sanitized finding or reference | Reviewer |
|---|---|---|---|
| Controller state timeline and adapter mutation history agree | `<pass/fail>` | `<reference>` | `<role>` |
| Health observations are tenant/cohort/release scoped, fresh, and policy-complete | `<pass/fail>` | `<reference>` | `<role>` |
| Approval and authority references are complete and within scope | `<pass/fail>` | `<reference>` | `<role>` |
| Audit sequence is durable, ordered, and correlated to decision IDs | `<pass/fail>` | `<reference>` | `<role>` |
| Logs, diagnostics, and evidence are sanitized | `<pass/fail>` | `<reference>` | `<role>` |
| No secrets, protected identities, personal data, raw provider responses, or production-only identifiers were committed | `<pass/fail>` | `<reference>` | `<role>` |
| Protected raw evidence has the required retention/access-control record | `<pass/fail>` | `<reference>` | `<role>` |

## 7. Exceptions, incidents, and remediation

| ID | Description | Impact | Immediate safe state | Owner | Due date | Approval or incident reference | Closure evidence |
|---|---|---|---|---|---|---|---|
| `<EX-01>` | `<finding>` | `<impact>` | `<paused/rolled_back/failed/blocked>` | `<role>` | `<date>` | `<reference>` | `<reference>` |

## 8. Acceptance decision

| Decision | Selection and rationale |
|---|---|
| Overall disposition | `<accepted / conditionally accepted with approved remediation / failed / blocked>` |
| Requirements satisfied | `<list or reference>` |
| Requirements not satisfied | `<list or none>` |
| Residual risks | `<sanitized summary>` |
| Required remediation | `<owner, due date, and approval reference>` |
| M14.8 tracker action | `<retain in-progress-local / mark completed after independent acceptance>` |
| Next permitted milestone | `<M14.9 only after acceptance>` |

**Change owner attestation:** `<name/role reference, UTC timestamp, approval reference>`
**Independent verification attestation:** `<name/role reference, UTC timestamp, decision>`
**Rollback authority acknowledgement:** `<name/role reference, UTC timestamp, decision>`

## 9. Repository-safe evidence index

| Artifact | Safe repository reference | Protected-system reference | SHA-256 or immutable ID | Retention owner |
|---|---|---|---|---|
| Sanitized drill record | `<path>` | `<reference>` | `<digest>` | `<role>` |
| Policy snapshot | `<path>` | `<reference>` | `<digest>` | `<role>` |
| Controller-state summary | `<path>` | `<reference>` | `<digest>` | `<role>` |
| Adapter mutation summary | `<path>` | `<reference>` | `<digest>` | `<role>` |
| Health-decision summary | `<path>` | `<reference>` | `<digest>` | `<role>` |
| Recovery verification summary | `<path>` | `<reference>` | `<digest>` | `<role>` |
| Redaction review | `<path>` | `<reference>` | `<digest>` | `<role>` |
