# M9 Hardened Execution Infrastructure

**Document status:** Prepared—awaiting environment owner confirmation
**Milestone:** M9
**Owners:** Automation Agent and Security Agent
**Source task:** `TASK_GRAPH.md` M9 (`blocked-by-infrastructure`)
**Author:** Manus AI
**Prepared:** 2026-08-27

## 1. Purpose and exit condition

M9 establishes an approved execution substrate for Orville workers. The substrate must provide a non-root execution identity, bounded resources, controlled network access, an explicit package policy, durable audit evidence, and a repeatable recovery path. Local mocks and deterministic adapter states are useful contract evidence, but they do not satisfy the live infrastructure gate.

M9 may move from `blocked-by-infrastructure` to accepted only when one named Linux or Windows execution target has passed the provisioning checklist, the security review, the acceptance suite, and an operator approval checkpoint. The target must be reproducible from a versioned specification and must have an identified owner for patching, credentials, logs, capacity, and incident response.

## 2. Target decision record

Complete this table before provisioning. Do not place secrets, bearer tokens, private keys, or full connection strings in this document.

| Field | Required value | Acceptance rule |
|---|---|---|
| Target ID | `[target-id]` | Stable, non-sensitive identifier |
| Target kind | `[non-root-container / VM / managed runner]` | Approved by Security and Operations |
| Host/cluster owner | `[owner/team]` | Named accountable owner |
| Orville release | `[commit/tag]` | Immutable source reference |
| Worker image/VM image | `[digest/version]` | Digest or immutable version recorded |
| Runtime identity | `[service identity]` | Non-root and least-privileged |
| Region/zone | `[region]` | Approved data boundary |
| CPU/memory/storage quotas | `[values]` | Enforced by substrate, not convention |
| Network policy | `[allowlist reference]` | Default deny; explicit egress/ingress |
| Package policy | `[lockfile/image policy]` | Reproducible and reviewed |
| Log destination | `[redacted sink ID]` | Access-controlled, retention-defined |
| Recovery owner | `[name/team]` | Can restore or terminate the target |
| Change record | `[change ID]` | Approved before execution |

## 3. Provisioning sequence

### 3.1 Approvals and immutable inputs

Record the change ID, target owner, security approver, release reference, image or VM digest, intended workload class, data classification, maintenance window, rollback target, and expiration date. Approval must identify the exact target and scope. A dry-run or plan preview is evidence of consequence only; it is not approval to provision or activate the target.

### 3.2 Host and runtime boundary

Provision a dedicated non-root container, VM, or managed runner. Disable privileged mode and host filesystem access unless an exception has a separately approved control. Set a read-only base filesystem where compatible, use an explicit writable data directory, drop unnecessary Linux capabilities, deny host-network mode, and ensure the worker cannot access the host Docker or container runtime socket.

For a Windows target, use a dedicated service identity or sandbox account, deny interactive administrator rights, restrict writable directories, and record the exact Windows Sandbox or VM policy. The identity must not inherit broad local administrator or domain administrator privileges.

### 3.3 Resource quotas and worker concurrency

Apply hard CPU, memory, process, file-descriptor, disk, and ephemeral-storage limits. Define the maximum worker concurrency, queue depth, execution duration, retry budget, and dead-letter behavior. Verify that a worker cannot raise its own quota or fork unbounded processes. Configure a safe termination path for quota exhaustion and capture the bounded reason code in the audit record.

### 3.4 Network and package policy

Apply default-deny network policy. Allow only named control-plane, artifact, telemetry, and approved provider destinations. Block metadata services, arbitrary outbound addresses, inbound public traffic, and lateral access to unrelated workloads. Store policy by reference and validate the effective policy from inside the target.

Build the image or VM from a pinned base and a reviewed dependency lock. Prohibit runtime package installation by default. If a package install is required, route it through a reviewed build process, record the package digest, and rebuild rather than mutating the live target.

### 3.5 Secrets, identity, and audit

Inject only the minimum secret references required for the selected worker profile. Do not copy credentials into source files, images, logs, prompts, test artifacts, or screenshots. Verify that the runtime sees redacted references or environment-backed values according to the existing `secrets_audit.py` contract.

Send append-only safe metadata to the approved audit sink: target ID, worker ID, policy version, run ID, step ID, timestamp, outcome, reason code, and correlation ID. Do not record prompts, bearer tokens, private keys, raw provider responses, or unnecessary personal data.

### 3.6 Health, restart, and recovery

Configure a liveness check, readiness check, startup timeout, bounded graceful shutdown, and restart policy. Verify that a crash, host restart, network interruption, quota breach, and dependency timeout leave a recoverable and auditable state. Unknown status for a non-idempotent operation must fail closed and enter review rather than being automatically repeated.

## 4. Acceptance suite requirements

Run the suite against the named target and immutable release. Every test must include target ID, run ID, policy version, timestamp, command or test reference, redacted result, reviewer, and artifact location.

