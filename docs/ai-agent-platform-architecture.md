# Orville AI Agent Platform Architecture

## Architectural boundary

Orville is a standalone Python orchestration engine extended with a durable control plane. The control plane stores project and task intent, plans, approvals, milestones, and sanitized events. The execution plane remains the existing dependency-aware `OrchestrationEngine`, which can later consume approved task milestones through an adapter. The workspace plane provides a bounded local development implementation for file inspection, checksum-guarded writes, commands, snapshots, and rollback.

```text
Natural-language request
        |
        v
Project/task control plane ---- append-only events ---- activity timeline
        |
        v
Editable plan and approval gate
        |
        v
Workspace session ---- repository tools ---- validation ladder
        |
        v
Immutable revision/checkpoint ---- preview/release adapters
```

## Implemented components

| Component | Location | Responsibility |
|---|---|---|
| Existing graph runtime | `orville_core/engine.py` | Dependency ordering, retries, cancellation, approval waits, checkpointed execution, verification hooks |
| Control-plane persistence | `orville_core/platform.py` | SQLite projects, tasks, plans, milestones, approvals, lifecycle transitions, sanitized events |
| Workspace execution | `orville_core/workspace.py` | Temporary isolated copy, path boundaries, checksum-guarded writes, allowlisted commands, revisions, rollback |
| Authenticated API | `orville_core/api.py` | Existing run/provider routes plus project/task/plan/event routes |
| Security primitives | `orville_core/security.py` | Filesystem, network, tool, dry-run, and secret-redaction policies |

## Lifecycle

A task starts as `new`, moves through analysis and plan approval, and only enters `workspace_ready` after approval. A rejected plan transitions to `cancelled` and does not invoke workspace mutation. Execution and validation states are explicit and transition checks reject illegal jumps. The current control plane does not yet create production previews or deployments; those are later adapters.

## Persistence strategy

SQLite is used for local durability with foreign keys, WAL mode, and append-only event sequence numbers. The existing checkpoint tables remain compatible and are not replaced. A future production deployment should move control-plane records to a managed relational database and artifacts to content-addressed object storage, while preserving the same domain contracts.

## Concurrency and revision safety

Every workspace write can require the current file checksum. A mismatch raises a stale-write error before replacement. Revision snapshots are content-addressed by a deterministic tree hash and retain the parent revision and changed paths. The current local implementation stores snapshots within the workspace parent; a production adapter must persist immutable snapshots and coordinate remote Git revisions.

## Security boundary

Commands are invoked without a shell, from a temporary workspace, with an allowlist and timeout. File paths resolve through an explicit root policy. Output is bounded. This is a local safety layer, not a complete hardened sandbox: production execution still requires a non-root container or VM, CPU/memory/disk/process limits, network egress controls, package-source policy, and child-process cleanup enforcement.

## Extension points

Future milestones should add adapters for identity and project membership, artifact storage, browser previews, validation runners, secrets, connectors, workflows, Git synchronization, deployment, evaluations, and observability. Each adapter must declare capabilities and permissions, return structured results, and expose unavailable or mock status when credentials or infrastructure are absent.
