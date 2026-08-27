# GUI-to-Engine API Contract

## Scope and ownership

This document defines the boundary between the Windows GUI and the Orville engine. The GUI is a presentation and interaction client; orchestration, policy enforcement, persistence, provider execution, verification, and artifact registration remain engine responsibilities. The contract is transport-neutral so the standalone local process and a future authenticated backend bridge can implement the same resource shapes.

The GUI must not call provider SDKs, connector APIs, browser sessions, filesystem roots, or checkpoint databases directly. It sends validated intent to the engine and renders sanitized responses. The engine remains authoritative for permissions, approval receipts, state transitions, retry limits, privacy routing, and secret redaction.

## Request and response envelope

Requests use a versioned JSON envelope:

```json
{
  "api_version": "v1",
  "request_id": "client-generated-idempotency-safe-id",
  "operation": "objective.create",
  "payload": {},
  "approval_reference": null
}
```

Responses use a stable envelope:

```json
{
  "api_version": "v1",
  "request_id": "client-generated-idempotency-safe-id",
  "status": "accepted",
  "resource": {},
  "events": [],
  "error": null
}
```

`request_id` is safe correlation metadata and must not contain secrets. Mutating requests require idempotency handling. Errors identify the failed operation, stable error class, remediation, and safe diagnostic reference; they must not return credentials, cookies, authorization headers, prompts, raw provider responses, or local secret-bearing paths.

## Resource contract

| Resource | GUI purpose | Engine authority |
|---|---|---|
| Objective | Create and inspect a user goal, constraints, deliverables, and acceptance criteria. | Intake classification, sensitive-domain handling, normalization, and validation. |
| Task graph | Show tasks, dependencies, assignments, statuses, and progress. | DAG validation, scheduling, leases, retries, and transitions. |
| Run | Start or inspect one execution of a graph. | Execution lifecycle, idempotency, cancellation, and terminal status. |
| Checkpoint | Display resumable state and recovery information. | Durable persistence, checkpoint version, restart recovery, and integrity. |
| Provider | Show configured provider availability and health. | Capability probing, privacy routing, budgets, rate limits, and fallback policy. |
| Local model | Import, inspect, pause, resume, cancel, or remove a local model registration. | File containment, provenance, approval gates, compatibility, and registration state. |
| Verification record | Show acceptance criteria, evidence, defects, and approval state. | Independent verification, evidence linkage, and final completion decision. |
| Artifact | List generated outputs, checksums, provenance, and history. | Registration, path policy, transformation history, retention, and redaction. |
| Approval | Present a consequence preview and collect a scope-matched approval reference. | Approval validity, expiry, actor, scope, and high-impact action gate. |
| Event stream | Render progress, logs, agent activity, tool calls, and state changes. | Ordering, replay, sanitization, bounded retention, and access control. |

## Resource operations

The canonical operation names are `objective.create`, `objective.inspect`, `run.create`, `run.pause`, `run.resume`, `run.retry`, `run.cancel`, `checkpoint.inspect`, `provider.list`, `provider.health`, `local_model.list`, `local_model.import`, `local_model.pause`, `local_model.resume`, `local_model.cancel`, `local_model.remove`, `verification.inspect`, `artifact.list`, `approval.inspect`, `approval.grant`, and `events.replay`. Implementations may expose these through the existing `/api/v1/...` routes or a local adapter, but the resource semantics and safety rules remain unchanged.

Read operations return sanitized resource projections. Mutating operations return `accepted` only after validation and policy checks; a high-impact operation returns `waiting_approval` until a valid approval reference is supplied. `run.pause`, `run.resume`, `run.retry`, and `run.cancel` preserve checkpoints and emit an event. They do not silently duplicate work or discard artifacts.

## State transitions and event stream

The engine owns state transitions. A GUI may request a transition but cannot set status fields directly. The stable lifecycle vocabulary includes `queued`, `running`, `paused`, `waiting_approval`, `blocked`, `partial`, `completed`, `failed`, and `cancelled`. Invalid transitions return a conflict with the current safe state and remediation.

Events are ordered by run and sequence number and include only safe metadata: event type, timestamp, task or resource identifier, status, bounded attempt number, sanitized failure class, and diagnostic reference. Event replay is bounded and resumable from a sequence cursor. The GUI must tolerate missing, delayed, duplicated, or out-of-order display updates without changing engine state.

## Authentication, authorization, and approvals

A deployed backend bridge must authenticate every request, authorize the resource and operation, validate the request body, apply CORS and rate-limit policy, and write a redacted audit record. The local standalone adapter may use the configured local trust boundary, but it must not bypass engine authorization or least-privilege grants.

Approval is separate from authentication and authorization. Operations that publish, delete, submit, change permissions, alter accounts, import/remove models, or otherwise create irreversible or high-impact effects require a valid scope-matched approval receipt. The GUI displays the consequence preview and approval state; the engine verifies the receipt immediately before execution.

## Providers, local models, artifacts, and verification

Provider responses are projected into safe availability, capability, rate-limit, and health fields. The GUI never receives API keys or raw credentials. Local-model operations use approved roots and provenance/checksum checks. Artifact projections include stable identifiers, safe names, size, media or document type, checksum, provenance reference, and verification state, but not secret-bearing paths or raw content unless the presentation policy permits it.

Verification records reference acceptance criteria and evidence identifiers. A missing provider, connector, website, or artifact leaves the workflow blocked or partial; it must not be represented as successful verification. Independent verification remains an engine decision and cannot be satisfied by a GUI acknowledgement.

## Compatibility and error contract

`api_version` is required. Additive response fields are backward-compatible; removal or semantic change requires a new version and migration note. Unknown response fields must be ignored by clients. Unknown operations, malformed payloads, stale versions, invalid transitions, missing approvals, unavailable dependencies, and rate limits map to stable error classes with operation-safe recovery guidance.

The GUI preserves user input and navigation state across errors, retries, refreshes, offline periods, and reconnects. It renders loading, empty, offline, blocked, failed, partial, and long-running states consistently. It must not retry mutating operations without an idempotency key.

## Acceptance and validation

The contract is accepted when all requested resources have documented request/response ownership; state transitions are engine-controlled; event replay is ordered, bounded, and sanitized; authentication and authorization are explicit; approval is separate from authentication; provider keys, prompts, raw responses, cookies, and sensitive paths are excluded; unavailable dependencies produce blocked or partial outcomes; and additive-version compatibility is defined.

Run the credential-free contract checks with:

```bash
python -m pytest tests/test_gui_engine_api_contract.py -q
python -m py_compile tests/test_gui_engine_api_contract.py
```

This document does not claim that a deployed backend bridge or GUI wiring is complete. Those are separate implementation items. It defines the interface boundary needed for those integrations without contacting external systems or using credentials.
