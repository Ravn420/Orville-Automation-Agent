# Memory and Idempotency Governance

## Scope

Orville keeps **short-term task memory** and **long-term project memory** separate from task prompts, execution checkpoints, and raw provider payloads. Memory is local-first, JSON-serializable, redacted before persistence, bounded in size, and addressed by an explicit `(scope, owner_id, key)` tuple.

| Memory class | Owner boundary | Intended lifetime | User controls |
|---|---|---|---|
| Task memory | One task or run | Short-lived; optional TTL up to one year | Inspect, replace, and delete |
| Project memory | One project | Long-lived until replaced or deleted | Inspect, replace, retention-plan, and delete |

## Rules

1. **Isolation:** A task can read only its own task memory, and a project can read only its own project memory. The store does not provide cross-owner search or fallback lookup.
2. **Redaction:** Values pass through `SecretRedactor` before JSON serialization. Credentials, bearer tokens, cookies, and raw authorization material must not be stored.
3. **User editing:** `put` replaces one named key for the same owner and preserves its stable memory identifier. Deletion requires the owner identifier and is a tombstone operation.
4. **Retention:** A caller may set a bounded TTL. `retention_plan` is non-destructive and reports expired candidates. `purge_expired` is the explicit destructive maintenance action and never runs implicitly during reads.
5. **Boundaries:** Values are capped at 100,000 encoded bytes. Scope, owner, key, and source are bounded and validated. Unsupported or non-JSON values are rejected.
6. **Privacy:** Deleted records and expired records are not returned by active reads. Inspection returns only the selected owner’s safe projection.

## Recovery and event history

The existing `OrchestrationEngine` persists pause, resume, cancellation, retry, approval, operation-checkpoint, replay, and controlled state-inspection evidence in durable run checkpoints. The authenticated API exposes bounded polling and resumable SSE event delivery. Events are ordered by monotonic sequence, categorized for task/agent/tool/model/approval/artifact activity, sanitized, and replayable from a cursor. A reconnecting client must reconcile against the final checkpoint rather than treating an event as authorization or proof of an external side effect.

## Idempotency and deduplication

Workflow runs require an idempotency key and persist a unique key constraint. Scheduled dispatch derives a stable key from the schedule identifier and scheduled run time; inbound events are deduplicated by event identifier; event streams use sequence as the display deduplication key; artifact manifests retain a new version only when the content hash changes; operation checkpoints use deterministic identifiers. External handlers must still provide provider-specific idempotency or compensation because Orville cannot prove a remote side effect from a local response alone.

## Verification

The memory store is implemented in `orville_core/memory.py` and exposed through `orville_core.MemoryStore`. Focused tests are in `tests/test_memory.py`. Recovery, event, checkpoint, scheduler, and workflow idempotency coverage remains in `tests/test_recovery_controls.py`, `tests/test_realtime_execution_events.py`, `tests/test_operation_checkpoints.py`, `tests/test_scheduler.py`, and `tests/test_scheduled_idempotency.py`.

Run:

```bash
python -m pytest -q tests/test_memory.py tests/test_recovery_controls.py tests/test_realtime_execution_events.py tests/test_scheduled_idempotency.py tests/test_operation_checkpoints.py
python -m pytest -q
```

These checks are local and credential-free. They do not authorize provider calls, publication, deployment, account changes, or deletion outside the explicit memory maintenance method.

## References

[1]: ../orville_core/memory.py "Durable memory implementation"
[2]: ../tests/test_memory.py "Memory governance tests"
[3]: REALTIME_EXECUTION_EVENTS.md "Realtime execution event contract"
[4]: SCHEDULED_WORKFLOW_IDEMPOTENCY.md "Scheduled workflow idempotency contract"
[5]: OPERATION_CHECKPOINTS.md "Durable operation checkpoints"
[6]: ../orville_core/engine.py "Orchestration engine recovery controls"
