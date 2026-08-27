# Orville AI Agent Platform Implementation Assessment

**Date:** 2026-08-24  
**Project:** Orville  
**Repository:** `C:\Users\Zeref\Documents\Manus Projects\Orville`  
**Assessment status:** Milestone 1 — assessment and foundation planning

## Summary

Orville is an existing standard-library-first Python orchestration engine, not a conventional web application. It already provides a durable task-graph runtime, provider adapters, authenticated API bridge, redacted artifacts, basic security primitives, model routing, streaming, and verification contracts. The requested platform should therefore be implemented as an incremental control-plane and execution-plane extension around the existing engine rather than as a rewrite.

The first implementation boundary is a durable project/task/plan/event model with explicit approval states and immutable revision concepts. A browser GUI, hard process isolation, multi-user identity, encrypted secrets, production deployment, and external integrations require additional infrastructure and must not be represented as complete until their supporting providers and enforcement mechanisms exist.

## 1. Existing architecture

| Area | Current implementation | Reusable foundation | Current limitation |
|---|---|---|---|
| Runtime | Python package `orville_core`, Python >= 3.10 | Standard-library-first design and typed modules | No web frontend in this repository |
| Orchestration | `OrchestrationEngine` executes dependency-aware graphs with retries, cancellation, approvals, timeouts, idempotency, and verification hooks | Existing execution and event semantics can back task milestones | Execution is run-centric and lacks project workspace isolation |
| Workflow contracts | `ProjectState`, `SoftwareObjective`, `TaskIntake`, `AgentDefinition`, `AgentHandoff`, and `VerificationRecord` | Existing objective normalization and specialist registry | Required project, plan, revision, approval, and workspace records are incomplete |
| Persistence | Atomic JSON checkpoint files and SQLite checkpoint store | Checkpoint durability and atomic replacement | No normalized database schema for platform records; JSON/SQLite stores are not yet multi-tenant |
| API | Optional FastAPI bridge under `/api/v1`; bearer-token authentication; CORS configuration; SSE event stream | Existing authenticated API and reconnectable event cursor pattern | Existing routes expose objectives, runs, providers, artifacts, and state rather than the required project/task API |
| Providers | Gemini, Ollama/custom local adapters, image generation, streaming, embeddings, capability routing, endpoint validation, health checks, and circuit breaking | Provider-neutral adapter and routing contracts | Credential lifecycle, connector scopes, encrypted secret storage, and provider-specific permissions remain incomplete |
| Artifacts | `ArtifactStore` with path policy and generated artifact registration | Artifact IDs, local artifact root, path traversal protection | No project-scoped artifact authorization or archive/export workflow |
| Security | `ToolPolicy`, `FilesystemPolicy`, `NetworkPolicy`, and `SecretRedactor` | Fail-closed policy primitives and log redaction | No enforced non-root subprocess sandbox, resource quotas, package firewall, identity model, or organization policy |
| Testing | `unittest` suite, compile checks, operational PowerShell scripts | Existing regression baseline and verification scripts | No browser smoke agent, accessibility checks, evaluation suites, or full security pipeline |
| Deployment | Docker and Windows packaging/deployment scripts are present | Existing operational documentation and packaging process | No revision-aware preview/staging/production release manager or recorded rollback target |

The source of truth for the current workflow contracts is [`orville_core/workflow.py`](../orville_core/workflow.py). The runtime behavior is implemented in [`orville_core/engine.py`](../orville_core/engine.py), while the current HTTP boundary is defined in [`orville_core/api.py`](../orville_core/api.py). The current README explicitly identifies database-backed project state, artifact storage, push events, hard isolation, encrypted secrets, production GUI, and operational telemetry as limitations.[1] [2] [3]

## 2. What can be reused

The existing `TaskGraph` and `TaskNode` abstractions should remain the execution substrate. The new platform should translate an approved `AgentTask` and its plan milestones into a scoped graph, then invoke the existing engine through an execution adapter. This avoids duplicating dependency handling, retry behavior, cancellation checks, approval waits, checkpointing, and independent verification.

`TaskIntake` can be extended into Plan Mode. Its classification, clarification questions, and normalized `SoftwareObjective` provide the initial specification-extraction layer. The current agent registry should become the seed catalog for the requested planning, implementation, debugging, research, testing, security, design, documentation, data, and deployment modes.

The SQLite checkpoint store and append-only engine events are suitable for a compatibility layer during Milestones 1–4. New records should use explicit IDs, project scope, actor identity, timestamps, and immutable revision references. Existing JSON checkpoints should remain readable during migration and should be treated as execution snapshots rather than as the long-term relational source of truth.

