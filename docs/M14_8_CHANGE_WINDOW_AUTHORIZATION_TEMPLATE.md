# M14.8 Change-Window Authorization Request Template

**Template version:** 1.0
**Related task:** `TODO-45ea939505f7` — M14.8 non-production canary and rollback drill
**Use:** Complete this document before seeking approval to execute the live drill described in `docs/M14_8_LIVE_DRILL_PROCEDURE.md`.

> **This is a request template, not an authorization.** It does not permit a deployment, provider operation, traffic change, credential use, fault injection, or production action until the designated approvers sign the decision record below.

## 1. Request Identification

| Field | Requester input |
|---|---|
| Request ID | `<change-request-id>` |
| Requested execution date and time | `<ISO-8601 date/time with timezone>` |
| Requested change-window start and end | `<start>` to `<end>` |
| Requester name and role | `<name / role>` |
| Automation owner | `<name / role>` |
| Verification owner | `<name / role>` |
| Security approver | `<name / role>` |
| Change authority | `<name / role>` |
| Incident commander and communications owner | `<name / role>` |
| Approval reference | `<ticket, decision-record, or signed-request reference>` |
| Status | `draft / submitted / approved / declined / expired / completed` |

## 2. Requested Scope and Safety Boundary

Describe the minimum necessary scope. The request must name a single non-production environment and must not use production tenants, production data, production credentials, or production traffic routes.

| Scope element | Required request value |
|---|---|
| Environment and tenant identifier | `<non-production target only>` |
| Data classification | `<synthetic / approved non-production dataset>` |
| Candidate release identifier and digest | `<candidate revision / digest>` |
| Immutable rollback release identifier and digest | `<known-good revision / digest>` |
| Deployment provider and approved adapter version | `<provider / adapter version>` |
| Maximum cohort ceiling | `<percentage or named bounded cohort>` |
| Initial synthetic cohort | `<internal cohort / route>` |
| Non-production cohort | `<named bounded cohort / route>` |
| Explicit exclusions | `Production routes, production tenants, real customer data, and production credentials are excluded.` |
| Expected customer impact | `None. State why the selected routing makes this true.` |

The requested action must be limited to a dry run, candidate deployment, bounded non-production cohort movement, the approved fault matrix, rollback to the named release, and evidence retention. Any action outside this boundary requires a new authorization.

## 3. Environment Approach Selection

Select one approach and explain why it can prove the required controls. Do not approve the request until the selection, associated costs, and limitations are understood.

| Approach | Trade-offs | Cost | Setup complexity | Select |
|---|---|---|---|---|
| Isolated managed non-production environment with provider-native canary controls | Highest fidelity for provider, identity, routing, and observability; requires dedicated tenant and provider access governance. | Provider-dependent. | High. | `[ ]` |
| Dedicated operator-run non-production host using reviewed adapter and synthetic workloads | Lower-cost rehearsal that can prove selected adapter controls; may not prove every managed-provider feature. | Existing approved host capacity. | Moderate. | `[ ]` |

**Selection rationale and known limitations:**

```text
<Explain the selected environment, why it is isolated, which live controls it proves, and which controls it cannot prove.>
```

## 4. M14 Dependency Evidence Gate

Every line must be complete with a sanitized evidence reference. A missing item is a **no-go** condition, not a risk accepted by default.

| Gate | Required evidence | Evidence locator or digest | Owner | Reviewed | Status |
|---|---|---|---|---|---|
| M14.1 environment and responsibility matrix | Approved environment, tenant boundary, classification, RTO/RPO, escalation route, and rollback authority. | `<reference>` | Automation + Security | `<reviewer/date>` | `[ ]` |
| M14.2 trust root | Reviewed root metadata, out-of-band pinned digest, rotation/revocation/recovery drill, and audit evidence. | `<reference>` | Security | `<reviewer/date>` | `[ ]` |
| M14.3 sandbox | Windows/Linux host validation for IPC, boundaries, resources, timeout, output validation, and cleanup. | `<reference>` | Security + Verification | `<reviewer/date>` | `[ ]` |
| M14.4 identity | Tenant isolation, least privilege, approval checks, revocation, and audit evidence for the approved identity adapter. | `<reference>` | Security + Identity | `<reviewer/date>` | `[ ]` |
| M14.5 secrets | Runtime reference resolution, rotation, redaction, access review, and proof that no secret value is retained in evidence. | `<reference>` | Automation + Security | `<reviewer/date>` | `[ ]` |
| M14.6 provider adapter | Approved provider-specific dry run, status, traffic split, pause, rollback, timeout, cancellation, and idempotency evidence. | `<reference>` | Automation | `<reviewer/date>` | `[ ]` |
| M14.7 metrics | Tenant/cohort/release-scoped metrics, freshness/completeness behavior, alert route, and no-data fail-closed test. | `<reference>` | Verification | `<reviewer/date>` | `[ ]` |

