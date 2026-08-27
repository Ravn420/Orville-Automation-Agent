# Long-Running Job State and Restart Recovery

## Scope and decision

Orville persists long-running workflow state in the authoritative local storage layer, using transactional records rather than process memory. The current SQLite workflow and scheduler stores are the local reference implementation. A worker restart must reconstruct active work from durable records and must not infer completion from an in-memory queue, GUI state, or provider response alone.

## Durable record model

| Record | Required fields | Owner |
|---|---|---|
| Workflow run | `run_id`, workflow/version identity, tenant/project scope, lifecycle status, attempt, idempotency key, created/started/finished timestamps | Orchestration store |
| Task checkpoint | `run_id`, `task_id`, dependency status, owner, attempt, input/output references, checkpoint sequence, status, safe error class | Orchestration store |
| Event cursor | `run_id`, event sequence, event type, safe payload reference, created timestamp | Event/state store |
| Execution lease | `run_id`/`task_id`, worker ID, lease generation, acquired/renewed/expiry timestamps | Scheduler/dispatcher |
| Artifact reference | `run_id`, relative artifact path, checksum, provenance/version, retention state | Artifact storage |
| Recovery record | run/task ID, detected interruption, prior lease, recovery decision, operator/retry reference, timestamp | Orchestration and audit store |

Prompts, credentials, bearer tokens, raw provider responses, and unbounded payloads are not stored in recovery metadata. Durable records keep references, bounded safe error classes, checksums, and redacted diagnostics according to the repository security boundary.

## State machine

```text
queued -> leased -> running -> checkpointed -> completed
                         |          |
                         |          +-> retry_wait -> leased
                         +-> blocked -> queued or cancelled
                         +-> failed -> retry_wait or dead_letter
                         +-> cancelled

running/checkpointed --restart reconciliation--> interrupted
interrupted -> leased (if lease expired and retry is safe)
interrupted -> blocked (if approval or dependency is required)
interrupted -> completed (only after durable completion evidence)
interrupted -> failed (if recovery validation fails)
```

A state transition is committed atomically with its checkpoint sequence and event record. Terminal states are immutable except for additive verification, notification, or audit metadata. Unknown or malformed states fail closed to `blocked` and require operator review.

## Checkpoint and lease rules

Before a worker performs a non-idempotent step, it records a durable lease and attempt identity. During execution it renews the lease within a bounded interval and writes a checkpoint after each independently recoverable step. A checkpoint includes only references to inputs/outputs and a safe result summary. Lease ownership is exclusive by generation; a stale worker cannot overwrite a newer generation. The existing scheduler lease and completed-occurrence idempotency rules remain prerequisites for recurring dispatch.

## Restart reconciliation

On startup, the supervisor loads non-terminal runs and compares their leases and checkpoint sequences with the current clock and durable event log. It clears only expired leases, records an `interrupted` recovery event, and resumes only from the latest verified checkpoint. It never replays a completed step solely because the process restarted. If a step’s external side effect cannot be proven idempotent, reconciliation moves the task to `blocked` and requests review rather than repeating it.

Recovery is deterministic: the same durable records, clock input, and policy version produce the same recovery decision. Reconciliation is bounded, repeatable, and safe to run more than once; recovery records use a deduplication key so a restart storm cannot create duplicate retries or notifications.

## Retention and cleanup

Active and interrupted runs retain checkpoints, event cursors, artifact references, and audit records until terminal disposition and the configured retention period. Cleanup must preserve the latest checkpoint and verification evidence. Temporary payloads, caches, and worker-local files are not recovery state and belong under the repository’s temporary/runtime data policy.

## Acceptance checks

A conforming implementation must persist non-terminal state, task checkpoints, event cursors, leases, idempotency identity, artifact references, and recovery decisions; perform atomic state/event updates; reject stale lease writes; reconcile expired leases after restart; resume only from verified checkpoints; avoid duplicate completed side effects; preserve blocked/approval states; and record safe recovery evidence. Focused tests cover the contract. Runtime supervisor implementation, crash injection, multi-process lease tests, and production storage durability remain follow-up gates.
