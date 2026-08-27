# Workflow Dry-Run Mode

## Purpose

Dry-run mode lets Orville validate workflow sequencing and preview external mutations without executing those mutations. It is a preview and safety boundary, not an approval, a deployment, a remote health check, or proof that an external operation would succeed.

## Execution contract

Call `WorkflowExecutor.execute(..., dry_run=True)` when a workflow may mutate external state. Each mutating step must declare `mutates_external_state=True` in its step configuration. In dry-run mode, that step is not sent to its handler; instead, the executor returns a redacted preview record in `dry_run_actions`:

```python
{
    "step_id": "publish",
    "kind": "publish",
    "executed": False,
    "requires_approval": True,
    "reason": "external side effects are disabled in dry-run mode",
}
```

Safe local steps continue to run so that validation, transformation, planning, and dependency checks can be exercised. The result contains `_dry_run=True`. A mutating step with no registered handler can still be previewed because dry-run must not require a provider or network boundary for the preview itself.

## Safety rules

| Rule | Required behavior |
|---|---|
| Mutation declaration | Mark provider calls, writes outside the approved local workspace, publication, deployment, deletion, connector mutation, and other external side effects with `mutates_external_state=True`. |
| Preview behavior | Skip the mutating handler and return a stable action preview; do not fabricate success output. |
| Approval | Dry-run does not satisfy approval. Normal execution still requires explicit approval for `requires_approval=True` steps. |
| Credentials | Do not load or transmit provider credentials solely for preview. Redact sensitive configuration from any displayed or persisted preview. |
| Filesystem | Use read-only inspection or an approved temporary workspace; never write user data as part of preview. |
| Network | Do not call external providers, webhooks, deployment targets, or connectors from a dry-run handler. |
| Retry | A dry run does not consume a production retry budget or create a remote idempotency record. |
| Reporting | Distinguish `planned`, `skipped_in_dry_run`, `executed`, `failed`, and `blocked` states. Never label a skipped mutation as completed. |

## Workflow design

Classify the workload before execution using `docs/WORKLOAD_CLASSIFICATION.md`. For scheduled workflows, combine dry-run with the scheduled idempotency contract, but do not advance the schedule or consume an external occurrence merely because a preview completed. For webhook-driven workflows, validate signature and schema locally only when the validation boundary is explicitly read-only; do not acknowledge an external delivery as processed solely because its preview passed.

The GUI and API should expose a clear preview indicator, the planned action count, the reason each mutation was skipped, and the next permitted action. Switching from dry-run to live execution is a separate user action subject to the existing approval, authorization, idempotency, and confirmation contracts.

## Command and test example

```python
from orville_core.automation import WorkflowExecutor, WorkflowStep

steps = (
    WorkflowStep("plan", "local_plan"),
    WorkflowStep("publish", "publish", {"mutates_external_state": True}, requires_approval=True),
)
preview = WorkflowExecutor({"local_plan": lambda _payload: {"ready": True}}).execute(
    steps,
    {},
    dry_run=True,
)
assert preview["_dry_run"] is True
assert preview["dry_run_actions"][0]["executed"] is False
```

Run focused validation from the repository root:

```powershell
python -m unittest tests.test_workflow_dry_run -v
python -m py_compile orville_core\automation.py tests\test_workflow_dry_run.py
```

Tests use synthetic local handlers and do not contact external services or use credentials.

## Limitations and operator checklist

Dry-run cannot prove provider availability, permission, quota, payload acceptance, or deployment success. Handlers must still be designed to be idempotent and safe to retry in live execution. Before live execution, confirm the target, affected resources, approval record, credentials boundary, idempotency key, rollback or compensation plan, and final user-facing consequence preview.

- [ ] Every external mutation is explicitly marked.
- [ ] Safe local validation steps are deterministic and bounded.
- [ ] Preview output contains no credentials, raw tokens, or sensitive payloads.
- [ ] Mutating handlers are not called in dry-run mode.
- [ ] Approval and confirmation are required again for live execution.
- [ ] Live execution has idempotency, retry, audit, and recovery controls.