The provider registry, capability-aware router, endpoint validation, health checks, and redaction behavior should be retained behind a connector interface. External credentials must continue to arrive through environment variables or a future secret-reference service; plaintext provider keys must not be persisted in plans, checkpoints, events, artifacts, prompts, or archives.

## 3. Required additions and gaps

### 3.1 Control-plane records

The project needs durable records for projects, members, instructions, memory, tasks, modes, plans, milestones, workspace sessions, tools, permissions, events, artifacts, revisions, checkpoints, previews, deployments, approvals, integrations, secret references, workflows, workflow versions/runs/events, evaluations, security findings, metrics, and notifications.

The first schema should prioritize `Project`, `ProjectMember`, `ProjectInstruction`, `ProjectMemory`, `AgentTask`, `Plan`, `PlanMilestone`, `TaskEvent`, `Revision`, `Checkpoint`, and `Approval`. The remaining records should be introduced through later migrations with explicit foreign keys and retention behavior.

### 3.2 Lifecycle enforcement

The required task states are `new`, `analyzing`, `plan_ready`, `awaiting_plan_approval`, `workspace_ready`, `executing`, `validating`, `repairing`, `preview_ready`, `awaiting_feedback`, `ready_to_publish`, `awaiting_release_approval`, `deploying`, and `completed`. State transitions must be validated, persisted, and represented in the activity log.

The current approval endpoint approves an individual run task. It is not yet a plan approval gate and does not encode risk-based approval policy. A new approval service must require review before architecture changes, authentication changes, migrations, external integrations, production changes, destructive actions, financial actions, or public communication.

### 3.3 Workspace and repository operations

The platform needs a workspace adapter with an explicit base revision, workspace session ID, allowed roots, non-root execution identity, resource limits, timeout policy, network allowlist, and cleanup behavior. Repository tools must return structured results, sanitized arguments, exit status, bounded output, changed paths, and evidence references.

Writes must use structured patches and expected checksums. A write against a stale base revision must fail without mutation and produce a conflict record. Revisions should be immutable and should retain parent revision, changed paths, author/agent identity, validation results, and rollback metadata.

### 3.4 Preview, validation, and repair

The validation ladder should be represented as a first-class milestone pipeline: parse/typecheck, format/lint, unit tests, integration tests, build, browser smoke tests, accessibility, security, and preview verification. Each result needs a status, command or check identifier, sanitized output, duration, and artifact/evidence references.

Bounded repair must be a deterministic policy with a maximum of three attempts per failure class. Each repair attempt must record the failure, relevant excerpts, expected invariant, attempted patch, validation result, and whether the task paused for user input. No unrestricted self-repair loop is acceptable.

### 3.5 Identity, security, and governance

The current bearer token is appropriate for a localhost bridge but not for the required multi-user project platform. A compatible identity adapter is needed for user identity, project membership, roles, organization scope, and artifact/task authorization. Until that adapter exists, the API must remain explicitly documented as single-token or development-only.

Secret storage must use references rather than values. Tool permissions must be scoped by project, task, mode, environment, and risk policy. Side effects such as publishing, payments, deletion, public posting, credential changes, destructive migrations, and production configuration require explicit confirmation.

### 3.6 GUI and external capabilities

This repository contains no frontend source. The existing README notes that a separate `orville_gui` project supplies a responsive Control Center foundation but does not access local files, API keys, or user model runtimes.[1] The GUI should therefore consume the new project/task/plan/event APIs through a typed client rather than accessing the engine internals.

Browser operation, research browsing, data analysis, RAG, multimedia, GitHub/GitLab synchronization, deployment providers, and payment providers require adapters with declared scopes and secure credential paths. The platform should provide local mocks and adapter health states where a real provider is unavailable; it must not claim provider-backed support solely from an interface definition.

## 4. Proposed data model

