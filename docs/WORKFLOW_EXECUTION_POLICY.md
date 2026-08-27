# Workflow Execution Policy

Orville separates workflow steps by execution ownership. Steps default to `deterministic` mode and use the ordinary registered handler map. A step may declare `execution_mode: agentic` when its behavior is exploratory or generative and an explicit agentic handler is registered for that step kind.

The following safety categories require deterministic implementations:

| Category | Required behavior |
|---|---|
| `safety_critical` | Deterministic policy and bounded operation |
| `authorization` | Deterministic permission and approval enforcement |
| `validation` | Deterministic input, boundary, and acceptance checks |
| `persistence` | Deterministic durable state and checkpoint writes |
| `artifact_integrity` | Deterministic registration, checksum, and provenance handling |

`validate_workflow_steps` runs before workflow-version persistence and again before execution. An agentic step in a protected category is rejected with `PermissionError`, and an unknown execution mode is rejected with `ValueError`. These checks occur before a handler is invoked. An agentic step without a registered agentic handler fails closed rather than falling back to a deterministic handler.

Example:

```python
WorkflowStep(
    "draft",
    "draft_text",
    {"execution_mode": "agentic"},
)

WorkflowStep(
    "persist",
    "save_state",
    {"execution_mode": "deterministic", "safety_category": "persistence"},
)
```

The policy is local-first, does not call external services, and does not grant approval for sensitive operations. Existing approval, dry-run, authorization, and boundary-validation gates remain independently required. Focused coverage is in `tests/test_workflow_execution_policy.py`.
