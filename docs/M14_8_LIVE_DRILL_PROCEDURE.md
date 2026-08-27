# M14.8 Non-Production Canary and Rollback Drill Procedure

**Task ID:** `TODO-45ea939505f7`
**Status:** Preparation only. This document authorizes neither deployment nor production traffic.
**Owners:** Automation Agent and Verification Agent, with Security Agent approval gates.
**Scope:** A named, isolated non-production environment only.

Complete `docs/M14_8_CHANGE_WINDOW_AUTHORIZATION_TEMPLATE.md` and obtain its recorded approval before beginning any live-drill step in this procedure.

## Purpose and Safety Boundary

M14.8 is the mandatory pre-production gate for proving that a canary advances and rolls back safely under restart, duplicate-event, partial-failure, injected-fault, and rollback-failure conditions. It may begin only after the M14.2–M14.7 dependency gates have retained, independently reviewed evidence. This procedure is deliberately fail-closed: a missing owner, approval, telemetry source, rollback target, secret boundary, or evidence location stops the drill before traffic is changed.

> **Never use production credentials, production tenants, production data, or a production traffic route for this drill.** The drill is not a substitute for M14.9 disaster recovery, M14.10 readiness/load gates, or M14.11 controlled production canary approval.

## Deployment-Topology Decision Record

The implementation owner must select one of the two documented non-production operating approaches before the change window. This procedure does not select an approach on the owner’s behalf.

| Approach | Trade-offs | Cost | Setup complexity |
|---|---|---|---|
| Isolated managed non-production environment with provider-native canary controls | Best fidelity to the intended deployment provider, identity, observability, and rollback behavior; requires a dedicated tenant and provider approval. | Provider-dependent. | High: environment, workload identity, metrics, and provider adapter must be configured. |
| Dedicated operator-run non-production host using the reviewed adapter and synthetic workloads | Lower-cost rehearsal that remains inside a controlled non-production boundary; may not prove every managed-provider control. | Existing host capacity only. | Moderate: requires isolated host, bounded synthetic load, and approved local adapter configuration. |

Record the selected approach, target identifier, owner, rollback target, and approval reference in the execution record before deployment. If the selected environment cannot prove the required M14.8 acceptance behavior, stop and retain the limitation; do not represent the drill as complete.

## Prerequisites Checklist

All entries must be marked **complete**, include a safe evidence reference, and be reviewed by the named owner before the deployment stage. An unchecked item is a stop condition.

### A. Authority, Scope, and Change Control

| Check | Evidence required | Owner | Status |
|---|---|---|---|
| Named non-production environment, tenant boundary, data classification, RTO/RPO, escalation path, and rollback authority are approved. | M14.1 environment/responsibility record. | Automation + Security | [ ] |
| The change window, scope, cohort ceiling, stop conditions, and rollback decision authority are explicitly approved. | Approval reference with date/time and approver role. | Change authority | [ ] |
| All participants acknowledge that no production tenant, credential, traffic route, or real customer data is in scope. | Signed execution record acknowledgement. | All drill owners | [ ] |
| A named incident route and communications owner are available during the entire drill. | On-call/incident reference. | Operations | [ ] |

### B. M14 Dependency Gates

| Dependency | Required retained evidence | Owner | Status |
|---|---|---|---|
| M14.2 trust root | Operator-reviewed root metadata, separately pinned digest, and successful rotation/revocation/recovery drill. | Security | [ ] |
| M14.3 sandbox | Live validation on each supported Windows/Linux host for IPC, filesystem/network boundary, CPU/memory/PID limits, timeout, output validation, and cleanup. | Security + Verification | [ ] |
| M14.4 identity | Approved identity integration with tenant isolation, least privilege, revocation, approval checks, and audited negative cross-tenant tests. | Security + IDE | [ ] |
| M14.5 secrets | Non-production workload identity resolves references at runtime; rotation/redaction/access-review evidence is retained; no value appears in UI, logs, artifacts, or checkpoints. | Automation + Security | [ ] |
| M14.6 deployment adapter | Provider-specific dry-run, status, traffic split, pause, rollback, timeout, cancellation, idempotency, and credential-boundary tests pass. | Automation | [ ] |
| M14.7 metrics | Tenant/cohort/release-scoped error, latency, saturation, business, security, and release metrics pass freshness/completeness checks; no-data behavior is fail-closed. | Verification | [ ] |

### C. Technical Readiness

| Check | Evidence required | Owner | Status |
|---|---|---|---|
| A known-good rollback revision is immutable, retrievable, and compatible with the target environment. | Revision ID, artifact digest, and restoration/compatibility check. | Deployment owner | [ ] |
| Canary cohorts are defined as a bounded internal synthetic cohort and a bounded non-production cohort; no route permits production traffic. | Cohort and routing configuration review. | Automation + Security | [ ] |
| Deployment configuration uses non-production secret references only and has passed redaction review. | Sanitized configuration review. | Security | [ ] |
| Preflight checks complete for the chosen target. | `python tools/deployment_validation.py preflight --target <target>` output, where `<target>` is one supported target. | Deployment owner | [ ] |
| Synthetic baseline is rerun without external provider credentials. | `python tools/m13_12_fault_runner.py --output logs/m13_12_fault_injection.json` report with all scenarios passed. | Verification | [ ] |
| Observability dashboard, alert route, audit sink, and secure evidence location are ready before traffic changes. | Dashboard/query references and sanitized evidence path. | Verification | [ ] |