| Record | Key fields | Invariants |
|---|---|---|
| `Project` | `id`, `name`, `description`, `owner_id`, `environment`, timestamps, retention policy | Project identity is stable; access is membership-controlled |
| `ProjectMember` | `project_id`, `actor_id`, role, status | Unique project/actor pair; role checked on every protected operation |
| `ProjectInstruction` | project ID, version, content, source, active flag | Versioned; active instruction is explicitly selected |
| `ProjectMemory` | project ID, key, value/artifact reference, confidence, source | Sensitive values are references or redacted content |
| `AgentTask` | request, project, base revision, status, milestone, mode, provider, budget, permissions, result revision | State transition and base revision are validated |
| `Plan` | task ID, interpreted objective, assumptions, affected files, risks, approvals, acceptance criteria | Rejection causes no repository mutation |
| `PlanMilestone` | plan ID, sequence, agent mode, dependencies, status, outputs | Milestones are ordered and auditable |
| `WorkspaceSession` | task ID, workspace path/reference, base revision, limits, status | Workspace is isolated, bounded, and cleaned up |
| `TaskEvent` | task ID, sequence, event type, actor, sanitized payload, timestamp | Append-only; cursor-resumable |
| `Artifact` | project/task ID, content hash, media type, storage reference, retention | Content is access-controlled and secrets-scanned |
| `Revision` | project ID, parent, content hash, changed paths, actor, validation summary | Immutable; stale bases cannot overwrite newer revisions |
| `Approval` | subject, risk class, requester, approver, decision, evidence | Approval scope is explicit and cannot be reused across unrelated actions |
| `Workflow` / `WorkflowRun` | definition/version, trigger, idempotency key, status, retry metadata | Runs are replayable, idempotent, and auditable |
| `SecurityFinding` | project/task, rule, severity, path, status, evidence | Findings are retained and linked to validation/release gates |

All records should include `created_at`, `updated_at` where mutable, actor identity, project scope, environment, and deletion/retention metadata. Events and revisions are append-only or immutable. Large logs, screenshots, reports, and datasets belong in artifact storage with metadata in the database.

## 5. Proposed API and UI

The existing `/api/v1/objectives`, `/runs`, `/artifacts`, and `/state` routes should remain backward-compatible while project-scoped routes are added. The first API slice should include project creation/retrieval, task creation, plan retrieval and approval, task event retrieval/streaming, revision listing, checkpoint creation, and artifact retrieval. Later slices should add workspace tools, previews, workflows, integrations, security findings, analytics, synchronization, and deployment operations.

The workspace UI should follow the requested three-column model: a project panel for plan/files/revisions/workflows/integrations; a central live preview or code surface with route and viewport controls; and an activity panel for milestones, tool status, validation, approvals, and logs. The bottom composer should submit natural-language requests with mode, model, environment, attachments, and selected UI context.

The UI must expose safe activity summaries rather than private chain-of-thought. Every tool event should show the tool name, sanitized arguments, status, affected files, bounded result, and evidence links. Plan approval must be visually distinct from release approval. The preview must identify the exact served revision and support desktop/mobile presets, route selection, refresh, screenshot capture, and later visual element selection.

## 6. Infrastructure requirements

| Requirement | Current state | Needed implementation |
|---|---|---|
| Durable database | SQLite checkpoint storage | Project-scoped relational schema and migrations; retain checkpoint compatibility |
| Object storage | Local artifact directory | Content-addressed artifact store with access checks, retention, and archive export |
| Event delivery | Polling-backed SSE over checkpoints | Append-only event store with cursor resume and later WebSocket support |
| Workspace isolation | Filesystem policy primitives | Non-root sandbox, process/resource limits, network policy, cleanup, and command allowlists |
| Identity | Shared bearer token | Pluggable identity and project authorization adapter |
| Secrets | Environment variables and redaction | Server-side secret references, encryption, rotation, and minimum-scope injection |
| Preview | Not implemented in this repository | Revision-pinned preview runner and browser smoke integration |
| Source control | Packaging and deployment scripts; no integrated Git service | Safe pull/branch/validate/commit/push/PR flow with conflict preservation |
| Deployment | Existing Docker/Windows artifacts | Provider adapter for preview/staging/production, release records, health checks, rollback |
| Observability | JSONL traces and evaluation notes | Metrics, structured audit events, latency/cost/error telemetry, drift monitoring |

## 7. Risks and mitigations

**Risk: broad scope produces a false-complete system.** Mitigation: implement the twelve milestones in order, report limitations after each milestone, and keep unsupported adapters in mock or unavailable states.

**Risk: a stale agent write overwrites a manual change.** Mitigation: require base revision and expected checksums for every write; reject stale writes and surface conflicts.

**Risk: secrets leak through model context or artifacts.** Mitigation: secret references, server-side injection, recursive redaction, secret scanning before persistence/export, and tests containing synthetic credentials.

**Risk: commands escape the intended workspace or exhaust resources.** Mitigation: non-root isolated execution, canonical-path checks, process-group cleanup, hard timeouts, quotas, package-source policy, and deny-by-default network egress.

