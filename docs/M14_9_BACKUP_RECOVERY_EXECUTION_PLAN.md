# M14.9 Backup, Restore, and Disaster-Recovery Execution Plan

**Milestone:** M14.9 — Backup, restore, and disaster-recovery operations
**Status:** Planned — execution follows accepted M14.8 evidence
**Owners:** Automation Agent and Security Agent
**Dependencies:** M14.1 approved enterprise environment, M14.4 identity and authorization boundary, named data/recovery owners, an approved protected storage target, and explicit change approval for restore exercises

## Objective

Establish evidence-backed backup and recovery controls for Orville's approved enterprise environment. The milestone is complete only after encrypted off-host backups, retention controls, restore verification, RTO/RPO evidence, access review, and an operator-ready recovery runbook have been exercised without placing protected data or credentials in source control.

> **Safety boundary:** A backup is not proof of recoverability. No restore, destructive repair, credential rotation, or production operation may be initiated automatically. Restore exercises require an approved target environment, a named recovery owner, an explicit change record, and a verified copy of the original data and evidence.

## Required outcome

| Control | M14.9 completion evidence |
|---|---|
| Backup coverage | Inventory maps every recoverable state store, release artifact, configuration class, audit record, and critical dependency to a backup method, owner, cadence, and exclusion rule |
| Encryption and off-host storage | Approved protected storage location, encryption-at-rest/in-transit evidence, immutable or tamper-resistant retention where available, and secret-free backup metadata |
| Recovery objectives | Owner-approved RTO and RPO target, measurement method, actual drill measurements, and exception/disposition record |
| Restore verification | Restored non-production copy passes integrity, authenticated health, read-only state/checkpoint, and representative smoke-workflow checks |
| Access review | Least-privilege reviewer-approved access matrix for backup creation, retrieval, restore, deletion, and audit review |
| Operational readiness | Approved recovery runbook, contact/escalation route, retained evidence index, and a tested decision path for failed restoration |

## Execution sequence

### 1. Establish scope, ownership, and recovery objectives

Create an authoritative inventory of data and artifacts that may require recovery. At minimum include controller state, task/workflow records, audit and approval records, configuration that is permitted to be backed up, persistent application data, release identifiers, infrastructure configuration references, and necessary recovery documentation. Explicitly exclude provider keys, raw credentials, private keys, cookies, and unapproved personal data from repository evidence.

Record the system owner, backup operator, restoration authority, security reviewer, incident owner, and escalation path. For every asset class, define an owner-approved recovery point objective (RPO), recovery time objective (RTO), target environment, data classification, backup frequency, retention period, and restore priority.

### 2. Select and approve the backup architecture

Choose an approved backup mechanism appropriate to the deployed storage technology. Document the source boundary, backup format, encryption, key-management responsibility, transport protection, off-host location, access controls, immutability or deletion safeguards, retention schedule, integrity check, and monitoring/alerting path. The architecture must keep runtime data outside source control and retain only non-secret backup metadata, identifiers, and checksums in repository evidence.

Before scheduling automated copies, run a dry-run or read-only preflight that proves source access, target containment, capacity, encryption configuration, permissions, and non-secret logging behavior. Fail closed if the target is local-only, the protected storage policy is unavailable, backup size/cadence exceeds the approved resource bounds, or the process would expose secrets.

### 3. Implement bounded, auditable backup operations

Implement or configure the approved backup workflow with a stable backup identifier, idempotency key, source snapshot/transaction boundary, timestamp, size, checksum, encryption/key reference, off-host target reference, retention expiry, and sanitized audit record. The workflow must detect concurrent runs, partial uploads, checksum mismatch, expired credentials, insufficient capacity, and unavailable targets without marking a backup successful.

Schedule backups only after the operator has approved cadence and retention. The failure path must keep the last known-good backup intact, emit a redacted alert to the named owner, retry only within the approved policy, and preserve enough metadata for independent troubleshooting.

### 4. Verify backup integrity and retention controls

For every candidate recovery point, verify that the backup object exists in the approved off-host location; its checksum or immutable identifier matches the recorded source snapshot; it is decryptable by an authorized recovery role; and its retention and legal/operational hold status are correctly applied. Perform periodic independent verification using a separate operator or service identity where the platform permits it.

Record the results as a sanitized backup ledger. A checksum alone does not validate application recovery, but any mismatch, inaccessible object, unapproved retention change, or unauthorized access finding blocks use of that recovery point.

### 5. Execute a controlled non-production restore drill

Obtain a restore-specific change approval and select an isolated non-production target. Preserve the original source and the selected backup before beginning. Restore the approved backup using the target-specific recovery method, then perform the four validation classes: integrity/checksum verification, authenticated health check, read-only state or checkpoint check, and representative smoke workflow.

Measure elapsed time from approved restore start to verified service readiness. Compare the recovery point timestamp and recovered state with the RPO target, and compare elapsed time with the RTO target. Retain a sanitized drill record containing backup identifier/checksum, target scope, command or procedure references, decision timeline, validation results, measurements, exceptions, and reviewer sign-off. Do not overwrite the original source during the exercise.