## 5. Operational Readiness Checklist

| Control | Request-specific evidence | Status |
|---|---|---|
| Candidate artifact has passed the declared regression, security, and deployment checks. | `<test references and revision>` | `[ ]` |
| Rollback artifact is immutable, retrievable, compatible, and independently verified in the target. | `<revision/digest and verification>` | `[ ]` |
| Approved change window, maximum cohort, maximum hold, stop conditions, and rollback authority are recorded. | `<approval reference>` | `[ ]` |
| Workload identity uses approved non-production secret references only; no credential is supplied by command line or stored in the request. | `<sanitized security review>` | `[ ]` |
| Provider operation IDs, audit sink, metrics dashboard, alert route, and sanitized evidence location are available. | `<safe references>` | `[ ]` |
| Clock source, metric-freshness limit, minimum sample count, and health thresholds are documented and approved. | `<policy revision/digest>` | `[ ]` |
| A named incident commander and communication channel are staffed for the full window. | `<on-call reference>` | `[ ]` |
| Synthetic M13.12 baseline passed without external credentials. | `<sanitized report hash>` | `[ ]` |

## 6. Planned Execution Timeline

The change authority must approve each decision point. Times are estimates; do not advance merely because a planned time has elapsed.

| Step | Planned window | Responsible owner | Required go/no-go evidence | Approval required |
|---|---|---|---|---|
| Freeze execution record and verify all prerequisites | `<time>` | Automation + Verification | All Section 4 and Section 5 entries are complete. | Change authority |
| Run approved provider dry run and verify rollback target | `<time>` | Automation | Dry-run operation ID, target scope, artifact digests, and baseline health. | Security + Change authority |
| Deploy to internal synthetic cohort | `<time>` | Automation | Safe provider status, scoped route, correlation ID, and audit event. | Change authority |
| Observe approved hold window | `<time>` | Verification | Fresh, complete, release-scoped metrics and no stop condition. | Verification |
| Advance once to bounded non-production cohort | `<time>` | Automation | Independent verified go decision and cohort ceiling confirmation. | Change authority |
| Run fault-injection matrix | `<time>` | Automation + Verification | One scenario at a time with verified baseline restoration. | Security for each fault class |
| Execute planned rollback and independently verify recovery | `<time>` | Automation + Verification | Candidate traffic is zero and known-good release is healthy. | Change authority |
| Retain sanitized evidence and close record | `<time>` | Verification | Independent conclusion and no-production statement. | Verification + Security |

## 7. Fault-Injection Authorization Matrix

Each fault is opt-in. Leave a row unchecked if the target cannot perform the fault safely and list it as an incomplete M14.8 gate. Do not substitute a local synthetic result for live evidence.

| Scenario | Target-scoped injection plan | Expected safe result | Abort and escalation trigger | Required evidence | Approve |
|---|---|---|---|---|---|
| Restart | `<approved component / restart mechanism>` | Durable state resumes without duplicate deployment or skipped rollback. | Unexpected state transition, duplicate provider action, or unbounded restart loop. | Event sequence, state revision, provider status. | `[ ]` |
| Duplicate event | `<event source / original idempotency key>` | Exactly one material deployment action; duplicate is safely recorded. | A second material provider action or missing audit record. | Idempotency and audit records. | `[ ]` |
| Partial failure | `<approved non-critical component or metric source>` | Canary pauses; failure is classified; no unsafe advance occurs. | Loss of observability, cross-scope effect, or inability to pause. | Health decision, alert, safe diagnostic. | `[ ]` |
| Release-health fault | `<scoped synthetic load or controlled threshold breach>` | Canary pauses or rolls back within the approved limit. | Threshold breach without controller action or a route outside the cohort ceiling. | Metric samples, controller action, provider status. | `[ ]` |
| Rollback failure | `<bounded reversible provider-adapter failure>` | Release is not complete; quarantine/incident state requires operator action. | Irreversible state, unbounded traffic, or failed incident route. | Error class, quarantine state, incident record. | `[ ]` |
| Deterministic recovery | `<approved recovery action>` | Cohort, state, and deployment converge to the known-good non-production target without duplicate action. | Recovery does not converge within approved limit. | Final state, audit chain, recovery verification. | `[ ]` |

