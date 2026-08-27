# Scheduled Workflow Idempotency and Retry Safety

## Contract

Each scheduled occurrence is identified by the deterministic key `schedule:<schedule_id>:<scheduled_slot>`. The workflow store uses that key as a unique idempotency boundary, and the schedule store uses a deterministic execution record for the same occurrence. Re-delivery of a completed occurrence returns the existing completed run and does not execute workflow steps again.

## Lifecycle

1. The scheduler claims the enabled schedule with a bounded lease. Claiming records the lease owner and expiry but does **not** advance `next_run_at`.
2. The dispatcher derives the occurrence idempotency key from the schedule ID and unchanged scheduled slot, then creates or reloads the execution record.
3. A running or failed occurrence may execute once for the current attempt. A completed occurrence is treated as authoritative and is not executed again.
4. On success, the dispatcher marks the workflow and execution completed, advances `next_run_at`, and releases the lease.
5. On failure, the dispatcher records a bounded error and releases the lease without advancing `next_run_at`. The same scheduled occurrence can therefore be retried with the same idempotency key.
6. Lease recovery permits another worker to retry after the previous lease expires. Concurrent workers cannot claim the same schedule while a different valid lease is held.

## Safety requirements

| Requirement | Contract |
|---|---|
| Idempotency | Use the schedule ID plus scheduled slot; do not use a random retry key. |
| Duplicate completion | Return the existing completed run and skip handlers. |
| Failure retry | Keep the scheduled slot due and reuse its idempotency key. |
| Lease safety | Require an enabled schedule and reject a valid lease owned by another worker. |
| Schedule advancement | Advance only after successful completion. |
| Error handling | Persist a bounded error, preserve the occurrence record, release the lease, and allow a later retry. |
| Side effects | Workflow steps must be independently idempotent for provider or connector operations; the dispatcher cannot make non-idempotent external APIs safe by itself. |

## Operational boundaries

The dispatcher owns durable run and execution identity. `ScheduleStore` owns leases and schedule timing. Workflow handlers own their provider-side idempotency keys, transaction boundaries, and external compensation. Approval-gated steps remain approval-gated on every attempt. A retry must not bypass authorization, expose credentials, or infer success from an untrusted response.

## Validation

Run the focused checks from the repository root:

```powershell
python -m unittest tests.test_scheduled_idempotency -v
python -m py_compile orville_core\scheduler.py orville_core\automation.py tests\test_scheduled_idempotency.py
```

The tests verify failed-occurrence retry with one durable run and execution record, completed-occurrence deduplication, preserved leases, and single handler execution for a completed occurrence. They use synthetic local handlers and do not call external services.

## Known limitations

The current contract does not implement provider-specific idempotency headers or distributed locks beyond the SQLite schedule lease. External handlers must supply their own idempotency or compensation behavior. Catch-up policy for multiple missed intervals and operator-configurable retry backoff remain separate scheduling work.
