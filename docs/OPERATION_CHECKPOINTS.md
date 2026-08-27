# Durable Operation Checkpoints

Orville persists secret-safe operation checkpoints before and after material workflow operations. The records are stored with the run checkpoint and survive process restart through the existing atomic checkpoint store.

Each record contains a deterministic checkpoint identifier, task identifier, operation kind, phase (`before` or `after`), status, attempt number, and monotonic sequence. Operation kinds are `agent`, `tool`, `model`, `approval`, `artifact`, and the generic `task`. Payloads, prompts, credentials, local paths, and raw exceptions are not copied into the operation record.

| Boundary | Before record | After record |
|---|---|---|
| Agent, tool, model, or artifact handler | `running` | `succeeded` or `failed` |
| Approval-gated operation | `waiting_approval` | `approved`, followed by execution records |
| Parallel operation | One `running` record per task before dispatch | One terminal record per task after merge |

A before record is persisted before handler invocation. The after record is persisted with the next checkpoint save after successful or failed completion. Approval resolution appends its after record before resumed execution. Existing idempotency, approval, dry-run, verification, and cancellation controls remain authoritative.

Checkpoint schema version 2 adds `operation_checkpoints` while readers continue to accept schema version 1 files with an empty operation-record list. Operation checkpoint records are exposed through `orville_core.OperationCheckpoint` and are validated by `tests/test_operation_checkpoints.py`.

The contract is local-first and does not call external services. It supports auditability and restart inspection but does not by itself claim that an external provider operation was committed; provider-specific idempotency and reconciliation remain required for external side effects.
