# Upcoming Sprint Backlog

**Planning horizon:** Next sprint
**Planning baseline:** `fix/regression-contracts` at `9387f42`; full regression baseline of 784 passed tests and 6 passed subtests.
**Purpose:** Convert the broad project TODO inventory into a bounded, dependency-aware sprint backlog. This document is a plan, not authorization for provider, identity, credential, deployment, browser, or destructive operations.

## Backlog Inventory and Planning Rule

The current TODO inventory contains 437 open checklist records, 13 in-progress records, and 14 blocked records. Those totals include future product epics, reusable execution-record placeholders, and external-gated work; they are not a single sprint backlog.

The sprint is prioritized by safety, dependency unlock, current ownership, and verification value. Existing active owners retain their assigned paths. A task requiring a provider account, identity tenant, credential, live host, external support request, destructive cleanup, or production-adjacent action is either preparation-only or blocked until explicit authorization and required inputs exist.

| Backlog class | Count | Sprint treatment |
|---|---:|---|
| Open | 437 | Select only bounded, prerequisite-aligned work packages. |
| In progress | 13 | Finish or explicitly hand off before parallelizing dependent work. |
| Blocked | 14 | Do not start without the named external approval or environment. |
| Reusable template placeholders | 5 of the blocked records | Exclude from sprint capacity; they are intentionally incomplete form fields. |

## Priority 0: Finish Existing Active Work

| Task ID | Work item | Current state | Owner | Sprint action | Completion evidence |
|---|---|---|---|---|---|
| `TODO-175df4cecc51` | Support replay, resume, pause, cancellation, retry, and controlled state inspection after interruption or failure. | In progress; Worker Task 2. | Existing worker owner | Continue only under the current assignment; do not create a competing implementation. | Focused recovery tests, full regression, handoff record, and status update. |
| `TODO-2b113eb0e255` | Stream graph, agent, tool, model, approval, and artifact events to the GUI with durable auditable history. | In progress; Worker Task 1. | Existing worker owner | Continue only under the current assignment; coordinate dependent task-thread work first. | Event-category coverage, durable audit evidence, UI contract tests, full regression, and handoff record. |
| `TODO-1313e3035aa4` | Route model inspection, conversion, loading, and execution through selected sandbox policy. | In progress locally. | Existing security/runtime owner | Continue on current owned paths; do not substitute unsupported live execution for local controls. | Boundary/failure tests and updated limitation evidence. |

These three tasks consume the available immediate integration capacity. The next sprint should not initiate work that overlaps their persistence, event, sandbox, or state-transition paths without an explicit ownership decision.

## Priority 1: M14.8 Readiness Evidence

M14.8 is **preparation complete but execution blocked**. The change-window template and live-drill procedure are ready for target-specific completion; no live drill is authorized by this plan.

| Task ID | Dependency or work package | Current state | Sprint action | Entry criterion | Exit criterion |
|---|---|---|---|---|---|
| `TODO-d57bb88a5510` | M14.2 trust-root ceremony | Local workflow implemented; live ceremony pending. | Obtain an approved non-production ceremony slot and complete the evidence table. | Named security owner, target, and operator approval. | Pinned digest, rotation/revocation/recovery evidence, and independent review. |
| `TODO-645712e7e866` | M14.3 live sandbox validation | Local controls pass; supported runtime hosts unavailable. | Secure a supported Windows Sandbox host and a Linux host with `bwrap`; plan host-specific validation only. | Named supported hosts and approved non-production workload. | IPC, resource, boundary, timeout, output, and cleanup evidence on both hosts. |
| `TODO-c5e611cb20ff` | M14.4 identity evidence | Local contract implemented; live identity integration pending. | Define the approved non-production identity target, test tenant, issuer/audience configuration, and revocation test plan. | Identity owner and non-production tenant. | Tenant isolation, least privilege, revocation, and audit evidence. |
| M14.5 external evidence | Secret manager/workload identity | Local contract complete; enterprise evidence pending. | Provision reference-only non-production secret access and schedule rotation/access-review exercise. | Approved secret manager and workload identity. | Sanitized rotation, redaction, and access-review evidence. |
| M14.6 external evidence | Provider-specific deployment adapter | Local adapter contract complete; provider selection pending. | Select the provider and execute the approved dry-run preparation sequence. | Provider decision, non-production target, and identity path. | Dry-run/status/traffic split/pause/rollback/timeout/idempotency evidence. |
| M14.7 external evidence | Production metrics and health source | Local metrics contract complete; monitoring source pending. | Configure scoped non-production metrics and fail-closed no-data check. | Target telemetry source and alert route. | Freshness, completeness, cohort scope, business/security metric, and alert evidence. |
| `TODO-45ea939505f7` | M14.8 non-production canary and rollback drill | In progress, local planning only. | Populate `M14_8_CHANGE_WINDOW_AUTHORIZATION_TEMPLATE.md`; do not execute until every prerequisite is complete and explicitly approved. | All M14.2–M14.7 evidence accepted. | Approved drill results for restart, duplicate event, partial failure, release-health fault, rollback failure, and deterministic recovery. |

