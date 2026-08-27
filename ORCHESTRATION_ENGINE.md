# Orville Core Orchestration Engine

## Scope

This first implementation slice provides a standalone, dependency-free Python orchestration core. It validates directed acyclic task graphs, executes registered task handlers in dependency order, persists complete run state after every material transition, records structured events, handles failed and blocked tasks, and resumes incomplete runs from JSON checkpoints.

## Project structure

```text
orville_core/
├── __init__.py       Public API
├── models.py         Task, graph, event, run, and checkpoint models
├── checkpoint.py     Atomic JSON persistence
└── engine.py         Dependency-aware executor
examples/
└── basic_run.py      Runnable demonstration
tests/
└── test_orchestration.py
```

## Quick start

From the project root, run the test suite:

```bash
python -m unittest discover -s tests -v
```

Run the demonstration:

```bash
python examples/basic_run.py
```

The demonstration writes a checkpoint to `.orville/checkpoints/basic-demo-run.json`.

## Execution contract

A `TaskNode` requires a stable `task_id`, title, handler name, dependency list, input mapping, and maximum attempts. A `TaskGraph` requires a stable graph ID and validates unique IDs, known dependencies, self-dependencies, and cycles before execution. A handler has the signature:

```python
def handler(task: TaskNode, context: dict[str, Any]) -> Any:
    ...
```

The handler returns a JSON-serializable output. Exceptions are captured into the checkpoint as task failures rather than being silently discarded. A missing handler is treated as a failed task, and tasks depending on a failed task become blocked.

## State transitions

Tasks begin in `planned`, become `ready`, then `running`, and finish as `verified`. A task may become `failed`, `blocked`, or `cancelled`. A run becomes `completed` when all tasks are verified or cancelled, `blocked` when a dependency prevents progress, or `failed` when an executable task exhausts its attempts or no executable work remains.

The current executor retries a failed task within the same run when its `attempts` value remains below `max_attempts`. A persisted failed checkpoint can also be loaded with `resume=True`; this permits recovery after process interruption or a separately managed retry decision.

## Checkpoint guarantees

Each checkpoint contains schema version, run ID, graph definition, task state, context, run status, and the complete ordered event list. Writes use a temporary file in the target directory, flush and file-level fsync, followed by atomic replacement. POSIX directory fsync is used where supported; Windows uses the atomic replacement boundary because directory fsync is not supported by the platform API.

Checkpoints are intended to be portable JSON artifacts. Future versions should add explicit migrations when the schema changes rather than silently reading incompatible data.

## Limitations in this slice

Execution is synchronous and single-process. It does not yet provide concurrent graph branches, distributed workers, database-backed checkpoint storage, model-provider adapters, approval interrupts, sandboxed tool execution, OpenTelemetry export, or GUI integration. These are tracked in `TODO.md` and should be added without weakening the checkpoint and state contracts established here.

## Recommended next implementation steps

1. Add explicit graph and task schema validation with JSON Schema or equivalent typed validation.
2. Add deterministic event IDs, parent-child correlation IDs, and artifact references.
3. Add a pluggable checkpoint backend while retaining the atomic JSON backend for local standalone use.
4. Add approval and interrupt nodes with safe resume semantics.
5. Add concurrency controls for independent tasks and a merge-safe artifact protocol.
6. Add provider-neutral model and tool-call contracts.
7. Add GUI event streaming and trace visualization.
