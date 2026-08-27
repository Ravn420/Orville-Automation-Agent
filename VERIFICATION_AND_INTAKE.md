# Verification and Intake Foundation

## Objective intake

`SoftwareObjective` provides a normalized representation of a user request. It records the objective, deliverables, constraints, target environment, risk level, acceptance criteria, assumptions, and required capabilities. `TaskIntake.to_graph()` creates a deterministic graph skeleton containing the objective and derived classification.

`TaskIntake.classify()` provides an initial deterministic category such as `coding`, `web_development`, `automation`, `research`, `media_generation`, `document_production`, `deployment`, `mixed`, or `general`. This is an initial routing hint, not a substitute for agentic planning. `clarification_questions()` identifies missing deliverables, acceptance criteria, and target environment details.

## Agent contracts

`AgentDefinition` describes a specialist’s identity, role, capabilities, and verifier status. `AgentRegistry` supports registration, lookup, capability selection, and separate verifier selection. `AgentHandoff` is a serializable contract for transferring a task between agents with inputs, expected outputs, constraints, and acceptance criteria.

## Independent verification

The engine accepts a verifier mapping in addition to task handlers. A verifier receives the task, output, and checkpoint context and may return a boolean, a dictionary containing `passed`, or a `VerificationRecord`. The engine persists the record under `context.verifications`, emits `task_verified_independently` on success, and fails the task with a durable `task_verification_failed` event when the gate fails.

This is intentionally separate from handler success. A handler returning without raising proves only that the handler completed; the verifier determines whether the output satisfies acceptance requirements.

## Model-backed execution

`model_task_handler(router)` converts task inputs into an `LLMRequest`, routes it through the provider layer, and returns response text plus provider, model, usage, tool-proposal, and routing-attempt metadata. Since task outputs are persisted by the checkpoint engine, the selected provider and fallback history remain available after resume.

## Verification command

```bash
python -m compileall -q orville_core tests examples
python -m unittest discover -s tests -v
```

The current regression suite passes 29 tests. The next execution-control increment should add verifier task nodes, parallel scheduling, conditional branching, approval pauses, cancellation, timeout policies, and idempotency controls.