**Risk: external side effects occur without authorization.** Mitigation: dry-run defaults, explicit tool permissions, risk-class approvals, release approval, idempotency keys, and audit records.

**Risk: event streams lose progress during reconnects.** Mitigation: monotonic event sequence, cursor-based SSE replay, bounded event retention, and terminal-state handling.

**Risk: current GUI/API contracts diverge.** Mitigation: preserve existing routes, add versioned project routes, publish typed schemas, and add contract tests before GUI integration.

**Risk: database migration damages existing state.** Mitigation: migration preview, backup before migration, reversible schema changes, compatibility loaders, and a user-approved migration step.

## 8. Assumptions

The repository is a Python package with an optional FastAPI API bridge and no frontend source in the inspected tree. The current deployment process is considered authoritative and must not be replaced without explicit approval. SQLite is suitable for the first local development slice, but production durability, multi-user authorization, and concurrent workspaces require a stronger database and storage deployment selected later.

The project currently has no confirmed external identity provider, object-storage provider, deployment provider, or Git synchronization credential path. Provider adapters should therefore be designed as interfaces with local deterministic implementations until credentials and permissions are explicitly configured.

The requested platform is treated as a product expansion of Orville, not a request to create a separate demonstration application. Existing package names, entry points, tests, provider behavior, and packaging artifacts must remain functional after each milestone.

## 9. Staged implementation plan

| Milestone | Scope | Completion evidence |
|---|---|---|
| 1 | Assessment, project/task/plan/event records, workspace shell | Assessment, schema/contracts, project/task APIs, event tests |
| 2 | Plan Mode, approvals, agent modes, model selection | Editable plan, rejection immutability, approval policy tests |
| 3 | Isolated workspace, repository tools, structured patches, revisions | Checksum enforcement, stale-write rejection, revision tests |
| 4 | Command execution, validation ladder, self-repair, diffs, checkpoints | Bounded repair tests and validation evidence |
| 5 | Live preview, browser smoke, visual selection, style controls | Revision-pinned preview and smoke test evidence |
| 6 | Backend/database/auth/storage generation and environment separation | Migration preview, identity adapter, secret-reference tests |
| 7 | Workflows, schedules, webhooks, retries, replay, approvals | Idempotent workflow-run and retry tests |
| 8 | Skills, plugins, hooks, subagents, MCP, OpenAPI connectors | Declared-permission extension tests |
| 9 | Browser operator, research, RAG, data analysis, multimedia | Adapter capability matrix and evidence-grounded outputs |
| 10 | GitHub/GitLab, pull requests, issue tracking, export, handoff | Conflict-safe synchronization and archive tests |
| 11 | Deployment, domains, HTTPS, monitoring, rollback, recovery | Release record, health checks, rollback drill |
| 12 | Security center, evaluations, drift monitoring, analytics, collaboration | Evaluation reports, security findings, metrics, access tests |

### First milestone implementation boundary

The first code milestone should add a backward-compatible platform domain layer, not attempt the entire feature list. It should provide durable project metadata, project instructions and memory, agent tasks, editable plans, milestones, approvals, append-only task events, and project-scoped API routes. It should adapt approved tasks to the existing orchestration engine without modifying repository files during plan generation or rejected-plan flows.

## 10. Validation strategy

Before each milestone is accepted, run the project’s existing test command, compile check, formatter/linter/type checks when available, production/package build checks, and relevant security checks. Add focused tests for state transitions, plan rejection immutability, authorization, redaction, event cursor replay, stale revisions, and bounded repair.

The first acceptance gate is: a user can submit a request, receive an editable plan, reject it without repository mutation, approve it into a scoped task, observe sanitized events, and retrieve the resulting checkpoint or revision. Any unsupported external capability must return a clear unavailable/mock status and document its required provider credentials.

## 11. Recommended next action

Implement Milestone 1 using a compatibility-focused domain and persistence layer in `orville_core`, then add API contract tests without removing the existing run-centric routes. Do not begin broad workspace mutation, deployment, or external side-effect integrations until the assessment and Milestone 1 plan are reviewed and approved.

## References

[1]: ../README.md "Orville README and current limitations"
[2]: ../orville_core/workflow.py "Orville workflow contracts"
[3]: ../orville_core/api.py "Orville authenticated API bridge"
[4]: ../orville_core/security.py "Orville security policy primitives"
[5]: ../STATE.md "Orville execution state"
[6]: ../TASK_GRAPH.md "Orville foundation task graph"
[7]: ../../../../upload/pasted_content_2.txt "Authoritative AI agent platform requirements"
