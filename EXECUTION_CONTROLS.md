# Orville Execution Controls

## Scope

This increment adds durable controls for conditional tasks, approval gates, cancellation requests, idempotency reuse, per-task timeouts, and exclusive output ownership. The controls are designed to preserve the existing checkpoint and resume contract.

## Conditional tasks

A task may specify a deterministic condition in `inputs["when"]` using a dotted context key and an expected value.

```python
TaskNode(
    "deploy",
    "Deploy",
    "deploy_handler",
    inputs={"when": {"key": "approval.production", "equals": True}},
)
```

When the condition is false, the task is marked `skipped`, its result is persisted, and the run can complete if all remaining tasks reach a terminal state. Arbitrary expressions are not evaluated.

## Approval gates

Set `approval_required=True` on a task to pause execution before the handler starts. The engine persists `waiting_approval` and emits `approval_required`. An authorized caller can call `engine.approve(run_id, task_id)` and resume the run. Approval state is persisted in the checkpoint.

## Cancellation

Cancellation can be requested by calling `engine.cancel(run_id)`. The request is persisted. The next execution boundary marks unfinished tasks as cancelled and records `run_cancelled`. Long-running handlers should additionally implement cooperative cancellation through their context or runtime-specific cancellation mechanism.

## Idempotency

Set `idempotency_key` on a task when a repeated execution must reuse a prior result. Cached values are stored under `context.idempotency`; a matching value produces a `task_idempotency_reused` event and does not invoke the handler again.

## Timeouts

Set `timeout_seconds` to enforce a handler completion deadline. A timeout becomes a persisted task failure and follows the normal retry policy. Python thread cancellation cannot forcibly stop code that ignores cancellation, so production handlers must use cooperative cancellation and external process isolation where hard termination is required.

## Ownership conflicts and required inputs

`owned_paths` declares files or resource paths a task may modify. Tasks that claim paths must now specify a non-empty `owner`, and graph validation rejects duplicate ownership claims before execution. A task may also declare `required_inputs`; every declared input must be present in the task input map before execution. This is a static check; future parallel scheduling must also enforce dynamic locks, branch merge rules, and post-task conflict detection.

```python
TaskNode(
    "implement",
    "Implement change",
    "code_handler",
    inputs={"workspace": "/repo"},
    required_inputs=["workspace"],
    owned_paths=["src/main.py"],
    owner="code",
)
```

## Clarification gates

`TaskIntake.clarification_gate()` distinguishes incomplete planning information from hard execution gates. Missing deliverables, acceptance criteria, or target environment are returned as warnings. Sensitive actions such as deployment, publication, credential handling, financial operations, destructive changes, and external messaging produce a hard gate. Explicitly conflicting requirements also produce a hard gate. Objective intake persists the gate in graph inputs and returns it to callers without silently performing the gated action.

The gate is deterministic and advisory at intake; execution handlers and approval controls remain responsible for enforcing the corresponding authorization before an external or destructive operation.

## Current limitations

Scheduling remains sequential. Conditional branches, approval gates, idempotency, and timeouts are implemented, but parallel execution, hard process termination, authorization policy enforcement, dynamic file locks, conditional graph expansion, and distributed leases remain future work.

## Verification

```bash
python -m compileall -q orville_core tests examples
python -m unittest discover -s tests -v
```

The current suite passes 182 tests, with one existing HTTP-client deprecation warning from the FastAPI test client dependency.