## Priority 2: Durable Task-Thread Vertical Slice

Begin this package only after Worker Tasks 1 and 2 complete, or after their owners explicitly reserve non-overlapping paths. This sequence builds a coherent capability rather than scattering unintegrated models across the codebase.

| Order | Task ID | Bounded deliverable | Dependency | Verification |
|---:|---|---|---|---|
| 1 | `TODO-6fa537929800` | Durable `TaskThread` model with stable IDs, lifecycle metadata, and recovery fields. | Ownership agreement with active event/recovery work. | Persistence, migration, and restart tests. |
| 2 | `TODO-3cbf6cb3907b` | Append-only `TaskMessage` model with safe event categories and artifact/citation references. | Durable thread identity. | Ordering, redaction, and restart tests. |
| 3 | `TODO-498262667bdc` and `TODO-74491cf31575` | Explicit status and stop-reason transitions. | Thread/message models. | Invalid-transition and recovery tests. |
| 4 | `TODO-2f7fd076f533` | Controlled task-message, detail, stop, resume, and retry operations. | Lifecycle transitions and approval boundary. | API/GUI contract, authorization, and idempotency tests. |
| 5 | `TODO-91309b9bf064` and `TODO-d436adee1bc5` | Restart-safe event history and optimistic concurrency protection. | Operations and append-only history. | Duplicate-action and concurrent-update regression tests. |

## Priority 3: Deferred Foundation and Product Epics

The following areas remain open but are intentionally not scheduled until the active work and M14 evidence work have reliable owners and scope. They should be refined as separate proposals, not added as unbounded sprint commitments.

| Area | Representative TODO IDs | Why deferred |
|---|---|---|
| Memory governance | `TODO-3108982ea7c3` | Requires durable task/thread data model and retention decision. |
| Model import and safety | `TODO-8b7695ad413d`, `TODO-8481cc10aeb5`, `TODO-c5619fe172c0` | Requires agreed activation, sandbox, and provenance architecture. |
| Threat model and authorization hardening | `TODO-500f367e0031`, `TODO-ab2076f7c0e6`, `TODO-2d201b75cc07` | Should follow a named risk register and architecture boundary review. |
| Evaluation and observability | `TODO-37bc97abee20`, `TODO-06227efe167c`, `TODO-5b61f3b41e3b` | Depends on durable thread/event model and redaction policy. |
| Accessibility and visual review | `TODO-14c0bd31a6ac`, `TODO-2db4ae3a211f`, `TODO-e8414ae5261d` | Requires stable user-facing workflow and design-state definition. |
| Connector, schedule, webhook, and structured-output epics | `TODO-9584124bc31d`, `TODO-a925a97a87a0`, `TODO-b7580c1bcccb`, `TODO-f9cae5b47aa8` | Large independent product initiatives with external authorization and security implications. |
| Browser, GUI, media, packaging, and parity epics | Multiple TODO records from sections 13–19 | Need a distinct user-approved product objective and capacity allocation. |

## Explicitly Blocked or Excluded

| Item | Blocker | Required action before planning work begins |
|---|---|---|
| Blackbox OAuth/device authorization | No verified official third-party flow; support contact is not authorized. | Obtain official documentation or explicit approval to submit a support request. |
| Obsolete asset cleanup | Destructive action requires named-path scope and retention review. | Provide explicit scoped deletion approval. |
| M13.15 / M14 provider operations | No approved provider, environment, credentials, or operator authorization. | Select provider and approve non-production integration scope. |
| M14.9, M14.10, M14.11 | Dependent on uncompleted environment, identity, live drill, and recovery gates. | Complete documented dependencies; do not schedule early. |

## Sprint Exit Criteria

The sprint is complete when the active worker tasks are either verified and closed or have a documented handoff; the M14.8 authorization request has a complete dependency evidence table or a clear no-go record; any accepted durable task-thread slice has focused tests and a full regression result; the full suite remains green; and all changed control files accurately distinguish local contracts from live external evidence.
