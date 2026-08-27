# Workload Classification

## Purpose

Every automated Orville task must be classified before execution planning. Classification selects the lifecycle owner, trigger adapter, idempotency and replay controls, observability expectations, and shutdown behavior. Classification is descriptive and deterministic; it does not execute a task, create a schedule, accept a webhook, or authorize an external action.

## Workload classes

| Class | Meaning | Primary trigger or lifecycle | Required controls | Owner |
|---|---|---|---|---|
| `one_shot` | A single bounded run initiated manually or by an explicit command. | Manual request or no trigger. | Objective, input boundary, result status, and optional idempotency key for retries. | Interactive client or one-shot runner. |
| `recurring` | A workflow that runs repeatedly according to a schedule. | Cron, interval, or schedule expression. | Schedule expression or interval, idempotency key, lease/claim, retry policy, and missed-run policy. | Scheduler and workflow dispatcher. |
| `event_triggered` | A workflow started by an external, data, connector, or task event. | Event, data, connector, or task-event trigger. | Event source, stable deduplication key, bounded payload, replay policy, and event audit record. | Event intake adapter and dispatcher. |
| `webhook_driven` | A workflow started by an inbound HTTP webhook. | Authenticated webhook request. | Webhook source, signature verification policy, replay protection, bounded payload, response contract, and event audit record. | Webhook intake adapter and dispatcher. |
| `persistent_service` | A long-running service that remains active between individual task executions. | Service lifecycle, daemon, worker, or explicit persistent-runtime requirement. | Health checks, restart policy, shutdown behavior, bounded resources, durable state, and operator-visible lifecycle status. | Service supervisor and runtime health controller. |

`webhook_driven` is intentionally separate from the broader `event_triggered` class because inbound HTTP authentication, signature validation, replay protection, and response timing are distinct controls. A service may also consume schedules or events, but `persistent_service` takes precedence when the specification requires a persistent runtime.

## Deterministic classification contract

The public API is `orville_core.agent_contracts.classify_workload`. It accepts an `AutomationSpec` or a mapping with equivalent fields and returns a `WorkloadClassification` containing `workload_type`, a stable reason, and the controls required for planning.

The classifier applies this precedence:

1. `requires_persistent_runtime=True` or `trigger_config.persistent_service=True` produces `persistent_service`.
2. `trigger_type="schedule"` produces `recurring`.
3. `trigger_type="webhook"` produces `webhook_driven`.
4. `trigger_type` in `event`, `data`, `connector`, or `task_event` produces `event_triggered`.
5. `trigger_type="manual"` or an omitted trigger produces `one_shot`.
6. An unsupported trigger or explicit workload type fails closed with `ContractError`.

An explicit `workload_type` is permitted for serialized task specifications, but it must agree with the inferred trigger and runtime requirements. Conflicting declarations fail closed rather than silently selecting an unsafe lifecycle. The existing `AutomationSpec` validation remains authoritative for schedule expressions, event sources, approval requirements, and persistent-runtime health checks.

## Planning and execution rules

Classification must occur before selecting a scheduler, event intake adapter, worker process, or deployment target. The classifier must not inspect provider response text as instructions, persist secrets, or make authorization decisions. Approval-gated steps remain approval-gated regardless of workload class.

The dispatcher owns durable run creation and idempotency. The scheduler owns lease and recurring-run timing. Event intake owns signature, replay, and duplicate handling. A persistent supervisor owns health and shutdown. The GUI may display the classification and its required controls, but it must not mutate durable workflow state or bypass these owners.

## Examples

```python
from orville_core import AutomationSpec, classify_workload

one_shot = classify_workload(
    AutomationSpec(objective="Generate a release note", trigger_type="manual")
)
assert one_shot.workload_type == "one_shot"

recurring = classify_workload({
    "trigger_type": "schedule",
    "trigger_config": {"expression": "0 9 * * 1-5"},
})
assert recurring.workload_type == "recurring"

webhook = classify_workload({
    "trigger_type": "webhook",
    "trigger_config": {"source": "approved-git-provider"},
})
assert webhook.workload_type == "webhook_driven"

service = classify_workload({
    "trigger_type": "event",
    "trigger_config": {"source": "local-queue", "persistent_service": True},
})
assert service.workload_type == "persistent_service"
```

## Validation checklist

- [ ] The workload type is one of the five supported values.
- [ ] Trigger and runtime signals produce the documented deterministic class.
- [ ] Conflicting explicit and inferred classes fail closed.
- [ ] Required controls are surfaced before execution planning.
- [ ] Recurring work uses scheduler leases and idempotency keys.
- [ ] Event and webhook work uses deduplication and replay controls.
- [ ] Persistent services define health checks, restart policy, bounded resources, and shutdown behavior.
- [ ] The classifier performs no network calls, scheduling, task creation, or external side effects.

## Related contracts

- `orville_core/agent_contracts.py`
- `orville_core/automation.py`
- `orville_core/scheduler.py`
- `docs/ORVILLE_MANUS_WORKER.md`
