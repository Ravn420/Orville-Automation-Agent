# Orville Workflow Foundation

## Purpose

This increment establishes the project-level contracts needed before expanding the scheduler or GUI. It adds durable project state, normalized software-objective intake, specialist-agent definitions, handoff-ready records, independent verification records, and a model-backed task handler that connects the provider router to the orchestration engine.

## Project state

`ProjectState` records project ID, objective, scope, assumptions, decisions, active phase, blockers, artifacts, and update time. It persists through an atomic JSON file so the project can be resumed outside Manus.

```python
state = ProjectState("orville", "Build a software-generation system", active_phase="foundation")
state.save("STATE.json")
restored = ProjectState.load("STATE.json")
```

## Objective intake

`SoftwareObjective` normalizes the user’s objective, requested deliverables, constraints, target environment, risk level, acceptance criteria, assumptions, and required capabilities. `TaskIntake.to_graph()` creates a validated graph skeleton. The current intake is deliberately deterministic; future planning agents will expand the skeleton into a multi-task graph after clarification and risk analysis.

## Agent registry

`AgentDefinition` identifies a specialist, role, capabilities, description, and verifier status. `AgentRegistry` supports registration, lookup, capability selection, and separate verifier selection. `default_agent_registry()` includes research, code synthesis, IDE, prototype, automation, orchestration, and verification roles.

`AgentHandoff` defines the portable handoff envelope: task ID, source and destination agents, objective, inputs, expected outputs, acceptance criteria, constraints, and status. The next scheduler increment should persist handoffs as events and enforce file ownership boundaries.

## Independent verification

`VerificationRecord` is separate from task execution. It records verifier agent, checks, defects, evidence, pass status, and timestamp. `verify_output()` provides a deterministic baseline for non-empty model output and optional case-insensitive acceptance-criterion checks. Production verification should add tests, static checks, source evidence, visual checks, and human approval where required.

## Model-backed tasks

`model_task_handler(router)` produces an engine-compatible handler. Task inputs may contain `messages` or a simple `prompt`/`objective`, plus routing preferences and capability requirements. The handler returns text, model and provider identity, finish reason, tool-call proposals, usage, and routing attempts. Because the engine persists task output in its checkpoint context, routing metadata is resumable and auditable.

Tool calls are proposals only. The handler does not execute tools. Authorization, argument validation, approval, filesystem and network boundaries, and side-effect controls remain responsibilities of the orchestration security layer.

## Verification command

```bash
python -m compileall -q orville_core tests examples
python -m unittest discover -s tests -v
```

The foundation test suite currently passes 26 tests, including the original orchestration, checkpoint, provider, routing, and new workflow tests.

## Remaining work

The next increment should add independent verifier execution to the engine, richer task intake and planning, graph task assignment through the agent registry, parallel and conditional scheduling, approval and cancellation controls, runtime security enforcement, and persistent task-graph records beyond a single execution checkpoint.