### 6. Test failure and escalation paths

Exercise at least one safe non-production failure mode, such as an inaccessible backup object, checksum mismatch, insufficient recovery capacity, incompatible release/schema, expired access path, or failed health check after restoration. Confirm that the workflow stops, preserves diagnostics, protects the known-good copy, records a non-secret incident reference, and escalates to the recovery authority. No failure may be recorded as a successful restore.

Where restoration exposes a suspected credential or integrity issue, follow the approval-gated rotation or incident procedure. Do not copy secrets into the backup record or repository.

### 7. Review access, retention, and recovery readiness

Perform a documented least-privilege access review covering creation, read, restore, deletion, retention-policy changes, encryption-key use, and audit review. Verify that break-glass access is approval-gated, time bounded, logged, and periodically reviewed. Confirm that deletion or retention-reduction requests follow the existing destructive-action confirmation controls.

Review the recovery runbook with the named environment owner and incident route. It must define trigger criteria, authority, preconditions, backup selection, restore steps, verification, rollback/failure handling, evidence retention, and closure conditions. Cross-reference the existing [`ROLLBACK_AND_RECOVERY_VERIFICATION.md`](ROLLBACK_AND_RECOVERY_VERIFICATION.md) for release rollback versus data recovery boundaries.

### 8. Produce the M14.9 acceptance record

The independent reviewer must confirm that the inventory, architecture approval, backup ledger, integrity verification, non-production restore evidence, RTO/RPO measurements, failure exercise, access review, and recovery runbook are complete and consistent. Open exceptions require a named owner, remediation date, risk acceptance where applicable, and explicit indication that M14.9 remains incomplete until resolved.

Update `TODO.md`, `STATE.md`, and `TASK_GRAPH.md` only after the acceptance record is approved. M14.10 may begin only when M14.9's accepted evidence is retained and M14.8 is completed.

## Work breakdown and owners

| Step | Primary owner | Independent review | Deliverable | Exit gate |
|---|---|---|---|---|
| Scope and RTO/RPO | Automation Agent | Security Agent and environment owner | Asset inventory and recovery-objective register | Owners and targets approved |
| Architecture selection | Automation Agent | Security Agent | Backup architecture and protection decision | Off-host encrypted target and access model approved |
| Backup workflow | Automation Agent | Security Agent | Bounded, auditable backup operation and backup ledger | Preflight, idempotency, capacity, and redaction checks pass |
| Integrity and retention | Security Agent | Independent verifier | Checksum/restore-readiness and retention evidence | Recovery point is available, intact, and authorized |
| Restore drill | Automation Agent | Verification Agent | Sanitized non-production restore drill record | Integrity, health, state, and smoke checks pass within objectives |
| Failure exercise | Automation Agent | Security Agent | Failure/escalation evidence | Failure remains fail-closed and known-good copy is preserved |
| Access and runbook review | Security Agent | Environment owner | Access-review record and approved recovery runbook | Least privilege and recovery authority are confirmed |
| Acceptance | Verification Agent | Orchestration Agent | M14.9 acceptance record | All gates pass or milestone remains in progress |

## Minimum evidence index

| Evidence item | Repository-safe content | Protected-system location |
|---|---|---|
| Asset inventory and RTO/RPO register | Classification, owner role, cadence, targets, and references only | Approved operational evidence store |
| Backup architecture decision | Non-secret topology, policy identifiers, and approvals | Architecture/change-management system |
| Backup ledger | Backup IDs, timestamps, checksums, sizes, status, and retention references | Backup platform audit/log store |
| Integrity verification | Checksum result, availability, decryptability outcome, and reviewer result | Backup platform / protected evidence store |
| Restore drill | Sanitized timeline, backup reference, measurements, validation outcomes, and exceptions | Incident/change and protected evidence stores |
| Access review | Roles, scopes, approvals, and review date; no secret values | Identity and backup-platform audit systems |
| Recovery runbook | Version, owners, trigger criteria, and exercise date | Repository and approved operations library |

## M14.9 completion checklist

- [ ] Every recoverable asset has an owner, classification, recovery priority, RTO, RPO, backup method, cadence, retention, and restore dependency.
- [ ] The approved backup target is encrypted, off-host, access-controlled, and monitored; repository evidence is secret-free.
- [ ] Backup operations are bounded, idempotent, auditable, and fail closed on partial or invalid results.
- [ ] Integrity verification confirms the selected recovery point exists, matches its recorded checksum/identifier, and is retrievable by an authorized recovery role.
- [ ] A controlled non-production restore meets approved RTO/RPO targets and passes integrity, health, read-only state, and smoke-workflow checks.
- [ ] A failure exercise proves diagnostics, escalation, preservation of the known-good backup, and no false-success outcome.
- [ ] Backup, restore, deletion, retention, and encryption-key access have received a least-privilege review.
- [ ] The recovery runbook and evidence index are approved by the named environment and recovery owners.