## 8. Monitoring, Stop Conditions, and Rollback Authority

The request must list target-specific values rather than relying on local defaults.

| Category | Approved value or rule |
|---|---|
| Minimum sample count | `<value>` |
| Metric freshness limit | `<value and clock source>` |
| Error-rate threshold | `<value>` |
| p95 and p99 latency threshold | `<values>` |
| Saturation threshold | `<value>` |
| Business-health threshold | `<value>` |
| Critical-security-finding threshold | `<value; normally zero>` |
| Maximum cohort | `<value>` |
| Maximum hold and recovery duration | `<values>` |
| Primary rollback authority | `<name / role>` |
| Alternate rollback authority | `<name / role>` |
| Incident route | `<safe reference>` |

**Automatic stop conditions:** identity or tenant-boundary breach; secret exposure; production-route contact; missing, stale, malformed, or cross-scope telemetry; missing audit evidence; unapproved provider operation; rollback-target uncertainty; cohort ceiling breach; or inability to pause/rollback within the approved limit.

## 9. Evidence, Redaction, and Retention

| Evidence category | Retention requirement | Safe reference |
|---|---|---|
| Authorization and decision record | Retain approver role, time, scope, and decision. Do not retain personal or credential data beyond policy. | `<reference>` |
| Deployment and provider status | Retain operation IDs, revision IDs/digests, bounded status, and correlation IDs only. | `<reference>` |
| Observability | Retain timestamped tenant/cohort/release-scoped summaries and alert disposition. | `<reference>` |
| Fault outcomes | Retain scenario ID, expected/observed state, recovery result, and independent verifier conclusion. | `<reference>` |
| Security and audit | Retain safe event hashes and redacted classifications; exclude credentials, headers, cookies, customer data, and raw sensitive payloads. | `<reference>` |
| Final status | Record complete, incomplete, or failed; link remediation task if a gate does not pass. | `<reference>` |

## 10. Risk Assessment

| Risk | Likelihood | Impact | Mitigation | Residual risk | Owner |
|---|---|---|---|---|---|
| Provider route affects a production boundary | `<low/medium/high>` | `<impact>` | Explicit non-production route review, cohort cap, and preapproved stop condition. | `<value>` | Security |
| Rollback does not converge | `<low/medium/high>` | `<impact>` | Immutable rollback target, bounded timeout, incident route, and recovery verification. | `<value>` | Automation |
| Metrics are incomplete or stale | `<low/medium/high>` | `<impact>` | Freshness/completeness gate that pauses or rolls back rather than advances. | `<value>` | Verification |
| Secret or sensitive data enters evidence | `<low/medium/high>` | `<impact>` | Runtime reference-only access, redaction review, and sanitized evidence location. | `<value>` | Security |
| Fault injection exceeds scope | `<low/medium/high>` | `<impact>` | Scenario-specific approval, one-at-a-time execution, and immediate abort criteria. | `<value>` | Change authority |

## 11. Authorization Decision Record

| Decision | Approver | Role | Date/time | Scope or condition |
|---|---|---|---|---|
| `[ ] Approved` | `<name>` | Change authority | `<ISO-8601>` | `<approved scope and expiry>` |
| `[ ] Approved with conditions` | `<name>` | Security | `<ISO-8601>` | `<conditions; unresolved condition is a no-go>` |
| `[ ] Declined` | `<name>` | `<role>` | `<ISO-8601>` | `<reason and follow-up>` |
| `[ ] Deferred` | `<name>` | `<role>` | `<ISO-8601>` | `<missing evidence or dependency>` |

**Approval expiry:** `<ISO-8601 date/time>`. The authorization automatically expires if the approved environment, release digest, rollback digest, provider adapter, cohort cap, fault matrix, or change window changes.

## 12. Post-Window Closure

| Closure check | Owner | Status |
|---|---|---|
| Candidate traffic is zero and the immutable rollback release is healthy in the non-production target. | Automation + Verification | `[ ]` |
| All authorized faults have a complete, sanitized evidence record and final disposition. | Verification | `[ ]` |
| Any failed or skipped scenario has a bounded remediation task and is not recorded as M14.8 complete. | Orchestration | `[ ]` |
| Independent verification concludes whether the M14.8 acceptance gate passed. | Verification | `[ ]` |
| The record explicitly confirms that no production action, route, tenant, credential, or customer data was used. | Security | `[ ]` |
| `TODO.md`, `TASK_GRAPH.md`, `STATE.md`, and `CHANGELOG.md` are updated only after the evidence review is complete. | Orchestration | `[ ]` |