## Deployment and Drill Steps

### 1. Freeze the Execution Record

Create a unique drill record containing the task ID, execution date/time, selected approach, target environment, release revision, rollback revision, approvers, owners, evidence location, maximum cohort percentage, and stop conditions. Confirm every prerequisite is complete. The change authority must explicitly approve proceeding from preparation to deployment.

### 2. Run Credential-Free Preflight and Synthetic Baseline

Run the supported preflight command against the selected target. Run the synthetic M13.12 fault matrix separately; it verifies local control-plane behavior but does not replace live evidence. Store outputs in a sanitized, access-controlled evidence location and record only references/hashes in the execution record.

```text
python tools/deployment_validation.py preflight --target <sandbox|web-hosting|attached-desktop|persistent-computing>
python tools/m13_12_fault_runner.py --output logs/m13_12_fault_injection.json
```

Do not pass credentials on command lines. Any required provider/deployment access must resolve through the approved non-production workload identity at runtime.

### 3. Verify the Rollback Target Before Deployment

Before deploying the candidate, query the deployment provider through the reviewed adapter to verify the known-good revision, target scope, health baseline, and rollback capability. Confirm the candidate and rollback release identifiers are unique and idempotency keys are scoped to this drill. If the rollback target cannot be confirmed, stop.

### 4. Deploy the Candidate to the Internal Synthetic Cohort

Execute the reviewed adapter’s approved dry-run first, then deploy to the internal synthetic cohort only. Record the provider operation ID, bounded timeout, request correlation ID, and sanitized status. Do not advance the cohort until release, identity, secret-reference, metric-scope, and audit checks are all healthy.

### 5. Observe the Hold Window and Advance Once

During the approved hold window, require fresh and complete metrics for the specific tenant, cohort, and release. Apply the approved thresholds for error rate, p95/p99 latency, saturation, security findings, and business health. Any stale, missing, cross-scope, or malformed metric is a failed health evaluation and must pause or roll back according to the reviewed policy.

If all gates pass, advance once to the bounded non-production cohort. Maintain the pre-authorized cohort ceiling and hold window. The Verification Agent independently records the advance decision and source evidence.

### 6. Execute the Required Fault Matrix

Inject one scenario at a time; restore a healthy baseline before starting the next scenario. Do not continue after an uncontrolled failure.

| Scenario | Injection method | Required safe outcome | Evidence |
|---|---|---|---|
| Restart | Restart the approved worker/control component during active canary state. | State resumes from durable evidence without duplicate deployment or skipped rollback. | Event sequence, state revision, provider status. |
| Duplicate event | Replay the same signed/authorized event with the original idempotency key. | Exactly one material deployment action occurs; duplicate is recorded safely. | Idempotency and audit records. |
| Partial failure | Fail one approved non-critical component or metric source. | Canary pauses; the failure is classified; no automatic unsafe advance occurs. | Health decision, alert, safe diagnostic. |
| Injected release-health fault | Use synthetic load or a controlled fault to breach one approved metric threshold. | Canary pauses or rolls back within the documented limit. | Metric samples, controller action, provider status. |
| Rollback failure | Make the reviewed adapter return a bounded rollback failure in the non-production environment. | The release is not marked complete; incident route and recovery state are recorded; operator action is required. | Error class, quarantine state, incident record. |
| Deterministic recovery | Restore normal conditions and perform the approved recovery action. | State, cohort, and deployment status converge to the documented safe target without duplicate actions. | Final state, audit chain, recovery verification. |

### 7. Roll Back and Verify

Execute the planned rollback after the scenario matrix, even if the candidate remained healthy. Verify that the rollback revision receives all non-production traffic, candidate traffic is zero, health returns to baseline, no queued duplicate action remains, and audit evidence is complete. A provider-side confirmation alone is insufficient; the Verification Agent must independently confirm the observed state.

### 8. Close the Drill Without Production Promotion

End the change window by retaining sanitized evidence, recording all deviations, and explicitly confirming that no production canary has been created. M14.8 can be marked complete only when every required scenario has passed under the approved environment and its independent evidence has been retained. Otherwise record the drill as incomplete, link the failed gate, and create the next bounded remediation task.

## Stop and Escalation Conditions

Stop immediately and invoke the named incident route when any of the following occurs: an identity/tenant boundary breach; secret value exposure; unbounded traffic change; rollback-target uncertainty; missing or stale required metrics; missing audit evidence; unapproved provider operation; inability to pause/rollback within the approved limit; data-classification violation; or any connection to production infrastructure. Do not retry an unsafe action automatically.

## Evidence and Retention Checklist

The retained bundle must contain only sanitized material: approval references, environment identifiers, policy version/digest, candidate/rollback revision identifiers, cohort configuration, deployment operation IDs, bounded status records, timestamped metric summaries, audit-event hashes, fault-injection record, rollback verification, incident references, and independent Verification Agent conclusion. It must not contain credential values, bearer headers, cookies, customer data, raw provider payloads, or unrestricted logs.

## Completion Gate

M14.8 is complete only after the Automation Agent records the executed drill and the Verification Agent independently confirms: every prerequisite was satisfied; all six scenario outcomes were safe and deterministic; the final environment is returned to the known-good non-production state; evidence is retained and redacted; and no production action was performed. M14.9 and M14.10 remain separate mandatory gates before M14.11.
