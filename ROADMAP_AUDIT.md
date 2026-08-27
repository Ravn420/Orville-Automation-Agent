# Orville Prior-Phase Roadmap Audit

**Audit date:** 2026-08-24  
**Scope:** Phases 0–3 and all prerequisites needed before GUI and production hardening  
**Auditor:** Orchestration Agent

## Executive finding

The initial Phase 1–3 implementation is real and tested, but it represents a **library-level vertical slice**, not yet a complete autonomous software-generation product. The core graph executor, checkpoint store, provider adapters, streaming, multimodal conversion, embeddings, capability filtering, endpoint preflight, and basic fallback behavior are present. The most important missed prerequisites are project-state persistence, task intake, agent handoff contracts, independent verification, model-task integration, safe local-model activation, security enforcement, GUI implementation, production testing, and deployment operations.

## Evidence reviewed

| Artifact | Finding |
|---|---|
| `orville_core/engine.py` | Synchronous dependency-aware execution, event recording, failure blocking, and checkpoint-backed resume |
| `orville_core/checkpoint.py` | Atomic JSON persistence with cross-platform durability handling |
| `orville_core/providers.py` | Gemini, Ollama, custom local endpoint, streaming, multimodal, embeddings, health checks, and provider registry |
| `orville_core/local_models.py` | User-downloaded local asset hashing, basic inspection, catalog persistence, and provider bridging |
| `orville_core/routing.py` | Capability filtering, local-only selection, preference order, fallback, and endpoint validation |
| `tests/` | 21 passing tests using deterministic fake transports |
| `examples/basic_run.py` | Runnable local checkpointed orchestration example |
| `*.md` documentation | Component-level documentation exists; product-level documentation is incomplete |
| `TODO.md` | Broad roadmap exists, with several items now marked complete and an audit gap register added |

## Completed versus partial work

| Area | Status | Qualification |
|---|---|---|
| Task graph representation | Partial complete | Typed DAG and validation exist, but intake and richer node types do not |
| Checkpointing | Partial complete | Atomic JSON and resume exist; durable replay, cancellation, approval checkpoints, and distributed storage do not |
| Retry behavior | Partial complete | Failed tasks can retry while attempts remain; policy, backoff, jitter, idempotency, and external-action safeguards do not |
| Provider adapters | Partial complete | Gemini and Ollama-compatible paths exist; streaming, embeddings, and multimodal support are basic rather than fully negotiated |
| Local model support | Partial complete | Cataloging exists; secure runtime validation and activation are absent |
| Routing | Partial complete | Capability and fallback routing exist; health-aware ranking, quotas, circuit breakers, and persistent telemetry are absent |
| Agent orchestration | Not complete | No operational specialist-agent registry or handoff protocol exists |
| Verification | Not complete | Task success is not independently verified against acceptance criteria |
| GUI | Not started | No frontend or desktop GUI files exist |
| Security | Mostly requirements | Endpoint preflight exists; tool sandboxing, secret storage, prompt-injection defenses, and audit enforcement are not implemented |
| Testing | Prototype level | Unit and fake-transport coverage exists; integration, acceptance, performance, security, and repository-level evaluations do not |
| Operations | Not started | No packaged health command, deployment target, metrics export, rollback, or runbook exists |

## Missed prerequisites that should be restored to the active execution path

### P0 — Must precede autonomous software generation

**Project state and resumability.** Create `PROJECT.md`, `STATE.md`, and `TASK_GRAPH.md`. The checkpoint file preserves one run, but the project currently lacks a durable source of truth for objective, decisions, active phase, blockers, artifacts, and cross-run task graph state.

**Task intake.** Add a normalized intake model for user objective, deliverables, constraints, target environment, risk level, assumptions, required capabilities, and acceptance criteria. The current engine requires a prebuilt graph and therefore cannot yet transform an ordinary software specification into an executable plan.

**Agent contracts.** Define an agent registry, ownership model, handoff envelope, artifact contract, conflict policy, and verification assignment. The named roles exist in project instructions but are not represented as executable objects in the codebase.

**Independent verification.** Separate task execution from acceptance verification. A task should not become verified solely because its handler returned successfully; tests, static checks, behavioral checks, source checks, or human approval should produce a separate verification result.

**Model-task integration.** Connect `ProviderRouter` to graph tasks through a model-backed handler that records provider ID, model ID, capabilities, usage, routing attempts, and failures in the checkpoint and event stream. The router is currently a standalone API.

**Execution controls.** Add parallel and conditional nodes, approval and human-in-the-loop pauses, cancellation, timeout policies, retry backoff, idempotency keys, and controlled failure escalation. These are prerequisites for safe multi-agent execution.

**Security enforcement.** Convert documented security requirements into runtime controls before allowing tools or external side effects: permission scopes, tool allowlists, path boundaries, network policy, prompt-injection separation, secret redaction, approval gates, and audit records.

### P1 — Required for a usable product

**Safe local-model activation.** Extend cataloging with runtime validation, resource checks, safe format policy, adapter/base-model checks, lifecycle actions, and generation smoke tests. A file being registered must not imply that it is safe or usable.

**GUI foundation.** Build the application shell, task composer, model manager, execution monitor, task graph view, verification view, and artifact browser after stabilizing the model and orchestration interfaces.

**Runtime and connector diagnostics.** Package the manual initialization checks into a repeatable health command. Keep degraded MCP endpoints explicitly documented and provide fallback behavior.

**Testing and evaluation.** Add a test matrix, integration tests, acceptance workflows, security regression tests, performance tests, and isolated repository-level software-generation evaluations.

**Documentation and operations.** Add a standalone README, operator runbook, contributor guide, task templates, glossary, deployment instructions, versioning, metrics, tracing, rollback, and maintenance procedures.

## Recommended execution order

1. Create durable project state files and normalize roadmap task IDs.
2. Implement intake, agent registry, handoff envelopes, artifact contracts, and independent verification records.
3. Add model-backed graph handlers with provider and routing metadata in checkpoints.
4. Add parallel, conditional, approval, cancellation, timeout, retry, and idempotency controls.
5. Implement security enforcement and safe local-model activation.
6. Build the GUI against the stabilized orchestration APIs.
7. Add layered testing, evaluation, observability, packaging, deployment, rollback, and runbooks.

## Conclusion

Nothing essential was lost from the roadmap, but several prerequisites were bypassed when implementation moved directly from the core library into provider features. The roadmap now records those omissions explicitly. The next implementation target should therefore be **intake and agent contracts plus model-task integration**, not a broad expansion of provider features or GUI work in isolation.