| ID | Acceptance test | Pass condition | Required evidence |
|---|---|---|---|
| M9-01 | Non-root identity | Worker UID/account is not privileged; privilege escalation checks fail closed | Identity output and policy reference |
| M9-02 | Filesystem boundary | Host paths and runtime sockets are inaccessible; only approved writable paths work | Boundary test log |
| M9-03 | Capability reduction | Unneeded kernel/OS capabilities are absent | Effective capability report |
| M9-04 | CPU and memory quota | A controlled stress job is terminated or throttled at the configured bound | Quota result and reason code |
| M9-05 | Process and descriptor limits | Fork/file-descriptor exhaustion is bounded and recoverable | Limit test result |
| M9-06 | Storage quota | Disk and ephemeral storage exhaustion stops safely without corrupting evidence | Storage result and recovery check |
| M9-07 | Concurrency and queue bound | Worker concurrency and queue depth never exceed configured limits | Scheduler/queue evidence |
| M9-08 | Network default deny | Unlisted ingress, egress, metadata, and lateral destinations are denied | Effective policy probes |
| M9-09 | Approved network allowlist | Each required control-plane and telemetry destination succeeds; no extra destination succeeds | Allowlist matrix |
| M9-10 | Package immutability | Runtime package installation is denied or separately audited; deployed digest matches record | Image/lock verification |
| M9-11 | Secret isolation | Secrets are available only through approved references and absent from logs/artifacts | Redacted scan and audit record |
| M9-12 | Audit integrity | Required safe metadata is append-only, correlated, and queryable by run ID | Audit read-back |
| M9-13 | Restart recovery | Worker restart preserves idempotency and returns to a known state | Restart timeline |
| M9-14 | Dependency timeout | Provider/control-plane timeout produces bounded retry or dead-letter behavior | Timeout evidence |
| M9-15 | Crash recovery | Forced worker crash is detected, recovered, and not duplicated unsafely | Crash/recovery record |
| M9-16 | Patch/rebuild reproducibility | Rebuilding from the pinned specification yields the declared digest or approved diff | Build attestation |
| M9-17 | Access review | Only named operators and service identities can administer, inspect, or retrieve evidence | Access review record |
| M9-18 | Termination and rollback | Target can be disabled and restored to the recorded baseline without orphaned credentials | Rollback evidence |

## 5. Acceptance rules

All M9-01 through M9-18 tests are mandatory unless a named exception is approved. A failed test blocks acceptance. An unavailable provider, missing host capability, unverifiable policy, or incomplete evidence is a failure or `blocked`, not a pass. Tests may use synthetic workloads and test data, but the target boundary and enforcement must be live.

The Security Agent independently reviews identity, isolation, network, package, secret, and audit evidence. The Automation Agent reviews worker lifecycle, quotas, retry behavior, recovery, and rollback evidence. The operator records the final decision in an approval checkpoint with the target ID, release reference, policy version, and bounded reason.

## 6. Rollback and incident controls

If provisioning or acceptance causes an unexpected effect, stop new work, disable the target, preserve safe audit metadata, and route active work to the existing safe fallback. Do not destroy logs or evidence during rollback. Revoke target-specific credentials, restore the last approved image or VM snapshot, verify access boundaries again, and open a new change record for any corrective rebuild.

A target with unknown execution status must not be reused for non-idempotent work until reconciliation is complete. The incident record must identify the last known checkpoint, affected run IDs, evidence preserved, containment action, recovery result, and reviewer.

## 7. Completion record

| Field | Value |
|---|---|
| Target ID | `[target-id]` |
| Release/image digest | `[immutable reference]` |
| Acceptance run ID | `[run-id]` |
| Tests passed | `[18/18 or approved exception]` |
| Tests failed/blocked | `[IDs and reasons]` |
| Security reviewer | `[identifier]` |
| Automation reviewer | `[identifier]` |
| Operator approver | `[identifier]` |
| Approval checkpoint | `[checkpoint ID]` |
| Evidence manifest | `[safe path or artifact ID]` |
| Decision | `[accepted / rejected / blocked]` |
| Follow-up actions | `[items and owners]` |

## References

- [`TASK_GRAPH.md`](../TASK_GRAPH.md), M9 task definition and current blocker status.
- [`APPROVAL_CHECKPOINTS.md`](APPROVAL_CHECKPOINTS.md), approval, evidence, and fail-closed controls.
- [`READINESS_REPORT.md`](READINESS_REPORT.md), current environment-owned readiness boundaries.
- [`CLEAN_ENVIRONMENT_VALIDATION.md`](CLEAN_ENVIRONMENT_VALIDATION.md), credential-free validation boundaries.
- [`M14_8_NONPRODUCTION_CHANGE_PACKAGE.md`](M14_8_NONPRODUCTION_CHANGE_PACKAGE.md), downstream canary change-control pattern.
- [`M14_9_BACKUP_RECOVERY_EXECUTION_PLAN.md`](M14_9_BACKUP_RECOVERY_EXECUTION_PLAN.md), downstream recovery-control pattern.

_Last updated by Manus AI._
