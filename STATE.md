# Orville Execution State

**Project:** Orville
**Active milestone:** M14 — Enterprise production readiness
**Active phase:** Model lifecycle, runtime hardening, and GUI workflow completion
**State:** In progress — local model lifecycle, runtime capability validation, streaming resume controls, and Windows Sandbox mapping/startup verification implemented; production hosting and official Blackbox OAuth remain blocked on external dependencies
**Last updated:** 2026-08-27

**Repository audit checkpoint — 2026-08-27:** A complete repository audit compiled the Python sources, built the base wheel, and ran the documented preview check (which passed with three existing normal-text contrast warnings). The first remediation increment added Fernet-encrypted non-Windows connector records using a runtime-only protected master key, preserved Windows DPAPI, fixed the outbound API request-class collision, and hardened model-download destinations against mixed-separator traversal. The second remediation increment added a shared platform-neutral repository-reference resolver for test contracts and a reviewed deterministic visual-regression baseline. Its focused suite passes **29 tests**. The full regression suite now completes with **780 passed, 8 failed, and 1 warning**. The authoritative remediation queue remains at the top of `TODO.md`; the release gate is blocked by the remaining tracked work.

**Automation checkpoint:** The primary Orville runtime now executes each active TaskGraph milestone with a default maximum of three concurrent independent tasks. Dependency ordering, verification, approval gates, cancellation, and failure/blocker handling remain authoritative; the execution loop advances immediately to the next eligible task after a verified completion. Focused orchestration tests pass; the current full regression release gate is blocked by the 8 failures documented in the repository-audit checkpoint above.

**Persistent roadmap worker checkpoint — 2026-08-27:** `tools/orville_manus_worker.py` now persists up to three already-created Manus task records, reserves their TODO positions to prevent duplicate selection, uses documented `GET /v2/task.detail?task_id=...` status checks, and resumes the same task thread through `POST /v2/task.sendMessage` after `task.status=stopped`; it never creates replacement tasks. The CLI accepts `--repo` and `ORVILLE_REPO`, preventing launches from protected working directories such as `C:\\Windows\\System32` from writing state outside the repository. Legacy active-task state was backed up and reset at the user’s request; a live cycle created three fresh tasks and received `running` responses for all three. Focused worker tests pass. Windows installation is documented and passes `--repo` plus `--max-active 3`; persistent hosting and live provider credentials remain deployment-owned.

**M14.8 automation started:** The active milestone, non-production canary and rollback drill, is marked `in-progress-local`. `docs/M14_8_NONPRODUCTION_CANARY_ROLLBACK_DRILL_RUNBOOK.md` defines the approved non-production procedure, and `artifacts/templates/M14_8_CANARY_ROLLBACK_ACCEPTANCE_EVIDENCE_TEMPLATE.md` defines the per-run acceptance record. The existing 18-scenario synthetic fault-injection baseline passed and was retained at `artifacts/m13_12_fault_injection.json`; focused canary/policy tests passed 7 tests. M14.8 remains incomplete until approved non-production execution and independently reviewed evidence for restart, duplicate-event, partial-failure, injected-fault, and rollback-failure recovery are retained.

**Phase 6 deployment documentation checkpoint — 2026-08-27:** `docs/DELIVERY_RUNBOOK.md` now documents the Compose deployment sequence, preflight and backup gates, authenticated health verification, approval-gated rollback, volume-preserving recovery, database restore evidence, and non-Compose fallback. Focused documentation assertions passed; live deployment, provider-side rollback, and production evidence remain deployment-owned.

**Phase 6 media verification checkpoint — 2026-08-27:** `docs/MEDIA_VISUAL_VERIFICATION.md` defines a common review record, complete-artifact inspection sequence, artifact-specific image/audio/video/document/animation/mixed checks, severity-based disposition, accessibility and rights evidence, and standalone validation commands. Three focused tests, Python compilation, structural checks, and secret-safe wording checks passed. Live media-provider and publication verification remain outside the local contract.

**Phase 6 reusable-components checkpoint — 2026-08-27:** `docs/REUSABLE_COMPONENTS_INTERACTIONS.md` defines reusable component families, state contracts, deterministic interaction patterns, composition rules, accessibility and responsive requirements, and review evidence. Three focused tests, Python compilation, structural checks, and secret-safe wording checks passed. Existing GUI and web screens are not claimed as fully migrated.

**Phase 6 safe-defaults checkpoint — 2026-08-27:** `config/settings-defaults.example.json` and `docs/SAFE_DEFAULTS_AND_ADVANCED_SETTINGS.md` define local-first, manual, bounded, and system-aware defaults across providers, models, privacy, storage, limits, schedules, notifications, preferences, and telemetry, while keeping optional advanced overrides discoverable and approval-gated. Three focused tests, JSON parsing, Python compilation, structural checks, and secret-safe wording checks passed. Production provisioning, live schedules, external notifications, and client migration remain outside this local contract.

**Phase 6 accessibility checkpoint — 2026-08-27:** `docs/ACCESSIBILITY_ACCEPTANCE_CRITERIA.md` defines keyboard operation, visible focus, semantic names and states, screen-reader announcements, contrast thresholds, reduced-motion behavior, zoom/reflow, alternatives, touch targets, and accessible error feedback across critical workflows. Three focused tests, Python compilation, structural checks, and secret-safe wording checks passed. The full suite completed with 493 passed, 3 failures in existing connector/shell API tests, and 1 pre-existing HTTP-client deprecation warning; no accessibility test failed.

**Phase 6 destructive-action confirmation checkpoint — 2026-08-27:** `docs/DESTRUCTIVE_ACTION_CONFIRMATIONS.md` defines consequence previews, explicit target/scope confirmation, reversible alternatives, approval boundaries, single-use expiry, fail-closed state transitions, accessible dialog behavior, safe diagnostics, and recovery actions for destructive or high-impact operations. Three focused tests, Python compilation, structural checks, and secret-safe wording checks passed. Live provider authorization and production destructive-action exercises remain outside the local contract.

**Phase 6 localization checkpoint — 2026-08-27:** `orville_core/localization.py` and `config/locales/en-US.json` separate stable user-visible text keys from business logic, provide locale fallback, safe interpolation, missing-key behavior, and secret-free workflow/error copy. Three focused tests and Python compilation passed. Additional locale translation, full UI migration, and translator review remain follow-up work.

**Phase 6 degraded-availability checkpoint — 2026-08-27:** `windows_gui.py` now maps unavailable cloud providers, local endpoints, connectors, and model runtimes to stable user-facing states with safe recovery actions. `docs/GUI_DEGRADED_AVAILABILITY.md` defines local draft/task-plan/artifact preservation, privacy-safe fallback, bounded retry, idempotency, and diagnostic boundaries. Three focused tests, Python compilation, structural checks, and secret-safe wording checks passed. Live provider, connector, runtime, and external recovery remain deployment-owned.
**Progress checkpoint:** Local model storage, runtime capability validation, streaming resume, metadata preservation, structured diagnostics, expanded lifecycle tests, provider retries with exponential backoff, circuit breaking, constrained fallback routing, the Windows local-model manager, guided provider setup, persisted provider discovery catalogs with automatic active-model switching, tenant-scoped remote catalog federation, provider-specific rate-limit accounting and usage metrics, redacted configuration export, enterprise remote policy storage with local fallback, comprehensive policy/catalog audit events, checksum-verified disaster-recovery backups, safe provider health checks, model safety classification, adapter/base-model checks, and local workflow API coverage are implemented and validated. Runtime requirement mismatches now produce deterministic validation errors. The standalone release gate now compiles, tests, and builds a wheel when the security extras are installed and the live security evidence flags are supplied; the M13.7 gate now passes in the configured Windows environment. Process-level sandboxing and cryptographic attestation verification are implemented; activation evidence persistence, a single verification service boundary, the M13.8 canary policy contract, the M13.1 platform matrix, the M13.7 gate aggregator, GUI attestation status/policy presentation, durable canary controller, and health evaluator are implemented locally. The full regression suite passes 347 tests with one existing HTTP-client deprecation warning. The executable M13.12 synthetic fault-injection runner passes all 18 scenarios. Linux/GPU live tests, production trust-root ceremony, live provider rollback, and production deployment remain explicit limitations.

## M14.7 production metrics and health-source checkpoint — 2026-08-27

M14.7 is complete as a local contract. `orville_core/production_metrics.py` provides explicit tenant/cohort/release scoping, freshness filtering, aggregation for error rate, latency, saturation, business health, security findings, and release quality, cross-scope rejection, and normalization into canary health observations. Focused tests pass (3). A production monitoring backend, alerting/SLO policy, completeness checks, and business-health source remain deployment-owned.

## M14.6 reviewed deployment-provider checkpoint — 2026-08-27

M14.6 is complete as a local contract. `orville_core/reviewed_deployment_provider.py` provides dry-run-by-default deployment operations, bounded provider calls, deterministic idempotency, traffic validation, protected credential-reference checks, and redacted status output. Focused tests pass (5). Provider-specific backend implementation, workload identity, provider-side cancellation/idempotency verification, and non-production rollback evidence remain deployment-owned.

## M14.5 protected secret management checkpoint — 2026-08-27

M14.5 is complete as a local contract. `orville_core/protected_secrets.py` provides runtime-only resolution, metadata-only versioned rotation, revocation, redacted metadata export, and explicit scrubbing. Focused tests pass (3); full regression passes 300 tests with one pre-existing Starlette/httpx deprecation warning. The next milestone task is M14.6. Enterprise provider provisioning, workload identity, scheduled rotation, encrypted value storage, and access-review evidence remain deployment-owned.

## Completed and validated

- Phase 0 governance baseline completed: added `AGENTS.md` and `CHANGELOG.md`, created `config/`, `docs/`, `artifacts/`, `logs/`, and `tmp/`, and documented untrusted-input handling, sensitive-action approvals, secret boundaries, retention, naming, validation, and handoff rules.
- Phase 0 validation confirmed all required control files and directories exist; no existing files were moved or deleted. The workspace is not a Git working tree, so Git status validation is not applicable in this copy.
- MCP configuration and implementation repair: corrected the `python fast api` connector URL from `http://127.0.0.1:42069 ` to `http://127.0.0.1:42069`, added `orville_core/mcp_server.py` plus `tools/run_python_mcp.py`, and added four approval-gated mutation tools. The bridge forwards 10 read-only and 4 mutation MCP tools to the authenticated REST API on port 8787, binds to port 42069, and requires both `ORVILLE_MCP_MUTATIONS_ENABLED=1` and per-call `approved=true` for writes.
- Clean-environment package validation passed: wheel generation, isolated virtual-environment installation of `.[api]`, and imports of FastAPI, Uvicorn, the CLI, and MCP bridge succeeded. The pre-existing corrupted CLI source was repaired so full collection could complete.
- Mutation bridge validation passed: focused MCP tests passed 8 tests, full regression suite passed 246 tests with one existing HTTP-client deprecation warning, Python compilation passed, and the live REST-to-MCP health call remained successful.
- MCP configuration diagnosis and repair: replaced the stale `https://mcp.fly.dev` transport with the official local flyctl stdio transport, installed flyctl v0.4.93 at `/home/ubuntu/.fly/bin/flyctl`, and validated discovery of 60 Fly tools. A read-only tool call reached flyctl but correctly reported that `flyctl auth login` is still required for authenticated Fly operations.

- Core synchronous orchestration engine, dependency graphs, retries, approvals, cancellation, timeouts, idempotency, checkpointing, providers, routing, streaming, embeddings, and verification contracts.
- Durable project/task/plan/milestone/approval/event control plane with lifecycle transitions and secret-redacted event cursors.
- Temporary workspace sessions with path boundaries, checksum-guarded writes, allowlisted commands, bounded output, revisions, and rollback.
- Structured validation ladder and three-attempt-per-failure bounded repair policy.
- Local workflow automation with manual/scheduled/webhook/data/connector/task-event trigger contracts, versioning, idempotency, retries, dead-letter state, and approval-gated steps.
- Permissioned skills, plugins, connectors, lifecycle hooks, and scoped subagent contracts.
- Revision-pinned preview metadata, selected-element context, deterministic safe style patches, and browser-smoke report contracts.
- Citation-aware research catalog, CSV profiling, project archive export, and provider-gated deployment handoff.
- Security findings, metrics, evaluation runs, release gates, rollback targets, explicit agent modes, capability-aware model selection, and local project-role authorization.
- Authenticated API routes for projects, tasks, plans, events, workflows, workflow runs, previews, security findings, export, project members, and adapter capability checks.
- Durable SQLite membership directory with role authorization, invitations, revocation, and fail-closed access checks.
- Adapter registry with explicit available, mock, blocked, degraded, capabilities, credential, and permission states for local workspace, browser, Git, deployment, identity, and object storage.
- Secret references, process-environment resolution, secret scanning/redaction, append-only audit records, durable schedules, signed inbound events, local preview HTTP runtime, deterministic readiness evaluation, and operational telemetry export.
- Runtime configuration validation, secure token generation, operator `config`/`readiness` commands, and a working `python -m orville_core.api` module entrypoint.
- Regression suite passes 278 tests with one existing HTTP-client deprecation warning. The 16-worker, 200-operation provider-control load test admitted exactly 100 of 200 calls under a 100-call window and completed 200 concurrent active-model switches. Focused model/runtime/streaming/media, metadata-diagnostics, GUI lifecycle, safety, and provider-resilience coverage passes; Python compilation passes for `orville_core`, `tests`, and `windows_gui.py`.
- Cloud-first Blackbox foundation added: `CloudRelayBoundary`, `ManagedBlackboxRelayAdapter`, server-side `create_relay_app`, `/api/v1/cloud/blackbox/*` status/admission/connect/disconnect routes, `tools/run_blackbox_relay.py`, and cloud integration documentation.
- The relay foundation rejects client-side Blackbox API keys, separates managed and user-connected access, enforces privacy approval and in-process quotas, and keeps provider credentials server-side in the deployable relay process.
- Local model records now preserve license, license restrictions, provenance, ownership, checksum, attestation, and safety metadata. Validation exposes stable diagnostics for unsupported or unsafe formats, missing runtimes, endpoint failures, corruption, resource shortages, incompatible hardware, base-model mismatches, scripts, and license review requirements.
- Windows GUI now includes a local model manager for inventory, validation, runtime selection, activation, deactivation, and approval-gated registration removal without deleting model files. End-to-end API tests cover import, metadata, validation, license review, activation, objective routing, deactivation, and safe removal.
- Blackbox API-key integration now has a credential-free contract validator for documented public/enterprise endpoint families, model identifiers, request capability metadata, and redacted error envelopes; endpoint- and account-plan-aware capability negotiation and model discovery now expose only safe metadata through credential-free APIs, with deterministic manual-model fallback. Managed-first cloud onboarding now provides an authenticated credential-free contract and accessible no-script guidance; user-connected access remains optional. The onboarding contract and Signal Room fallback now expose an explicit optional `Connect your Blackbox account` action without making it a prerequisite. Local API-key route validation is covered by tests, while live API-key authentication, quota, and account-plan behavior remain external gates. Blackbox relay status now exposes a deterministic local fallback decision for disconnected, unavailable, rate-limited, expired, invalid, disabled, and unconfigured states; no-credential status remains actionable. Connector capability auditing now accepts only concrete project connector requirements, selects enabled read-only operations, defaults to dry-run, and supports fixture invocation without permitting sensitive operations. Connector mutation governance now requires a concrete project requirement, explicit approval, and a non-secret approval reference for connector defaults, manual/OAuth connections, refresh, revoke, and disconnect. Connector transfer contracts now enforce approved-root containment, file-size/MIME limits, staged downloads, and credential-free transfer tests. Schedule execution history now persists outputs, artifacts, costs, connector actions, and approvals and is exposed through the authenticated API. Signal Room now has local smoke, document-language, focus, reduced-motion, and contrast audit checks; existing palette contrast findings remain warnings.
- `tools/release_gate.py` and `docs/RELEASE_GATES.md` provide standalone compilation, regression, wheel-build, model-safety, security, and deployment gates. Compilation, the full 278-test regression suite, and wheel packaging pass; generated wheel output remains disposable under `tmp/`. The saved report is `artifacts/release_gate_validation.txt`.
- M12.8 continuation: `sandbox_adapters.py` implements Windows Sandbox configuration/launch and Linux bubblewrap argv construction with capability detection; model handlers fail closed when a task requests sandboxing without an available approved adapter. `attestations.py` implements persistent trust-store bootstrap, approval-gated rotation/revocation, digest-bound Ed25519/in-toto verification, and a timeout-bounded Cosign adapter. `tuf_metadata.py` implements signed root/timestamp/snapshot/targets repository-chain verification and target digest/length checks; `tools/tuf_root_ceremony.py` and `config/tuf-trust-root.example.json` define the explicit-approval production ceremony boundary. Live Windows verification now confirms that CMD executes in Sandbox, host folders map automatically, and `LogonCommand` executes when the `.wsb` path is passed to `WindowsSandbox.exe` as a quoted argument. Evidence: `tmp/live-sandbox-test/automatic_mapping_success.txt`. GPU isolation and production trust-root ceremony remain unclaimed; negative fallback and TUF-integrity tests pass.

## Blackbox support-confirmation blocker — 2026-08-27

The first actionable unchecked TODO item requiring explicit Blackbox developer-support confirmation was reviewed and marked blocked. Public documentation does not establish third-party OAuth, device authorization, CLI token interoperability, scopes, redirect URI, refresh-token, rate-limit, or redistribution semantics. No support request, external post, credential submission, or provider-side action was performed under the current task constraints.

## Remaining infrastructure-dependent work

- Enterprise production identity, OAuth/SSO, organization membership, and full authorization middleware integration; local durable project membership is now implemented.
- Hardened non-root container/VM execution with CPU, memory, disk, process, network, and package-source controls.
- Enterprise secret-manager provisioning, encrypted value storage, workload identity, scheduled rotation, and external access-review evidence; the local value-free reference, runtime resolver, redaction, rotation metadata, revocation, and scrubbing contract is implemented.
- Real browser operator, live preview server, screenshot capture, accessibility testing, and visual DOM instrumentation.
- Hosted scheduler, webhook receiver, connector health/retry workers, and durable workflow execution workers remain infrastructure-dependent; local scheduling now includes atomic leases and stale-lease recovery, signed event intake includes replay protection and durable delivery inspection, and local workflow dispatch is implemented.
- GitHub/GitLab synchronization, conflict-aware branches, pull/merge requests, and remote issue integration.
- Real deployment providers, domains, HTTPS, monitoring, disaster recovery, and production rollback execution.
- Production Blackbox relay hosting, durable multi-tenant quotas, live upstream verification, official Blackbox OAuth/device authorization, and user-connected Blackbox health testing remain pending.
- Persistent GUI integration, collaboration UI, notifications, RAG/vector storage, multimedia workflows, and OpenTelemetry export. The desktop GUI now includes local model management, guided provider setup, model discovery, privacy-policy persistence, and redacted configuration export; broader persistent resource management remains pending.
- Process-level model sandboxing and cryptographic attestation verification are implemented as platform adapters and trust-root policy. Windows Sandbox live mapping/startup evidence is retained in `tmp/live-sandbox-test/automatic_mapping_success.txt`. Activation evidence persistence is implemented through `attestation_service.py` and `LocalModelRecord.activation_evidence`; M13.1 is documented in `docs/M13_SECURITY_BASELINE_PLATFORM_MATRIX.md`; M13.8 is implemented in `canary_policy.py` with an example under `config/`. GUI evidence presentation, GPU isolation, Linux live execution, and production trust-root ceremony remain infrastructure-dependent.

## Enterprise federation, audit, backup, and concurrency milestone — 2026-08-27

Implemented tenant-scoped remote catalog synchronization, authenticated catalog publish/sync, policy and catalog audit events, checksum-verified policy/discovery backups, backup inspection APIs, and a standalone concurrency load test. Evidence: `artifacts/provider_controls_load_test.json`; 16 workers and 200 operations produced 100 accepted and 100 rejected calls under the configured limit, with all 200 active-model switches completing.

## Provider operations and enterprise policy milestone — 2026-08-27

Implemented durable provider discovery catalogs, automatic active-model switching, provider-specific call/token rate-limit accounting, provider-scoped usage metrics, and an enterprise remote policy storage adapter with authenticated synchronization and atomic local fallback. Added API routes for catalog inspection, model selection, rate-limit configuration, provider usage, and policy-store status. Validation: 272 tests passed with one pre-existing HTTP-client deprecation warning.

## Provider discovery, privacy routing, and export milestone — 2026-08-27

Implemented provider model discovery for Ollama, OpenAI-compatible providers, and Gemini, with manual-model fallback for unsupported provider families. Added atomic persistence for local-only, cloud-approved, and restricted routing policies; local-only and restricted classes force local-provider routing. Added credential-free provider configuration export and desktop controls for discovery, policy save, and export. Validation: 261 tests passed with one pre-existing HTTP-client deprecation warning.

## Governance milestone — 2026-08-27

`AGENTS.md` now defines repository trust boundaries, explicit approval requirements, secret storage and masking rules, artifact retention and cleanup, predictable directory ownership, naming and formatting conventions, branch and commit conventions, review requirements, validation expectations, and agent handoff state. `docs/REPOSITORY_GOVERNANCE.md` provides the directory and lifecycle reference. `CHANGELOG.md` records the compatibility impact and validation evidence. The workspace contains the expected `orville_core/`, `tests/`, `config/`, `docs/`, `artifacts/`, `logs/`, `tmp/`, `browser_extension/`, and `release/` directories. Governance validation confirmed all required files and sections exist with no trailing whitespace; no runtime or user-data behavior changed.

## Provider onboarding milestone — 2026-08-27

The Windows desktop control center now exposes a guided provider setup window for Ollama, Gemini, OpenAI-compatible local servers, and Anthropic. It supports user-supplied endpoint/model/API-key fields, masked credential entry, provider inventory refresh, redacted provider health checks, model discovery, privacy-policy persistence, and redacted configuration export. The UI does not persist credentials or authorize remote transmission.

## M13 planned milestone — 2026-08-27

The next roadmap milestone is specified in `docs/NEXT_MILESTONE_SECURITY_CANARY.md`. It contains seven security-hardening tasks covering platform isolation, trust-store lifecycle, attestation verification, and release gates, followed by eight canary-deployment tasks covering policy schemas, deployment adapters, durable state transitions, health evaluation, rollback, observability, synthetic fault injection, and production integration. Production integration is infrastructure-dependent and gated on a non-production canary and rollback drill.

## M14 planned milestone — 2026-08-27

The next milestone is specified in `docs/NEXT_MILESTONE_ENTERPRISE_PRODUCTION.md` and tracked in `TODO.md` and `TASK_GRAPH.md`. It covers enterprise environment ownership, production trust-root ceremony, live Windows/Linux sandbox validation, tenant identity and least privilege, protected secret management, reviewed deployment-provider integration, production metrics, non-production canary and rollback drills, disaster recovery, load/soak gates, and a controlled production canary. Every production task remains infrastructure-dependent until its environment, credentials, approvals, and evidence exist.

## Operating rule

Unsupported capabilities remain explicit adapters or blocked handoffs. Do not represent a local contract as a production integration until its credentials, permissions, provider, and validation evidence exist.


## M13 local implementation checkpoint — 2026-08-27

Implemented the local portions of M13: provider-neutral Windows and Linux sandbox adapter contracts, fail-closed execution selection, persistent trust-store lifecycle, TUF/Cosign/in-toto verification adapters, security release-gate aggregation, durable SQLite-backed canary state, synthetic deployment controls, minimum-sample health evaluation, approval-gated advancement, pause/quarantine, idempotent rollback, secret-filtered canary audit records, and `/api/v1/canary/*` routes. Validation: Python compilation passed and 287 tests passed with one existing Starlette/httpx deprecation warning. Production worker IPC, GPU/live Linux validation, production trust-root ceremony, live deployment-provider integration, and non-production rollback drills remain infrastructure-dependent.


## M14.1 enterprise environment contract — 2026-08-27

Implemented and validated the standalone enterprise environment and responsibility-matrix contract. It validates tenant and environment identifiers, data classifications, allowed network labels, bounded RTO/RPO, named security/platform/deployment/data owners, rollback authority, and escalation channel without provisioning infrastructure or storing credentials. Evidence: `orville_core/enterprise_readiness.py`, `config/enterprise-environment.example.json`, `docs/M14_ENTERPRISE_ENVIRONMENT.md`, and 2 focused tests. Full regression suite: 292 tests passed with one existing Starlette/httpx deprecation warning.


## M14.2 production trust-root ceremony checkpoint — 2026-08-27

Implemented the approval-gated `ProductionTrustRootCeremony` workflow with canonical out-of-band SHA-256 pin verification, signed-root bootstrap, increasing-version rotation, reasoned revocation records, atomic trust/evidence writes, and secret-free status evidence. Added 3 focused tests, a non-secret configuration example, and operator documentation. Full regression validation passes 295 tests with one existing Starlette/httpx deprecation warning. The live operator ceremony, production root material, out-of-band approval, and rotation/revocation drill remain pending.


## M14.3 sandbox validation checkpoint — 2026-08-27

Targeted security and sandbox tests passed 15 tests. The attached Windows 11 Pro build 26200 host had no discoverable WindowsSandbox.exe or wsl.exe, and the available Linux host had no bwrap/bubblewrap runtime. Live runtime enforcement therefore remains pending; evidence is retained in artifacts/m14_3_sandbox_validation_2026-08-27.md. Full regression suite passes 295 tests with one existing Starlette/httpx deprecation warning.


## M14.4 enterprise identity checkpoint — 2026-08-27

Implemented tenant-scoped identity claims and least-privilege authorization with bounded claim lifetimes, active membership grants, explicit approval references for sensitive actions, revocation, unknown-action denial, and secret-free authorization audit records. Evidence: `orville_core/enterprise_identity.py`, `tests/test_enterprise_identity.py`, and `docs/M14_ENTERPRISE_IDENTITY.md`. Full regression suite passes 297 tests with one existing Starlette/httpx deprecation warning. Live OIDC/SAML gateway integration, MFA, issuer/audience verification, and production revocation propagation remain pending.

## 2026-08-27 — Managed-first cloud onboarding and OAuth boundary

TODO 395 and 397 are complete locally. `cloud_onboarding.py`, the authenticated onboarding route, and accessible Signal Room fallback content establish managed cloud as the default, keep Blackbox account connection optional, and expose an explicit optional connection action. Focused onboarding tests passed, Signal Room static checks passed with the existing contrast warning, the full regression suite passed 347 tests, and compilation passed. TODO 401 was immediately evaluated and marked blocked because official Blackbox OAuth/device-authorization semantics remain unconfirmed; no external authorization, credentials, or account action was used.


## 2026-08-27 — Managed-cloud default-access explanation

TODO 399 is complete locally. The managed-first onboarding contract exposes the user-facing `privacy_notice`, and the accessible Signal Room fallback explains that default access is provided through Orville managed cloud access subject to Orville service limits, privacy terms, and availability. Added a focused regression assertion in `tests/test_cloud_onboarding.py`. Validation passed: focused onboarding tests (2), Python compilation, and Signal Room static checks; the existing WCAG contrast finding remains a warning. No external credentials, authorization, or account action was used.

Current worker: Orchestration Agent. Next eligible TODO item: 403, subject to the existing OAuth/device-authorization blocker at TODO 401 and the in-progress account-action item at TODO 397.

Known limitation: the compiled Signal Room bundle has no editable source project in this copy; the accessible no-script fallback is the maintained user-visible guidance for this checkpoint.

> Control-file update: TODO 399 is marked `[x]` only after focused validation satisfied its acceptance criteria.



## 2026-08-27 — Blackbox connection lifecycle actions

TODO 405 is complete locally. The onboarding contract now exposes test, provider/model selection entry point, credential replacement, disconnect, and credential deletion actions. Added a local credential-free connection-test route and a credential-deletion route that preserves managed access and local mode; replacement remains the existing API-key connection operation. Focused onboarding/cloud-relay API tests passed (7), Python compilation passed, and Signal Room static checks passed with the existing contrast warning. No credentials or external account action was used.

Current worker: Orchestration Agent. Next eligible TODO item: 407.


## 2026-08-27 — Blackbox subscription and usage disclosure

TODO 407 is complete locally. The onboarding contract and accessible Signal Room fallback disclose that connecting a Blackbox account may require an eligible subscription and may incur usage charges under Blackbox account terms, with a direct official terms link. Focused onboarding/cloud-relay API tests passed (7), Python compilation passed, and Signal Room static/link checks passed with the existing contrast warning. No credentials or external account action was used.

Current worker: Orchestration Agent. Next eligible TODO item: 409.


## 2026-08-27 — Blackbox disconnect state preservation

TODO 409 is complete locally. The disconnect API now explicitly reports that managed access, local mode, and unrelated task state remain unchanged; focused regression coverage passed alongside compilation and Signal Room static checks. The existing contrast warning remains non-blocking. No credentials or external account action was used.

Current worker: Orchestration Agent. Next eligible TODO item: 411.


## 2026-08-27 — Pre-execution provider and privacy context

TODO 411 is complete locally. Cloud admission now returns a redacted summary of active provider, model, endpoint family, privacy mode, and remote execution location before work is admitted; provider credentials remain excluded. Focused onboarding/cloud-relay API tests passed (7), Python compilation passed, and Signal Room static checks passed with the existing contrast warning. No credentials or external account action was used.

Current worker: Orchestration Agent. Next eligible TODO item: 415.


## 2026-08-27 — Blackbox secret-free persistence boundary

TODO 419 is complete locally. Documentation and regression coverage enforce that Blackbox credentials do not enter environment files, project files, checkpoints, prompts, artifacts, screenshots, crash reports, or source control; persisted connection metadata remains secret-free and tests use synthetic credentials. Focused credential, relay, onboarding, and API tests passed (24), compilation passed, and policy checks passed. The existing HTTP-client deprecation warning remains non-blocking.

Current worker: Orchestration Agent. Next eligible TODO item: 421.


## 2026-08-27 — Blackbox log and telemetry redaction

TODO 421 is complete locally. `SecretScanner` now redacts sensitive fields and values, bearer authorization headers, token-shaped values, account identifiers, and embedded provider-error data. The first validation exposed an account-identifier gap; the scanner was corrected and the rerun passed 24 focused tests plus compilation. No credentials were used; the existing HTTP-client deprecation warning remains non-blocking.

Current worker: Orchestration Agent. Next eligible TODO item: 423.


## 2026-08-27 — Blackbox authentication shortcut prohibition

TODO 423 is complete locally. The onboarding contract now declares API-key-only authentication and explicitly forbids browser-cookie capture, undocumented session endpoints, private web APIs, and shared Orville-owned credentials. Focused onboarding, redaction, relay, and API tests passed (24), compilation passed, and policy-document checks passed. No browser session, credential, or external account action was used.

Current worker: Orchestration Agent. Next eligible TODO item: 425.


## 2026-08-27 — Explicit privacy routing controls

TODO 425 is complete locally. Durable privacy routing now covers `local_only`, `cloud_approved`, and `restricted`; local-only behavior is enforced for local-only and restricted data, while cloud-approved routing can allow configured fallback. Expanded API regression coverage passed with 31 focused tests and compilation. No external credentials or remote account action was used.

Current worker: Orchestration Agent. Next eligible TODO item: 427.


## 2026-08-27 — Default secret-path exclusion from workspace context

TODO 427 is complete locally. Workspace creation and context indexing now exclude `.env` files, private-key suffixes, credential/secret paths, and related secret directories by default. Regression coverage passed across workspace, API, relay, onboarding, and redaction suites (35 tests), and compilation passed. No credentials or external account action was used.

Current worker: Orchestration Agent. Next eligible TODO item: 429.


## 2026-08-27 — User-visible remote-content confirmation

TODO 429 is complete locally. Onboarding exposes confirmation scope for workspace files, repository content, images, audio, video, and tool results, while cloud admission rejects workspace data without explicit `approved_remote` confirmation. Focused onboarding, cloud, privacy, workspace, and redaction tests passed (35), compilation passed, and Signal Room checks passed with the existing contrast warning.

Current worker: Orchestration Agent. Next eligible TODO item: 431.


## 2026-08-27 — Endpoint and callback validation boundary

TODO 431 is complete locally. Blackbox endpoint validation enforces HTTPS, credential-free URLs, documented allowlisted hosts, positive timeouts, and model/capability metadata; onboarding records callback-state and token-expiry requirements if an official flow is ever confirmed. Focused Blackbox contract, endpoint, onboarding, cloud, and security tests passed (33), compilation passed, and Signal Room checks passed with the existing contrast warning.

Current worker: Orchestration Agent.


## 2026-08-27 — Credential references and provider permissions

TODO 439 is complete locally. Added value-free credential references with active/expired/revoked lifecycle checks, provider-specific action/scope authorization, and stronger token/account redaction. Focused security, secrets, onboarding, relay, API, privacy, and workspace tests passed (42), and compilation passed. The existing HTTP-client deprecation warning remains non-blocking.

Current worker: Orchestration Agent. Next eligible TODO item: 445.


## 2026-08-27 — Complete provider configuration schema

TODO 445 is complete locally. `ProviderConfig` now validates and redacts authentication method, endpoint family, base URL, model, account/plan state, capabilities, privacy mode, timeout, and enabled state. Provider, API, onboarding, relay, security, and workspace tests passed (63), and compilation passed. No credentials or external account action was used.

Current worker: Orchestration Agent. Next eligible TODO item: 451.


## 2026-08-27 — OAuth/device-flow boundary

TODO 465 is complete locally. The onboarding contract explicitly keeps official OAuth/device authentication unimplemented and unadvertised until a documented, verified third-party flow exists; unverified OAuth/device flow is now listed as forbidden. Focused onboarding, API, cloud, and security tests passed (36), compilation passed, and no OAuth endpoint is advertised.

Current worker: Orchestration Agent. Next eligible TODO item: 467.


## 2026-08-27 — API-key validation and actionable provider errors

TODO 467 is complete locally. Provider HTTP failures now map 401, 402, 403, 429, timeout, and endpoint failures to actionable, secret-free error categories. Focused provider, Blackbox contract, cloud, onboarding, security, and redaction tests passed (61), and compilation passed. No live provider request or external credential was used.

Current worker: Orchestration Agent. Next eligible TODO item: 469.


## 2026-08-27 — Secret-free API state and exports

TODO 469 is complete locally. End-to-end coverage confirms synthetic API keys are absent from redacted exports, state responses, checkpoint files, provider exceptions, and redacted telemetry. The full focused suite passed 67 tests and compilation passed. No external provider request or credential was used.

Current worker: Orchestration Agent. Next eligible TODO item: 471.


## 2026-08-27 — Pre-execution capability reporting

TODO 471 is complete locally. Relay configuration and cloud admission now expose disjoint supported and unsupported capability lists before execution, with regression coverage across cloud, provider, API, onboarding, security, and redaction suites. Validation passed with the existing HTTP-client deprecation warning only.

Current worker: Orchestration Agent. Next eligible TODO item: 473.


## 2026-08-27 — Local fallback preservation

TODO 473 is complete locally. Fallback policy coverage confirms configured local providers remain available for disconnected, expired, invalid, rate-limited/quota, unavailable, and disabled relay states, while ready managed access is not replaced. Cloud and provider regression validation passed with no external calls.

Current worker: Orchestration Agent. Next eligible TODO item: 475.

## 2026-08-27 — Credential redaction security review checkpoint

TODO 469 and TODO 477 are complete locally. `SecretRedactor` now protects structured values, bearer/query-style secrets, exception messages, and both file-backed and SQLite checkpoint payloads. The independent `tools/security_review.py` checker passed in isolated Python mode using synthetic credentials only. Focused security tests passed 11, the full regression suite passed 359 tests with one existing HTTP-client deprecation warning, and compilation passed. No external credentials or side effects were used.


## 2026-08-27 — Managed/user routing and privacy integration

TODO 497 is complete locally. Managed-relay routing, user-connected routing, privacy policies, workspace context manifests, explicit remote approval, and local fallback are integrated and validated by 57 focused tests plus compilation. No external provider request or credential was used.

Current worker: Orchestration Agent. Next eligible TODO item: 499.


## 2026-08-27 — GUI connection lifecycle controls

TODO 499 is complete locally. The accessible Signal Room fallback exposes provider/model configuration, connection diagnostics, optional API-key connection, disconnect, and credential deletion controls. Static Signal Room checks and 70 focused tests passed; two pre-existing contrast warnings and the HTTP-client deprecation warning remain non-blocking.

Current worker: Orchestration Agent. Next eligible TODO item: 505.


## 2026-08-27 — Phase 4 verification and delivery checkpoint

TODO 543, 545, 547, 553, 555, 557, 559, 561, 565, and 567 are complete locally. Added provider/relay external-boundary integration tests, startup/main-workflow/expected-failure smoke coverage, independent-review evidence, a sanitized validation record, and `docs/DELIVERY_RUNBOOK.md`. Updated `TODO.md` and `CHANGELOG.md`.

Validation: full pytest suite passed 365 tests; unittest discovery passed 159 tests; Python compileall passed; Signal Room smoke/accessibility checks passed; isolated `examples/basic_run.py` completed and persisted one checkpoint. Ruff, Black, mypy, isort, and flake8 are not configured in the supplied environment. Existing Starlette/httpx deprecation and unittest resource warnings remain non-blocking. No live provider request, external credential, account action, or destructive operation was used.

Changed paths: `tests/test_external_boundaries.py`, `tests/test_smoke_workflow.py`, `artifacts/phase4-independent-review.md`, `artifacts/phase4-validation-record.md`, `docs/DELIVERY_RUNBOOK.md`, `TODO.md`, `CHANGELOG.md`, `STATE.md`.

Assumptions and boundary: the supplied workspace is not a Git working tree, so commit/status inspection was unavailable. Official third-party Blackbox OAuth remains blocked pending documented provider flow; live deployment and provider verification remain deployment-owned.

Current worker: Orchestration Agent. Next eligible TODO item: 569.


## Frontend-backend contract checkpoint — 2026-08-27

The selected Phase 6 web/mobile item is complete as a local contract. `docs/FRONTEND_BACKEND_CONTRACTS.md` defines the `/api/v1` route surface, stable response/error envelopes, operation identifiers, safe end-user messages, frontend token-storage boundaries, runtime configuration, environment-variable ownership, bounded timeout/retry behavior, and staging/production deployment controls. `config/frontend-backend.example.json` provides a non-secret example, and `tests/test_frontend_backend_contract.py` verifies the fixture, route/environment documentation, bounded operation names, and synthetic secret-redaction expectations.

Validation passed: 3 focused unittest cases, JSON parsing, and Python compilation. No credentials, external services, or destructive actions were used. TLS termination, durable identity, CORS enforcement, rate limiting, secret injection, and production frontend hosting remain deployment-owned controls; the repository contains the contract and local example only.


## Project initialization rules checkpoint — 2026-08-27

Worker Task 2 completed the Phase 6 web/mobile initialization contract in `docs/PROJECT_INITIALIZATION_RULES.md`. The contract defines the required initialization record, fail-closed ambiguity handling, common stages, and separate rules for `static_site`, `full_stack_web`, and `mobile_application`, including runtime, configuration, data/auth, quality, preview, delivery, and external-side-effect boundaries. Focused tests passed (4) and Python compilation passed for `tests/test_project_initialization_rules.py`. Generated-project build, test, preview, deployment, and platform-tool validation remain profile-specific and are not claimed by this documentation contract.

Assumptions: the repository's existing Python/unittest conventions remain authoritative, and profile-specific generated projects will provide their own framework commands. No credentials, external services, or destructive actions were used.

Unresolved risks: the rules are documented and structurally tested, but no framework-specific scaffolder or generated application was changed in this task.


## Web and mobile acceptance-criteria checkpoint — 2026-08-27

The selected Phase 6 web/mobile item is complete as a local quality contract. `docs/WEB_MOBILE_ACCEPTANCE_CRITERIA.md` defines target viewport classes, responsive reflow and touch criteria, WCAG 2.2 Level AA accessibility checks, keyboard and assistive-technology requirements, secret-safe frontend security controls, API and artifact boundary checks, production security headers, and measurable performance budgets for LCP, INP, CLS, transfer size, bounded requests, and mobile resource use. `tests/test_web_mobile_acceptance_criteria.py` verifies the required quality domains, target matrix, measurable thresholds, unique acceptance IDs, and explicit secret-exclusion language.

Validation passed: 3 focused unittest cases and Python compilation. No credentials, external services, or destructive actions were used. Live device coverage, production telemetry, deployment headers, assistive-technology sessions, and real network measurements remain release-evidence responsibilities for future web/mobile implementations.


## Asset lifecycle procedures checkpoint — 2026-08-27

Worker Task 2 completed the Phase 6 media asset procedure contract in `docs/ASSET_LIFECYCLE_PROCEDURES.md`. It defines versioned asset briefs, generation/editing custody, source preservation, licensing and provenance states, deterministic naming, storage classes, manifest requirements, approvals, and separate technical, quality, accessibility, rights, security, and delivery checks. Focused tests passed (4) and Python compilation passed for `tests/test_asset_lifecycle_procedures.py`.

Assumptions: asset-specific generation runtimes and provider terms are supplied by the downstream task; this change defines framework-neutral custody and verification rules only. No credentials, external services, or destructive actions were used.

Unresolved risks: the procedure is documented and structurally tested, but no media-generation adapter, format-specific validator, or asset repository was changed in this task. Rights evidence remains task- and provider-specific.


## Operation-aware API error checkpoint — 2026-08-27

The selected Phase 4 implementation item is complete locally. `orville_core/api.py` now provides centralized FastAPI handlers for HTTP and request-validation failures. Responses include a stable `error` envelope with a machine-readable status code, an operation name derived from the route template, a bounded retryable flag, and an end-user message such as `post_objectives failed: the request is invalid.` The legacy `detail` field is retained with the same safe message for compatibility. Dynamic unmatched-route path values are replaced with a safe `resource` marker, and payloads/details are never echoed.

`tests/test_api_error_messages.py` covers invalid authentication, invalid objective payloads containing a synthetic API key, and missing resources containing a sensitive path value. Focused validation passed: 3 tests and Python compilation for `orville_core/api.py` and the focused test module. The existing HTTP-client deprecation warning remains non-blocking. No live credentials, external services, or destructive actions were used.


## Automated build, test, and preview checkpoint — 2026-08-27

Worker Task 2 completed the Phase 6 automation procedure item. `tools/project_checks.py` now provides standalone `build`, `test`, `preview`, and `all` modes. `docs/BUILD_TEST_PREVIEW.md` documents prerequisites, expected outputs, loopback-only API preview smoke behavior, safety boundaries, and failure evidence handling. Focused automation tests passed (4), Python compilation passed, the credential-free preview check passed with existing contrast warnings, and the build mode compiled sources and produced `orville_core-0.1.0-py3-none-any.whl` under `tmp/project-check-wheels/`.

The full test mode was invoked but remains red on an unrelated pre-existing failure in `orville_core/api.py`: `Request.__init__()` rejects the existing `headers` keyword and the exception handler references an undefined `HTTPError`. Evidence is retained at `tmp/project_checks_failure.txt`; this task did not modify unrelated API code.

Assumptions: local development dependencies and the existing repository test configuration remain authoritative. The optional API preview smoke requires a user-provided `.env.production` token and a running loopback API; no credential or external service was used.

Unresolved risks: the wrapper correctly fails when the regression suite fails, so `all` cannot be claimed green until the pre-existing API failure is repaired by a separate scoped task. Contrast warnings remain reported by the existing UI checker.


## Media provenance checkpoint — 2026-08-27

The selected Phase 6 media item is complete as a local contract. `orville_core/media_provenance.py` provides `MediaProvenanceStore`, checksum-addressed `MediaAsset` records, ordered `MediaTransformation` records, and redacted `MediaHistoryRecord` persistence. Source and generated files are copied beneath a bounded provenance root without modifying caller-owned files; prompts and metadata pass through `SecretRedactor`, while a prompt digest supports reproducibility checks without retaining secret values. The public package exports the new contracts, and `docs/MEDIA_PROVENANCE.md` documents the layout and workflow.

Validation passed: 3 focused media-provenance unittest cases, Python compilation for the new module, focused tests, and package public-import verification. No credentials, external services, or destructive actions were used. Multi-process locking, remote object storage, signing, and media-specific perceptual hashes remain future hardening or deployment work.


## Document templates checkpoint — 2026-08-27

Worker Task 2 completed the Phase 6 document-template item in `docs/DOCUMENT_TEMPLATES.md`. The contract defines shared metadata and four Markdown templates for reports, specifications, runbooks, and research outputs, with evidence, acceptance, security, approval, validation, rollback, citation, and lifecycle requirements. Focused tests passed (4) and Python compilation passed for `tests/test_document_templates.py`.

Assumptions: existing detailed research templates remain compatible and authoritative for research-specific records; the new document defines the shared minimum contract and does not replace those files. No credentials, external services, or destructive actions were used.

Unresolved risks: template completeness is structurally tested, but rendered-document layout, citation correctness, and domain-specific human review remain deliverable-specific.


## Media validation checkpoint — 2026-08-27

The selected Phase 6 media item is complete as a local validation contract. `orville_core/media_validation.py` provides modality policies and stable validation results for format allowlists, file-size bounds, declared resolution, duration, image alt text, audio/video transcript or captions, and license, rights-holder, and source metadata. `docs/MEDIA_VALIDATION_CHECKS.md` documents the checks, evidence sequence, default formats, and limitations. The public package exports `MediaValidationPolicy`, `MediaValidationResult`, and `validate_media`.

Validation passed: 5 focused media-validation unittest cases, Python compilation, and public-import verification. No credentials, external services, or destructive actions were used. The checker does not decode codecs, transcribe media, assess caption quality, validate remote rights pages, or certify legal clearance; those remain pipeline or review responsibilities.


## Presentation procedures checkpoint — 2026-08-27

Worker Task 2 completed the Phase 6 presentation-procedure item in `docs/PRESENTATION_PROCEDURES.md`. The contract defines a versioned deck brief, narrative and evidence planning, content validation, design-system consistency, accessibility checks, export verification for editable/PDF/web formats, delivery manifests, approvals, and handoff rules. Focused tests passed (4) and Python compilation passed for `tests/test_presentation_procedures.py`.

Assumptions: presentation generation and export engines remain downstream adapters; this task defines the framework-neutral planning and verification contract without producing a deck. No credentials, external services, or destructive actions were used.

Unresolved risks: rendered slide legibility, exporter-specific fidelity, citation correctness, and rights review require a deck-specific verification pass after generation.


## Editable source preservation checkpoint — 2026-08-27

Worker Task 2 completed the Phase 6 editable-source preservation item in `docs/EDITABLE_SOURCE_PRESERVATION.md`. The contract defines source/export manifests, immutable source versions, derivative relationships, no-source fallback, deterministic naming, storage boundaries, fidelity checks, approvals, and handoff evidence. Focused tests passed (4) and Python compilation passed for `tests/test_editable_source_preservation.py`.

Assumptions: downstream presentation and media exporters provide the source and derivative metadata required by the manifest; this task defines preservation rules without implementing an exporter or artifact store. No credentials, external services, or destructive actions were used.

Unresolved risks: exporter-specific fidelity, format support, rights evidence, and actual source recovery require artifact-specific verification after generation.


## Document and presentation verification checkpoint — 2026-08-27

The selected document-workflow item is complete as a local verification contract. `orville_core/document_verification.py` provides deterministic checks for Markdown, PDF, and PPTX format, page or slide counts, numeric citations, links, charts, images, alt text, and basic Markdown legibility. It reports stable findings and explicitly refuses to claim rendered PDF/PPTX legibility without a visual render review. `docs/DOCUMENT_VERIFICATION.md` documents the contract, evidence procedure, and limitations; the public package exports the policy, result, and verifier.

Validation passed: 5 focused document-verification unittest cases, Python compilation, and public-import verification. No credentials, external services, or destructive actions were used. Remote-link reachability, citation quality, PDF/PPTX rendering, OCR, font-size inspection, contrast, clipping, and human accessibility review remain separate verification responsibilities.


## GUI information architecture checkpoint — 2026-08-27

Worker Task 2 completed the GUI product-experience item defining target users, primary workflows, navigation, information architecture, and user journeys in `docs/GUI_INFORMATION_ARCHITECTURE.md`. The contract covers Builder, Operator, Reviewer, and Project owner roles; readiness, objective execution, verification, artifact delivery, and recovery workflows; stable navigation and object hierarchy; contextual detail layout; and journey-specific acceptance criteria. Focused tests passed (4) and Python compilation passed for `tests/test_gui_information_architecture.py`.

Assumptions: the contract describes the intended GUI information architecture without changing the existing GUI implementation; hosted collaboration, live browser control, and deployment remain separate gated capabilities. No credentials, external services, or destructive actions were used.

Unresolved risks: visual design, wireframes, implemented route coverage, and live accessibility behavior require subsequent GUI-specific tasks and verification.


## Visual design-system checkpoint — 2026-08-27

The selected product-experience item is complete as a shared design contract. `config/design-system.example.json` defines light/dark semantic colors, typography, spacing, elevation, icon sizing, control dimensions, motion, and responsive breakpoints. `docs/VISUAL_DESIGN_SYSTEM.md` defines component states and interaction patterns for buttons, inputs, forms, tables, cards, notifications, dialogs, empty states, status indicators, and navigation, plus theme, accessibility, responsive, security, and review requirements. `tests/test_visual_design_system.py` verifies token completeness, theme roles, touch-target minimums, component coverage, state coverage, and security/responsive boundaries.

Validation passed: 3 focused unittest cases, JSON parsing, and Python compilation. No credentials, external services, or destructive actions were used. Existing GUI/web clients are not claimed as fully migrated; wireframes, high-fidelity mockups, and implementation-level visual regression evidence remain subsequent roadmap items.


## GUI wireframes and high-fidelity mockup checkpoint — 2026-08-27

Worker Task 2 completed the GUI pre-implementation visual artifact item. `docs/GUI_WIREFRAMES.md` defines low-fidelity layouts for the primary surfaces and responsive/state behavior. `docs/mockups/orville-control-center.html` provides a standalone high-fidelity control-center mockup aligned with the existing design tokens, semantic structure, responsive thresholds, focus behavior, reduced motion, and touch-target rules. Focused tests passed (4) and Python compilation passed for `tests/test_gui_wireframes_mockup.py`.

Assumptions: the artifacts are reviewable design contracts and a standalone prototype, not a production GUI implementation. No credentials, external services, or destructive actions were used.

Unresolved risks: visual comparison across browsers, implemented route coverage, full keyboard/screen-reader testing, and user research validation require later GUI implementation and review tasks.


## Polished visual-style checkpoint — 2026-08-27

The selected product-experience item is complete as a style and review contract. `config/visual-style.example.json` operationalizes the design system with professional/modern/clear voice qualities, stable hierarchy, one-primary-action composition, compact-readable density, performance budgets, 44 px touch targets, focus and loading safeguards, and explicit review gates. `docs/VISUAL_STYLE_GUIDE.md` defines the visual language, composition, hierarchy, status semantics, performance posture, accessibility/usability posture, responsive behavior, and migration boundary. `tests/test_visual_style_guide.py` verifies profile safeguards and required guide coverage.

Validation passed: 3 focused unittest cases, JSON parsing, and Python compilation. No credentials, external services, or destructive actions were used. Existing clients are not claimed as fully migrated; rendered visual regression, live accessibility review, and performance telemetry remain subsequent implementation gates.


## Theme preferences and status indicators checkpoint — 2026-08-27

Worker Task 2 completed the GUI theme and status-indicator item. The standalone mockup now supports light and dark semantic tokens, an accessible theme toggle, local preference persistence restricted to `light` or `dark`, fallback for invalid preferences, reduced-motion behavior, and text-backed status indicators. `docs/THEME_AND_STATUS_BEHAVIOR.md` records the contract and verification gates. Focused tests passed (4) and Python compilation passed for `tests/test_theme_and_status_behavior.py`.

Assumptions: the mockup is the current implementation surface for this task; other GUI clients must adopt the same semantic roles and preference boundaries. No credentials, external services, or destructive actions were used.

Unresolved risks: cross-browser storage behavior, system-preference integration, complete dark-theme contrast review, and adoption by the desktop GUI remain subsequent implementation and accessibility tasks.


## Operational dashboard checkpoint — 2026-08-27

The selected GUI workflow item is complete as a desktop implementation. `windows_gui.py` now renders six bounded aggregate cards for active tasks, recent runs, model availability, system health, failures, and generated artifacts. It refreshes asynchronously through the existing health, state, providers, and artifacts routes, preserves the existing composer and context panels, and degrades to safe values without displaying raw errors, payloads, provider configuration, or credentials. `docs/DASHBOARD_SPECIFICATION.md` records the card contract and behavior; `tests/test_dashboard.py` provides focused coverage.

Validation passed: 3 focused dashboard unittest cases and Python compilation for `windows_gui.py` and the test module. No credentials, external services, or destructive actions were used. The dashboard does not yet provide per-provider live health, web/mobile parity, or rendered visual regression evidence.


## Task composer checkpoint — 2026-08-27

Worker Task 2 completed the core GUI task-composer item in `docs/mockups/task-composer.html`. The standalone prototype captures software requirements, deliverables, existing context, local file references, target environment, constraints, model preference, and acceptance criteria. It supports local draft persistence, reset behavior, review gating, and structured payload preview without external requests or credential capture. Focused tests passed (4) and Python compilation passed for `tests/test_task_composer.py`.

Assumptions: this task delivers a standalone prototype and interaction contract; integration with the production GUI, backend task creation, upload service, provider inventory, and execution graph remains downstream work. No credentials, external services, or destructive actions were used.

Unresolved risks: browser-level file handling, backend validation, large-file limits, model capability discovery, authenticated project persistence, and full accessibility testing require subsequent integration tasks.

**Phase 6 task-plan view checkpoint - 2026-08-27:** docs/TASK_PLAN_VIEW.md defines the task-plan projection model, dependency and assignment presentation, status semantics, blocker/retry/verification details, safe interactions, accessibility fallback, and bounded rendering requirements. Three focused tests, Python compilation, structural checks, and secret-safe wording checks passed. The existing GUI does not claim this view is implemented; live visual regression remains a follow-up gate.

**Phase 6 imported-model workflow checkpoint - 2026-08-27:** docs/IMPORTED_MODEL_WORKFLOW.md defines local file/folder selection, reference/copy/link storage, metadata scanning, compatibility validation, activation approval, stable diagnostics, lifecycle states, and safe deactivation/removal. Three focused tests, Python compilation, structural checks, and secret-safe wording checks passed. Live GPU/runtime provisioning, provider upload, and full GUI integration remain outside the local contract.


## Model manager checkpoint — 2026-08-27

The selected GUI workflow item is complete as a unified desktop entry point. `windows_gui.py` now labels the local inventory window as **Model Manager**, documents support for cloud providers, endpoint-based models, Ollama servers, and imported local files, and provides direct **Provider setup** and **Import local model** actions alongside inventory refresh, validation, activation, deactivation, and registration-removal controls. `docs/MODEL_MANAGER_SPECIFICATION.md` records the source workflows and safety boundaries; `tests/test_model_manager.py` provides focused coverage.

Validation passed: 3 focused model-manager unittest cases and Python compilation for `windows_gui.py` and the test module. No credentials, external services, or destructive actions were used. Runtime provider health, endpoint reachability, compatibility, license, and attestation checks remain API-owned.


## Secret-safe model configuration checkpoint — 2026-08-27

Worker Task 2 completed the model configuration flow item in `docs/mockups/model-configuration.html`. The standalone prototype provides canonical provider presets, endpoint and model validation, masked credential input, redacted review, credential clearing after save, explicit health-check review, and approval messaging. `docs/MODEL_CONFIGURATION_FLOW.md` records configuration states and secret-safe boundaries. Focused tests passed (4) and Python compilation passed for `tests/test_model_configuration_flow.py`.

Assumptions: the prototype delegates persistence, secret storage, endpoint policy, and health requests to the approved local API or standalone adapter; no network request is made by the preview. No credentials, external services, or destructive actions were used.

Unresolved risks: production secret-store integration, endpoint allowlisting, provider capability discovery, authenticated persistence, and complete desktop GUI integration require subsequent tasks.


## Capability-aware generation workspace checkpoint — 2026-08-27

Worker Task 2 completed the generation workspace item in `docs/mockups/generation-workspace.html`. The standalone prototype supports text, code, image, audio, video, vision, embedding, and other capabilities; filters compatible models from declared capability metadata; surfaces modality-specific inputs and outputs; persists only local drafts; provides redacted request review; and separates review from explicit execution. `docs/GENERATION_WORKSPACE.md` records the modality, lifecycle, compatibility, evidence, and safety contract. Focused tests passed (4) and Python compilation passed for `tests/test_generation_workspace.py`.

Assumptions: the prototype delegates generation to an approved adapter and makes no network request or external side effect. Backend execution, provider capability discovery, artifact persistence, and authenticated project integration remain downstream work. No credentials, external services, or destructive actions were used.

Unresolved risks: actual modality support, model parameter validation, large-file limits, content policy enforcement, streaming progress, and output fidelity require adapter-specific and integration testing.


## Execution monitor checkpoint — 2026-08-27

The selected GUI workflow item is complete as a bounded desktop implementation. `windows_gui.py` now exposes an Execution Monitor from the Active tasks and Recent activity navigation entries. The monitor polls persisted run checkpoints and event history, renders task progress, agent/task activity, tool event classifications, elapsed time derived from event timestamps, and at most 80 event rows. It provides Refresh, Pause monitor, Resume waiting task, Retry run, and Cancel run controls while suppressing raw payloads, event details, exceptions, and credentials. `docs/EXECUTION_MONITOR_SPECIFICATION.md` defines the data and control contract; `tests/test_execution_monitor.py` provides focused coverage.

Validation passed: 3 focused execution-monitor unittest cases and Python compilation for `windows_gui.py` and the test module. No credentials, external services, or destructive actions were used. Pause controls observation polling; backend hard pause and cooperative handler interruption remain future engine work.


## Artifact browser checkpoint — 2026-08-27

Worker Task 2 completed the artifact-browser item in `docs/mockups/artifact-browser.html`. The standalone prototype supports artifact search and type/status filtering, safe local preview, source/export metadata, download preparation, explicit export, version comparison, and non-destructive revision actions. `docs/ARTIFACT_BROWSER.md` records artifact states, validation, organization, versioning, and approval boundaries. Focused tests passed (4) and Python compilation passed for `tests/test_artifact_browser.py`.

Assumptions: the prototype operates on local sample metadata and delegates real storage, authorization, export, and retrieval to downstream approved services. No external transfer, publication, deletion, or destructive action is performed by the preview. No credentials or external services were used.

Unresolved risks: production artifact indexing, access control, large-file handling, safe rendering of untrusted content, checksum enforcement, and backend download/export integration require subsequent implementation and security testing.


## Verification and review checkpoint — 2026-08-27

The selected GUI workflow item is complete as a bounded desktop review surface. `windows_gui.py` now exposes Verification from the workspace navigation and loads persisted run evidence into sections for acceptance criteria, test results, source evidence, visual checks, defects, residual risks, and approval state. Values are bounded to 4,000 characters per section, run IDs are encoded, and unavailable runs receive a generic recovery message. `docs/VERIFICATION_REVIEW_SPECIFICATION.md` defines the evidence contract; `tests/test_verification_review.py` provides focused coverage.

Validation passed: 3 focused verification-review unittest cases and Python compilation for `windows_gui.py` and the test module. No credentials, external services, or destructive actions were used. The view records evidence and does not itself certify source quality, visual accessibility, OCR, pixel comparison, or approval authorization.


## Settings workspace checkpoint — 2026-08-27

Worker Task 2 completed the settings item in `docs/mockups/settings-workspace.html`. The standalone prototype provides sections for providers/models, privacy routing, storage paths, resource limits, schedules, notifications, and user preferences, with local allowlisted persistence, bounded numeric controls, reset behavior, protected credential references, and approval messaging. `docs/SETTINGS_WORKSPACE.md` records the contract. Focused tests passed (4) and Python compilation passed for `tests/test_settings_workspace.py`.

Assumptions: the prototype delegates authenticated persistence, secret storage, endpoint policy, schedule execution, and notification delivery to approved services; no external action is performed by the preview. No credentials, external services, or destructive actions were used.

Unresolved risks: backend schema and authorization enforcement, path validation, scheduler durability, notification redaction, and desktop GUI integration require subsequent implementation and security testing.


## Plain-language workflow checkpoint — 2026-08-27

The selected usability item is complete. `windows_gui.py` now leads with a plain-language objective prompt, explains the workflow through **How Orville works**, and maps navigation to progress, model selection, and verification without requiring framework terminology. `docs/PLAIN_LANGUAGE_WORKFLOWS.md` defines the Describe/Prepare/Work/Review path, maps technical terms to user-facing wording, and preserves safety/accessibility rules. `tests/test_plain_language_workflows.py` provides focused coverage.

Validation passed: 3 focused plain-language workflow unittest cases and Python compilation for `windows_gui.py` and the test module. No credentials, external services, or destructive actions were used. Advanced technical terminology remains available in specialist views; the primary path does not claim to remove those capabilities.


## Progressive disclosure checkpoint — 2026-08-27

The selected usability item is complete as a bounded desktop implementation. `windows_gui.py` now keeps provider setup focused on provider type and model name by default, while provider ID, endpoint, masked API key, timeout, capabilities, and privacy policy remain behind an explicit reversible `Show advanced options` control. Entered values are preserved when the disclosure is toggled, and existing approval, credential, recovery, and accessibility boundaries remain unchanged. `docs/PROGRESSIVE_DISCLOSURE.md` defines the disclosure model and acceptance checks; `tests/test_progressive_disclosure.py` provides focused coverage.

Validation passed: 3 focused progressive-disclosure unittest cases and Python compilation for `windows_gui.py` and the test module. No credentials, external services, or destructive actions were used. Model-manager runtime and attestation controls remain a follow-up disclosure surface rather than being changed in this task.


## GUI accessibility checkpoint — 2026-08-27

The selected accessibility item is complete as a bounded desktop implementation. `windows_gui.py` now provides native Tab traversal, Alt+1 objective focus, Alt+2 workflow help, Escape shell focus, visible focus borders for buttons and text controls, explicit objective-workspace keyboard guidance, and secret-safe operation-specific recovery feedback. The desktop path uses no animated transitions for accessibility feedback. `docs/GUI_ACCESSIBILITY.md` defines the keyboard, focus, semantic-label, contrast, reduced-motion, and error-feedback contract; `tests/test_gui_accessibility.py` provides focused coverage.

Validation passed: 3 focused GUI accessibility unittest cases and Python compilation for `windows_gui.py` and the test module. No credentials, external services, or destructive actions were used. Full screen-reader, platform-specific keyboard, rendered contrast measurement, and web/mobile parity reviews remain environment-dependent follow-up gates.


## Responsive layout checkpoint — 2026-08-27

The selected responsive-layout item is complete as a bounded native desktop implementation. `windows_gui.py` now reflows dashboard cards from three columns at widths of 1080 px and above, to two columns at 790–1079 px, and to one column below 790 px. Card labels wrap within bounded widths, the refresh action follows the final row, the context rail collapses below 980 px, and the sidebar collapses below 790 px while the primary objective workspace remains available. `docs/RESPONSIVE_LAYOUTS.md` defines the width behavior and review boundaries; `tests/test_responsive_layouts.py` provides focused coverage.

Validation passed: 3 focused responsive-layout unittest cases and Python compilation for `windows_gui.py` and the test module. No credentials, external services, or destructive actions were used. Pixel-level visual review, OS-specific font metrics, and web/mobile parity remain environment-dependent follow-up gates.


## Worker Task 2 checkpoint — Help, errors, onboarding, and recovery guidance — 2026-08-27

The selected Phase 6A item is complete as a local contract and prototype. `docs/HELP_AND_RECOVERY_GUIDANCE.md` defines contextual help, first-run onboarding, operation-specific safe errors, tooltips, confirmation semantics, state-aware recovery actions, accessibility, localization readiness, and secret-safe messaging. `docs/mockups/help-recovery.html` demonstrates the workflow with synthetic identifiers and no external requests. `tests/test_help_and_recovery.py` passed 4 focused tests; Python compilation passed. Live assistive-technology review and integration into the production GUI remain downstream validation work.


## Consistent workflow-state checkpoint — 2026-08-27

The selected state-handling item is complete as a bounded desktop implementation. `windows_gui.py` now defines one shared state vocabulary and classifier for loading, empty, offline, blocked, failed, partial, long-running, and ready outcomes. The execution monitor and verification view use the same copy formatter, show loading and empty states before requests, distinguish approval waits and active work, and provide bounded next-step guidance without exposing raw exceptions, credentials, payloads, or provider responses. `docs/WORKFLOW_STATE_HANDLING.md` defines the taxonomy and recovery rules; `tests/test_workflow_state_handling.py` provides focused coverage.

Validation passed: 3 focused workflow-state unittest cases and Python compilation for `windows_gui.py` and the test module. No credentials, external services, or destructive actions were used. Live outage drills and cross-client visual review remain environment-dependent follow-up gates.


## GUI architecture boundary checkpoint — 2026-08-27

The selected architecture item is complete as a documented local contract. `docs/GUI_ARCHITECTURE_BOUNDARIES.md` selects a layered native-client architecture with presentation, client adapter, API boundary, orchestration, model services, storage, and external-integration layers. It records ownership, prohibited coupling, authenticated request/event flow, standalone operation, future-client reuse, credential handling, approval gates, failure projection, and lifecycle responsibilities. `tests/test_gui_architecture_boundaries.py` provides focused coverage.

Validation passed: 3 focused GUI architecture documentation unittest cases and Python compilation for the test module. No credentials, external services, or destructive actions were used. Runtime dependency enforcement, multi-client contract testing, and production integration review remain follow-up gates.


## Worker Task 2 checkpoint — GUI quality and major-journey test coverage — 2026-08-27

Added `docs/GUI_TEST_STRATEGY.md` and `tests/test_gui_quality.py`. The aggregate suite covers shared component contracts, task/model/generation/artifact/settings/help workflows, accessibility and secret-safety markers, responsive behavior, and the ordered objective-intake → plan-review → execution → verification → delivery journey. Five focused tests and Python compilation passed. Live browser automation, visual regression, screen-reader review, performance measurement, and backend-integrated end-to-end execution remain downstream release gates.


## Visual regression checkpoint — 2026-08-27

The selected visual-regression item is complete as a deterministic local check. `tools/visual_regression.py` fingerprints reviewed design tokens and stable semantic structure from the canonical control-center mockup, while `artifacts/visual_regression_baseline.json` stores the reviewed baseline. `docs/VISUAL_REGRESSION.md` defines covered assets, commands, baseline review policy, and limitations; `tests/test_visual_regression.py` covers baseline matching, critical-screen evidence, and fail-closed drift detection.

Validation passed: 3 focused visual-regression unittest cases, the baseline check, and Python compilation for the checker and test module. No credentials, external services, or destructive actions were used. Pixel-perfect screenshot comparison across OS/browser/native rendering, assistive-technology review, and web/mobile baselines remain environment-dependent follow-up gates.

**Phase 6 GUI performance checkpoint — 2026-08-27:** `tools/measure_gui_performance.py` now provides a deterministic, credential-free benchmark for fresh `windows_gui` import startup, representative interaction latency, peak traced Python memory, and a fixed 1,000-task/500-artifact workload. `docs/GUI_PERFORMANCE_MEASUREMENT.md` defines the local release gates and limitations; `docs/GUI_PERFORMANCE_BASELINE.json` records the Windows-target baseline of 328.055 ms startup, 2.185 ms average interaction handling, and 100,235 peak traced bytes. Four focused tests and Python compilation passed. Window painting, disk/network latency, and production hardware variance remain deployment/platform-owned.

**Last updated:** 2026-08-27



## Worker concurrency reconfiguration — 2026-08-27

The standalone Manus roadmap worker now permits up to 10 concurrent existing task threads. `tools/orville_manus_worker.py` accepts `--max-active` values from 1 through 10, defaults to 10, and defines explicit `Worker Task 1` through `Worker Task 10` slots. Worker documentation and focused tests were updated. Validation passed: 9 worker tests, Python compilation, CLI help inspection, and credential-free `--dry-run --max-active 10`. No network call or credential value was used.


## Worker Task 2 checkpoint — Standalone GUI operations documentation — 2026-08-27

Added `docs/GUI_STANDALONE_OPERATIONS.md` covering source execution, local API startup, build and release gates, PyInstaller packaging, portable and installed modes, safe updates, independent Compose deployment, rollback, recovery, data preservation, and Manus-independent security boundaries. Added `tests/test_gui_standalone_operations.py`; three focused tests and Python compilation passed. Code signing, live provider/browser checks, production deployment, and infrastructure-owned rollback evidence remain downstream responsibilities.


## GUI sensitive-data exposure checkpoint — 2026-08-27

The selected interface exposure item is complete as a bounded native-GUI hardening implementation. `windows_gui.py` now applies a recursive safe display projection to provider/model/API output, redacts credential-like values and local paths, suppresses raw manager exceptions, hides runtime endpoint/authentication values in the details panel, and stops echoing the submitted objective into output/context widgets. `docs/GUI_SENSITIVE_DATA.md` defines the display policy and limitations; `tests/test_gui_sensitive_data.py` provides focused synthetic-data coverage.

Validation passed: 3 focused sensitive-data unittest cases and Python compilation for `windows_gui.py` and the test module. No live credentials, external services, or destructive actions were used. Live traffic inspection, secret-store review, crash/clipboard telemetry review, and web/mobile exposure review remain separate release gates.


## Worker Task 2 checkpoint — Workload classification — 2026-08-27

Implemented deterministic classification for `one_shot`, `recurring`, `event_triggered`, `webhook_driven`, and `persistent_service` workloads in `orville_core.agent_contracts`. Added `WorkloadClassification`, `classify_workload`, AutomationSpec support, public package exports, `docs/WORKLOAD_CLASSIFICATION.md`, and focused tests. Five focused tests and Python compilation passed. The classifier performs no network calls, scheduling, task creation, or external side effects. Runtime trigger adapters and service supervisors remain responsible for execution controls.


## Schedule ownership and lifecycle checkpoint — 2026-08-27

The selected schedule contract item is complete as a documented local contract. `docs/SCHEDULE_OWNERSHIP_LIFECYCLE.md` defines schedule ownership, IANA timezone handling with UTC normalization and DST behavior, expiration, pause/resume, missed-run policy, failure notification ordering, bounded notification retries, deduplication, and safe notification payloads. It explicitly distinguishes the contract from runtime schema migration and live provider delivery. `tests/test_schedule_ownership_lifecycle.py` provides focused coverage.

Validation passed: 3 focused schedule-contract unittest cases and Python compilation for the test module. No credentials, external services, or destructive actions were used. Runtime schema migration, live scheduler execution, notification-provider delivery, and production timezone/DST drills remain follow-up gates.


## Worker Task 2 checkpoint — Scheduled workflow idempotency — 2026-08-27

Implemented deterministic scheduled-occurrence keys and retry-safe execution handling. `ScheduleStore.claim` now leases without advancing `next_run_at`; `advance_after_success` advances timing only after successful completion. Execution records are reused by deterministic occurrence ID, completed runs are not re-executed, and failed occurrences remain retryable with the same workflow idempotency key. Added `docs/SCHEDULED_WORKFLOW_IDEMPOTENCY.md` and `tests/test_scheduled_idempotency.py`. Six focused scheduler/automation tests and Python compilation passed. Provider-side idempotency, compensation, missed-interval catch-up, and configurable backoff remain downstream responsibilities.


## Long-running job state checkpoint — 2026-08-27

The selected long-running state-storage item is complete as a documented local contract. `docs/LONG_RUNNING_JOB_STATE.md` defines durable workflow/task/event/lease/artifact/recovery records, atomic state transitions, checkpoint sequencing, stale-lease protection, restart reconciliation, deterministic recovery, retention, and fail-closed handling for unproven external side effects. `tests/test_long_running_job_state.py` provides focused coverage.

Validation passed: 3 focused long-running state unittest cases and Python compilation for the test module. No credentials, external services, or destructive actions were used. Runtime supervisor implementation, crash injection, multi-process lease testing, and production storage durability remain follow-up gates.

**Worker concurrency configuration checkpoint — 2026-08-27:** The Windows scheduled-task installer now consistently registers `orville_manus_worker.py` with `--max-active 10`, and its description and dry-run guidance state the ten-thread limit. The worker implementation already enforces the safe range of 1–10 and caps persisted active-task state at ten. Existing scheduled-task metadata was observed using `--max-active 10`; no credentials or task records were changed.



## Worker Task 2 checkpoint — Execution target selection — 2026-08-27

Added `docs/EXECUTION_TARGET_SELECTION.md` and `tests/test_execution_target_selection.py`. The contract defines when to use sandbox execution, managed web hosting, attached Windows desktop execution, or persistent computing based on lifecycle, interface, operating-system, network, resource, and data-residency requirements. It also defines secret, approval, resource, recovery, rollback, and escalation boundaries. Three focused tests and Python compilation passed. Live deployment capacity, provider verification, infrastructure approval, and environment-specific release checks remain downstream work.


## Health monitoring, structured logging, and runbook checkpoint — 2026-08-27

The selected operational observability item is complete as a documented local contract. `docs/HEALTH_MONITORING_LOGGING_RUNBOOKS.md` defines component health states, safe signal thresholds, bounded JSON event fields, correlation and redaction rules, retention/access boundaries, service/dependency, failure, saturation, security, and release runbooks, and ownership/escalation. Existing production metrics, usage health, readiness, and secret-safe audit modules are identified as local reference sources.

Validation passed: 3 focused health/logging/runbook unittest cases and Python compilation for the test module. No credentials, external services, or destructive actions were used. Live alert delivery, hosted dashboards, production-calibrated thresholds, retention enforcement, and operator tabletop exercises remain deployment-owned gates.


## Worker Task 2 checkpoint — Workflow dry-run mode — 2026-08-27

Implemented `WorkflowExecutor.execute(..., dry_run=True)` for workflows that may mutate external state. Steps marked `mutates_external_state=True` are skipped and returned as stable `dry_run_actions`; safe local steps may execute; `_dry_run=True` is returned; and live approval enforcement remains unchanged. Added `docs/WORKFLOW_DRY_RUN.md` and `tests/test_workflow_dry_run.py`. Three focused tests and Python compilation passed. The preview does not prove provider availability, permissions, quotas, payload acceptance, or deployment success.


## Approval checkpoint checkpoint — 2026-08-27

The selected approval-checkpoint item is complete as a local implementation and contract. `orville_core/automation.py` now persists deterministic, idempotent `ApprovalCheckpoint` records with bounded action/target summaries, pending and terminal resolution states, approver references, and first-decision preservation. `docs/APPROVAL_CHECKPOINTS.md` defines irreversible/high-impact action coverage, fail-closed lifecycle rules, exact target/scope confirmation, single-use approval, dry-run separation, recovery, and safe evidence. `tests/test_approval_checkpoints.py` provides focused coverage.

Validation passed: 3 focused approval-checkpoint unittest cases and Python compilation for the automation and test modules. No credentials, external services, or destructive actions were used. Live identity-provider authorization, external connector execution, and production destructive-action exercises remain deployment-owned gates.


## Worker Task 2 checkpoint — Secret-handling rules — 2026-08-27

Added `docs/SECRET_HANDLING_RULES.md` and `tests/test_secret_handling_rules.py`. The contract defines protected environment and configuration handling, server-side consumption, redaction before logs and retained evidence, artifact and screenshot review, non-secret references, rotation/revocation, and recovery boundaries. Three focused tests and Python compilation passed. Provider secret-manager configuration, live deployment permissions, and operational incident response remain environment-owned controls.

**Worker task-record assignment checkpoint — 2026-08-27:** At the user's request, seven new private Manus task records were created for free worker slots 3–9 and persisted in `.orville_manus_worker_state.json`. They were assigned distinct unchecked TODO lines 727, 729, 731, 733, 735, 737, and 741. The state now contains nine unique task records across Worker Task 1–9; Worker Task 10 remains available. A credential-free dry run validated nine unique IDs, nine unique worker slots, and `max_active_tasks=10`. No credential value was written to the repository.



## External-boundary validation checkpoint — 2026-08-27

The selected boundary-validation item is complete as a local implementation and contract. `orville_core/boundary.py` provides bounded text and identifier validation, HTTP(S) URL validation with explicit local-host permission, and recursive bounded output sanitization for sensitive keys, credential-like text, bearer tokens, and local paths. `docs/EXTERNAL_BOUNDARY_VALIDATION.md` defines boundary ownership, input categories, output projection, error/logging behavior, and limits. Existing provider/cloud-relay boundary tests remain intact; `tests/test_external_boundaries.py` adds focused primitive coverage.

Validation passed: 6 focused external-boundary pytest cases and Python compilation for the boundary module and test module. No credentials, external services, or destructive actions were used. Live provider fuzzing, browser payload review, file-parser hardening, and production traffic inspection remain separate release gates.


## Worker Task 2 checkpoint — Core unit-test coverage — 2026-08-27

Added `tests/test_core_unit_contracts.py` with focused unit coverage for task parsing round-trips, graph validation failures, routing endpoint and request validation, persisted engine state transitions, and artifact registration metadata. Five tests and Python compilation passed using temporary local state and synthetic inputs. Existing broader orchestration, routing, workflow, and artifact suites remain separate regression coverage; no external services or credentials were used.


## Worker Task 2 checkpoint — Regression fixtures — 2026-08-27

Added retained JSON fixtures under `tests/fixtures/regressions/` with a manifest linking three previously fixed local failure modes: scheduled retry identity, workflow dry-run mutation suppression, and nested secret redaction. Added `tests/test_regression_fixtures.py` to load and exercise the fixtures. Four focused tests and Python compilation passed using temporary local state and synthetic values. External-provider, browser, connector, and deployment regressions remain separate integration scope.


## Boundary integration-test checkpoint — 2026-08-27

The selected integration-test item is complete as a discoverable local-fixture suite. `tests/test_boundary_integrations.py` covers filesystem context isolation and model import/checksum integrity, GitHub connector invocation through a patched local bridge with approval gating, browser persistence/recovery, scheduled workflow dispatch and lease release, provider failure redaction, and webhook signature validation. No live GitHub, browser, provider, connector, or external scheduler credentials are used.

Validation passed: 6 focused pytest cases and Python compilation for the integration module. One pre-existing FastAPI/Starlette TestClient deprecation warning was emitted. Existing broader boundary suites remain complementary; live service interoperability and platform-specific execution remain deployment-owned gates.


## Worker Task 2 checkpoint — Deterministic test data and mock services — 2026-08-27

Added deterministic external-boundary cases in `tests/fixtures/deterministic_external_cases.json`, a loopback-only mock HTTP service in `tests/fixtures/mock_external_service.py`, and `tests/test_deterministic_mocks.py`. The mock provides stable health, echo, and unavailable responses and is exercised through `JsonHttpClient` without credentials or internet access. Three focused tests and Python compilation passed. Provider-specific, browser, connector, and deployment integration remain separate scope.


## Performance-test checkpoint — 2026-08-27

The selected performance-test item is complete as a bounded local suite. `tests/test_performance_boundaries.py` measures graph execution at 100 tasks, parallel fan-out with four workers and twelve independent tasks, transient retry completion with a three-attempt cap, and registration/listing of 100 local artifacts. Thresholds are intentionally generous for repeatable CI-style checks and the tests use temporary local fixtures only.

Validation passed: 4 focused performance pytest cases and Python compilation for the performance module in 4.23 seconds. No credentials, external services, or destructive actions were used. These are smoke-level performance gates, not production capacity targets; load calibration and environment-specific benchmarking remain follow-up work.


## Worker Task 2 checkpoint — Security attack-surface tests — 2026-08-27

Added `tests/test_security_attack_surfaces.py` with five focused tests covering nested secret leakage, prompt injection treated as bounded untrusted data, path traversal and unauthorized writes, unsafe shell syntax and credential-like sandbox environments, and unauthorized tool actions. Five tests and Python compilation passed using synthetic values and temporary local paths. Live browser, connector, provider, deployment, and production telemetry security validation remain separate scope.


## Worker Task 2 checkpoint — Failed-test triage gate — 2026-08-27

Added `tools/test_triage.py`, `config/test_triage_manifest.json`, `docs/TEST_FAILURE_TRIAGE.md`, and `tests/test_test_triage.py`. Updated `tools/project_checks.py` so the regression check requires the triage manifest after tests and before release acceptance. The validator rejects missing fields, duplicate test IDs, unsupported or untriaged statuses, malformed schema, and missing manifests. Three focused tests, validator CLI execution, and Python compilation passed. Automatic failure discovery and live release-system integration remain downstream work.


## Worker Task 2 checkpoint — Deployment commands by target — 2026-08-27

Added `deploy.ps1` and `docs/DEPLOYMENT_TARGET_COMMANDS.md` for sandbox, web hosting, attached desktop, and persistent computing. The dispatcher is dry-run by default, supports explicit `-Execute`, checks required local files, and reuses existing project-check, Compose, release-builder, and installer boundaries. Added `tests/test_deployment_commands.py`; three focused tests, PowerShell syntax validation, and Python compilation passed. Live host capacity, Docker availability, code signing, infrastructure approval, and post-deployment smoke tests remain downstream gates.


## Worker Task 1 checkpoint — Deployment targets and environment variables — 2026-08-27

The selected deployment-definition item is complete locally. `docs/DEPLOYMENT_TARGETS_AND_ENVIRONMENT.md` defines the supported local Python, installed Windows, portable Windows, Docker Compose small-team, and disposable-container targets; the runtime variable matrix; optional integration variables; secret boundaries; and explicit exclusions for unclaimed managed-cloud, Kubernetes, serverless, and public multi-replica targets. `.env.example` now includes safe defaults for `ORVILLE_PORTABLE` and `ORVILLE_REQUESTS_PER_MINUTE`. Focused contract tests passed (3) and Python compilation passed. No credentials, network calls, infrastructure changes, or destructive actions were used. Live production promotion remains deployment-owned.

**Worker orphan cleanup checkpoint — 2026-08-27:** Removed only the seven invalid Worker Task 3–9 records after repeated remote `task.detail` HTTP 404 responses. Preserved the two valid Worker Task 1–2 records and created a non-secret state backup under `artifacts/`. Re-registered the Windows Scheduled Task and updated `tools/install_orville_manus_worker.ps1` to use `--max-active 3` temporarily while the API task-routing issue remains unresolved. Validation confirmed two persisted records, zero orphan slots, and scheduled arguments using `--max-active 3`.



## Worker Task 1 checkpoint — Versioning and release notes — 2026-08-27

The selected versioning item is complete locally. `docs/VERSIONING_AND_RELEASE_NOTES.md` defines Semantic Versioning 2.0.0, the `pyproject.toml` version source of truth, release immutability, candidate handling, release-note structure, validation evidence, upgrade, and rollback rules. `RELEASE_NOTES.md` records the 0.1.0 standalone baseline, user-facing changes, security boundaries, validation scope, upgrade guidance, and known limitations. Focused tests passed (3) and Python compilation passed. No credentials, external services, or destructive actions were used.


## Worker Task 2 checkpoint — Pre-deployment and post-deployment smoke checks — 2026-08-27

Added `tools/deployment_validation.py` with target preflight checks and bounded credential-free HTTP smoke checks. Updated `deploy.ps1` to run preflight before target operations and local `/docs` smoke checks after web-hosting and persistent-computing execution. Added `tests/test_deployment_validation.py`; seven focused deployment tests, PowerShell syntax validation, and Python compilation passed. Live deployment, production host availability, code signing, provider authentication, and infrastructure-owned smoke checks remain downstream gates.


## Worker Task 1 checkpoint — Least-privilege permissions — 2026-08-27

The selected permission-minimization item is complete locally. `orville_core.security.LeastPrivilegePolicy` now provides task-scoped, default-deny checks for connector IDs and scopes, repository IDs with separate write permission, filesystem roots through `FilesystemPolicy`, and normalized remote hosts plus actions. `docs/LEAST_PRIVILEGE_PERMISSIONS.md` documents the boundary matrix and separation from explicit high-impact approval gates. Focused tests passed (4) and Python compilation passed. No credentials, external systems, network calls, or destructive actions were used. Live connector, repository, remote, and deployment enforcement remains target-specific.


## Phase 6 sensitive-operation confirmation checkpoint — 2026-08-27

The selected confirmation-gate item is complete locally. Added `orville_core/confirmations.py` with an allowlisted sensitive-operation catalog covering payments, purchases, publishing, deletion, account and permission changes, credential entry, external sends, connector mutations, and destructive file actions. `ConfirmationRequest` records the exact operation, target, scope, requester, bounded expiry, and stable fingerprint without secret payloads; `ConfirmationGate` fails closed on missing, expired, mismatched, invalid, or reused receipts and consumes a receipt once. Updated `docs/DESTRUCTIVE_ACTION_CONFIRMATIONS.md` and added `tests/test_confirmations.py`. Seven focused tests and Python compilation passed; no credentials, external services, or destructive actions were used. UI wiring and provider-specific authorization remain caller/deployment responsibilities.


## Worker Task 1 checkpoint — Sensitive-domain safe handling — 2026-08-27

The selected safe-handling item is complete locally. `orville_core.workflow` now classifies medical, legal, tax, financial, insurance, real-estate, gambling, and major-life-decision objectives, attaches informational-only and professional-review metadata, identifies consequential actions, and adds explicit approval/review gates without providing domain advice. Focused tests passed (4) and Python compilation passed for the modified modules. No credentials, external services, or user-specific advice were used. Professional review, emergency handling, jurisdiction-specific requirements, and live policy evaluation remain outside this deterministic intake contract.


## Phase 6 untrusted-content execution-boundary checkpoint — 2026-08-27

The selected untrusted-content item is complete locally. Added `orville_core/untrusted_content.py` with deterministic bounded instruction-like content detection and a fail-closed `authorize_tool_execution` boundary. External pages, tool results, model outputs, and downloaded artifacts can be assessed as data but cannot authorize tool execution; trusted origins still require separate explicit endorsement. Added `tests/test_untrusted_content.py` covering detection, origin blocking, endorsement requirements, bounds, and non-text rejection. Five untrusted-content tests plus existing external-boundary tests passed, Python compilation passed, and a precise secret-pattern scan passed. Runtime integration at every provider-specific tool adapter remains follow-up work.


## Worker Task 1 checkpoint — Dependency and supply-chain review — 2026-08-27

The selected supply-chain review item is complete locally. `orville_core.supply_chain` now provides non-executing review primitives for downloaded packages, scripts, and artifacts: approved-root containment, SHA-256 verification, provenance requirements, script independent-review gating, and value-only review results. `docs/SUPPLY_CHAIN_REVIEW.md` defines dependency, download, script, artifact, evidence, and retention procedures. Focused tests passed (4) and Python compilation passed for the modified modules. No packages were installed, scripts executed, artifacts downloaded, credentials used, or external calls made. Live vulnerability databases, package indexes, remote repositories, model hubs, and deployment scanners remain environment-specific follow-up checks.


## Phase 6 incident-response and recovery checkpoint — 2026-08-27

The selected incident-response item is complete locally. Added `docs/INCIDENT_RESPONSE_CREDENTIAL_ROTATION_RECOVERY.md`, defining severity classification, incident intake, safe evidence preservation, fail-closed containment, credential rotation and revocation, backup/checkpoint recovery, staged restoration, recovery failure handling, closure, and post-incident review. The runbook requires explicit confirmation for sensitive actions, prohibits credentials in evidence, and preserves standalone operation. Added `tests/test_incident_response_procedures.py`; four focused documentation tests, Python compilation, and a precise secret-pattern scan passed. Live provider rotation, infrastructure recovery, and production incident exercises remain deployment-owned.


## Phase 9 orchestration test-matrix checkpoint — 2026-08-27

The selected test-matrix item is complete locally. Added `docs/ORCHESTRATION_TEST_MATRIX.md`, mapping orchestration, delegation, graph dependencies, retries, failures, approvals, integration, and safety-integration capabilities to executable test modules, owners, acceptance gates, deterministic execution profiles, and external limitations. Added `tests/test_orchestration_test_matrix.py` to verify required capability rows, referenced test-module existence, deterministic/safety gates, and the absence of live-validation claims. Four focused tests, Python compilation, and a precise secret-pattern scan passed. Full regression execution and live provider/infrastructure integration remain governed by the release gate.


## Worker Task 1 checkpoint — Rollback and recovery verification — 2026-08-27

The selected rollback item is complete locally. `orville_core.recovery` now provides approval-requiring rollback-plan construction and non-destructive recovery-evidence verification for backup existence, SHA-256 integrity, authenticated health, read-only state, and smoke workflow checks. `docs/ROLLBACK_AND_RECOVERY_VERIFICATION.md` documents evidence preservation, credential response, storage safety, failed-recovery escalation, and closure requirements. Focused tests passed (4) and Python compilation passed. No deployment commands, restores, external services, credentials, or destructive actions were used. Live rollback, database restoration, and target-specific recovery drills remain deployment-owned.


## Phase 9 structured logging checkpoint — 2026-08-27

The selected structured-logging item is complete locally. Added `orville_core/structured_logging.py` with JSON-lines event emission, execution-scoped correlation IDs, execution/task/agent identifiers, bounded fields, UTC timestamps, severity, and reuse of the existing secret-safe sanitizer. Added `tests/test_structured_logging.py` covering nested correlation propagation, JSON shape, redaction, bounded messages, JSONL persistence, and resource-safe file handling. Four focused logging tests plus existing credential-redaction tests passed with `ResourceWarning` promoted to errors; Python compilation passed. Adapter-specific logger wiring and centralized log transport remain follow-up integration work.


## Worker Task 1 checkpoint — Execution metrics — 2026-08-27

The selected metrics item is complete locally. `orville_core.telemetry.MetricSeries` and `TelemetryRegistry.record` now capture task duration means, success and failure rates, total retry counts, bounded failure classes, and verification outcomes while preserving existing callers. Focused tests passed (3) and Python compilation passed. Metrics retain aggregate values only and no payloads, prompts, credentials, or raw errors. Adapter-specific wiring and production dashboard export remain environment-specific follow-up work.


## Phase 9 operational dashboards and reports checkpoint — 2026-08-27

The selected operational-dashboard item is complete locally. Added `tools/operational_report.py` to aggregate bounded JSONL execution logs into a report containing target, event and execution counts, failure count, success rate, duration statistics, status counts, and data-quality flags. Added `docs/OPERATIONAL_DASHBOARDS_AND_REPORTS.md` defining local, attached-desktop, sandbox, web-hosting, and persistent-computing support, review semantics, retention boundaries, and deployment-owned alerting limitations. Added `tests/test_operational_report.py`; four focused tests, Python compilation, and a precise secret-pattern scan passed. Hosted log collection, live dashboards, alert delivery, and infrastructure SLO collection remain deployment-owned.


## Worker Task 1 checkpoint — Maintenance ownership and upgrade cadence — 2026-08-27

The selected maintenance item is complete locally. `docs/MAINTENANCE_OWNERSHIP_AND_UPGRADE_CADENCE.md` assigns ownership and review boundaries for core, integrations, security, GUI, release/deployment, documentation, and incident recovery; defines change, weekly, monthly, quarterly, pre-release, and post-release activities; and documents upgrade triggers, evidence, escalation, and ambiguity handling. Focused documentation tests passed (3) and Python compilation passed. No credentials, external services, schedules, or infrastructure changes were used. Live ownership assignment, alerting, dependency scanners, and recovery exercises remain environment-specific.

**Task replication-delay polling checkpoint — 2026-08-27:** Added `tools/poll_task_replication.py`, a standalone bounded read-only poller for newly created Manus task IDs. It retries HTTP 404 and transient HTTP responses, reports visibility or timeout, stops on terminal errors, validates task IDs, and reads credentials only from the named process environment. Added `tests/test_poll_task_replication.py`; four focused tests, Python compilation, and invalid-ID CLI validation passed.



## Phase 9 standalone README checkpoint — 2026-08-27

The selected standalone README item is complete locally. Rewrote `README.md` with prerequisites, isolated installation, configuration variables and secret boundaries, local usage, examples, project checks, deployment commands, testing, troubleshooting, security boundaries, and standalone limitations. Added `tests/test_standalone_readme.py` to verify required sections, runnable commands, referenced local files, security guidance, and absence of credential-shaped literals. Four focused README tests, Python compilation, and a precise secret-pattern scan passed. Provider authorization, live deployment, and external-service availability remain explicitly outside the README's local claims.


## Worker Task 1 checkpoint — Architecture document — 2026-08-27

The selected architecture-document item is complete locally. `docs/ARCHITECTURE.md` documents the standalone component model, agent roles and handoffs, DAG and checkpoint state flow, tools and external boundaries, artifact and verification lifecycles, recovery, observability, and security controls. Focused architecture-contract tests passed (3) and Python compilation passed. No credentials, external services, or destructive actions were used. The document describes implemented contracts and explicitly leaves live provider, browser, connector, infrastructure, and production validation environment-specific.


## Phase 9 operator runbook checkpoint — 2026-08-27

The selected operator-runbook item is complete locally. Added `docs/OPERATOR_RUNBOOK.md`, covering target and repository-root confirmation, readiness/configuration/health checks, local smoke validation, structured operational-report review, failure triage, connector diagnosis and fallback, credential exposure handling, checkpoint and backup recovery, staged restoration, escalation, and closure evidence. Added `tests/test_operator_runbook.py`; four focused runbook tests, Python compilation, and a precise secret-pattern scan passed. Live provider, connector, infrastructure, and production recovery actions remain deployment-owned.


## Phase 9 task-template catalog checkpoint — 2026-08-27

The selected task-template item is complete locally. Added `config/task-templates.json` with versioned templates for research, coding, automation, web development, media, documents, and deployments. Each template defines an objective, deliverables, constraints, acceptance criteria, and verification method. Added `docs/TASK_TEMPLATES.md` with refinement, safety, maintenance, and usage guidance and `tests/test_task_templates.py` covering all requested types, common fields, safety contracts, JSON integrity, and versioning. Four focused tests, Python compilation, JSON parsing, seven-template count validation, and a precise secret-pattern scan passed. Templates are starting contracts; live provider, deployment, and external-side-effect behavior remains separately authorized and environment-owned.


## Worker Task 1 checkpoint — Contributor guide — 2026-08-27

The selected contributor-guide item is complete locally. `docs/CONTRIBUTING.md` documents standalone prerequisites and setup, repository layout, development workflow, focused and full validation, review requirements, security and untrusted-content rules, release and deployment procedures, handoffs, completion criteria, and troubleshooting. Focused documentation tests passed (3) and Python compilation passed. No credentials, external services, or destructive actions were used. Live ownership, hosted infrastructure, provider authorization, and production release actions remain environment-specific.


## Phase 9 standalone examples checkpoint — 2026-08-27

The selected standalone-examples item is complete locally. Added `examples/README.md` documenting no-Manus execution expectations, retained `examples/basic_run.py` as a deterministic checkpointed graph example, and added `examples/local_operational_report.py` for local JSON report generation using temporary data. Added `tests/test_standalone_examples.py`; three focused tests executed the basic workflow and report example and checked source safety. Python compilation and a precise credential-pattern scan passed. Examples do not require Manus, MCP, browser sessions, provider credentials, or external services; provider and deployment behavior remains separately documented.


## Worker Task 1 checkpoint — Graceful degradation — 2026-08-27

The selected graceful-degradation item is complete locally. `docs/GRACEFUL_DEGRADATION.md` defines stable connector, website, provider, partial-dependency, and offline states; preserves objectives, graphs, checkpoints, artifacts, and evidence; constrains retries and fallbacks; labels partial results; and defines recovery and escalation boundaries. Focused documentation tests passed (3) and Python compilation passed. No credentials, external services, browser sessions, or destructive actions were used. Live connector recovery, website availability, authentication, failover, alerting, and production network behavior remain environment-specific.


## Phase 9 glossary checkpoint — 2026-08-27

The selected glossary item is complete locally. Added `docs/GLOSSARY.md` as the canonical terminology reference for task graph, agent role, artifact, verification gate, connector, and execution state, plus related execution, correlation, task-node, dependency, handoff, approval, checkpoint, retry, dry-run, provider, and runbook terms. Added `tests/test_glossary.py` covering required definitions, concept boundaries, safety rules, referenced maintenance command, and secret-safe wording. Four focused glossary tests, Python compilation, and a precise secret-pattern scan passed. New contracts and state-name changes must update the glossary in the same change.


## Worker Task 1 checkpoint — Repeated failure pattern review — 2026-08-27

The selected continuous-improvement item is complete locally. Added `orville_core/failure_patterns.py` with a bounded, non-executing analyzer for terminal task-graph run records. It aggregates recognized failure events by sanitized failure class, counts distinct runs and tasks, filters nonterminal and nonfailure records, enforces a minimum repetition threshold, and returns no raw errors, prompts, outputs, URLs, credentials, or event payloads. Added `docs/REPEATED_FAILURE_REVIEW.md` and focused tests. Three tests, package-export compilation, and Python compilation passed. The analyzer does not infer causality or automatically change policy, retries, permissions, routing, or production systems.


## Phase 9 reusable fixes checkpoint — 2026-08-27

The selected reusable-fixes item is complete locally. Added `config/reusable-fixes.json` with five named recurring-fix categories mapping release validation, sensitive-operation safety, operator recovery, standalone delivery, and terminology/observability to stable templates, tests, documentation, and automation entry points. Added `docs/REUSABLE_FIXES.md` defining the reuse workflow, maintenance rules, and safety boundaries, plus `tests/test_reusable_fixes.py`. Four focused tests, Python compilation, JSON validation, referenced-asset checks, and a precise secret-pattern scan passed. Catalog entries are guidance rather than authorization; sensitive operations and live environments remain separately gated.


## Worker Task 1 checkpoint — Lifecycle phase-duration metrics — 2026-08-27

The selected phase-duration item is complete locally. Extended `TelemetryRegistry` with bounded `record_phase_duration` measurements for planning, execution, verification, and recovery, including normalized phase names and rejection of unknown, negative, or non-finite durations. Phase aggregates are exposed in the existing snapshot/export structure alongside task metrics. Focused tests passed (3) and Python compilation passed. No payloads, prompts, credentials, or raw errors are retained. Automatic instrumentation at every production lifecycle boundary and hosted time-series collection remain environment-specific follow-up work.


## Worker Task 1 checkpoint — Agent-assignment performance review — 2026-08-27

The selected assignment-review item is complete locally. Added `orville_core/assignment_review.py` with a bounded aggregate report over terminal task-graph run records. It compares assignment labels with task counts, completions, failures, verification failures, attempt means, and duration means, while excluding nonterminal runs and omitting titles, prompts, outputs, paths, raw errors, credentials, and personal data. Added `docs/AGENT_ASSIGNMENT_REVIEW.md` and focused tests. Three tests, Python compilation, and public-export validation passed. The report does not rank individuals, infer causality, assign blame, or automatically reassign agents; live production performance and cross-installation analysis remain environment-specific.


## Cleanup task blocked — 2026-08-27

The next eligible cleanup item was reviewed but not claimed for implementation. Repository inspection found disposable candidates such as 	mp, __pycache__, and .pytest_cache, but AGENTS.md requires explicit confirmation before destructive file or repository actions and requires named-path retention checks. No dependency, connector, instruction, artifact, cache, or user data was deleted. The item is marked blocked in TODO.md pending explicit approval and a scoped deletion list.


**Worker startup creation-readability checkpoint — 2026-08-27:** Added an opt-in CLI gate for concurrency above three. With `--validate-create-readability`, the worker creates one harmless private diagnostic task, retries `task.detail` on HTTP 404 and transient transport failures for bounded attempts, and fails closed before polling existing state if the task remains unreadable. Added `tests/test_worker_creation_validation.py`; 14 focused worker/gate tests and Python compilation passed. The Scheduled Task remains at `--max-active 3` until the upstream create/read visibility issue is resolved.



## Phase 9 readiness report checkpoint — 2026-08-27

The selected readiness-report item is complete locally. Added `docs/READINESS_REPORT.md` reflecting the current architecture and operations surface: orchestration, checkpoints, approvals, untrusted-content blocking, structured logging, operational reports, deployment preflight/smoke checks, standalone examples, task templates, operator runbook, glossary, and reusable-fixes catalog. The report distinguishes local implementation readiness from conditional target readiness and production readiness, records the full-suite collection blocker caused by `task_status` being used before definition in `tools/orville_manus_worker.py`, and records the cleanup-item approval blocker. Added `tests/test_readiness_report.py`; four focused tests, Python compilation, and a precise secret-pattern scan passed.


## Worker Task 1 checkpoint — Prioritized backlog — 2026-08-27

The selected backlog item is complete locally. Added `config/priority-backlog.json` with traceable existing-TODO records and explicit status, priority, impact, effort, risk, dependencies, acceptance evidence, and blocker fields. Added `docs/PRIORITIZED_BACKLOG.md` defining the score signal, dependency/blocker overrides, lifecycle, review cadence, and security boundaries. Added focused tests. Three tests, JSON parsing, and Python compilation passed. The first validation found one catalog wording mismatch with `TODO.md`; the record was corrected to the exact existing integration-contract wording and the final validation passed. The catalog does not create new work or authorize destructive actions.


## Phase 9 milestone roadmap review checkpoint — 2026-08-27

The selected roadmap-review item is complete locally through an equivalent milestone review. Added `docs/MILESTONE_ROADMAP_REVIEW_2026-08-27.md`, covering completed-local areas, conditional target readiness, priorities, dependencies, risks, known blockers, acceptance gates, and review-maintenance cadence. The review records the full-suite collection blocker caused by `task_status` being used before definition in `tools/orville_manus_worker.py` and the approval blocker on cleanup. Added `tests/test_milestone_roadmap_review.py`; four focused tests, Python compilation, and a precise secret-pattern scan passed. No live provider, production, account, deployment, or destructive action was performed.


## Worker Task 1 checkpoint — GUI-to-engine API contract — 2026-08-27

The selected GUI-to-engine contract item is complete locally. Added `docs/GUI_ENGINE_API_CONTRACT.md`, defining versioned request/response envelopes, ownership and projections for objectives, task graphs, runs, checkpoints, providers, local models, verification records, artifacts, approvals, and event streams; engine-controlled state transitions; authentication and authorization boundaries; approval separation; redaction; idempotency; unavailable-dependency handling; and additive compatibility rules. Added focused contract tests. Three tests and Python compilation passed. The document does not claim that a deployed backend bridge or GUI wiring is complete; those remain separate implementation items.


## Phase 9 authenticated GUI backend bridge checkpoint — 2026-08-27

The selected GUI-backend-bridge item is complete locally. The existing `orville_core/api.py` bridge provides exact bearer-token authentication, route authorization dependencies, Pydantic request validation, bounded safe error responses, explicit CORS allowlisting with credentials disabled, authenticated one-minute rate limiting, and `AuditStore` redaction before persistence. Added `docs/GUI_BACKEND_BRIDGE.md` as the canonical integration contract and `tests/test_gui_backend_bridge.py` with four focused tests covering the required controls and synthetic audit redaction. API/audit Python compilation and a precise documentation secret scan passed. Production TLS, identity lifecycle, secret storage/rotation, centralized retention, and infrastructure controls remain deployment-owned.

**Autonomous TODO workflow checkpoint — 2026-08-27:** Strengthened the Manus worker continuation playbook so each stopped task resumes exactly one TODO item, claims before implementation, runs focused tests and compilation before completion, synchronizes `TODO.md`, `STATE.md`, `TASK_GRAPH.md`, and `CHANGELOG.md`, and fails closed on missing approvals for external changes. Git branch/commit/PR behavior is conditional on repository metadata; the attached directory currently has no `.git` metadata or remote. Added `docs/AUTONOMOUS_TODO_WORKFLOW.md` and prompt-contract coverage. Validation: 15 focused worker/automation tests passed and Python compilation passed.



## Phase 9 real-time execution events checkpoint — 2026-08-27

The selected real-time event-delivery item is complete locally. The existing authenticated API exposes polling at `GET /api/v1/runs/{run_id}/events` and resumable SSE at `GET /api/v1/runs/{run_id}/events/stream`, using sequence IDs and `Last-Event-ID`/`last_event_id` cursors. Added `docs/REALTIME_EXECUTION_EVENTS.md` documenting authentication, ordering, deduplication, reconnect, terminal-state, safe-reconciliation, and bounded-backoff behavior. Added `tests/test_realtime_execution_events.py`; four focused tests, API/test Python compilation, and a precise documentation secret scan passed. WebSocket support is not required because the documented polling and SSE contract satisfies the item; live deployment behavior remains environment-owned.

## Guarded TODO autopilot checkpoint — 2026-08-27

`tools/todo_autopilot.py` now provides standalone one-item TODO execution with fresh Git branches, configurable editing-agent commands, configurable validation commands, post-validation checkbox updates, commit creation, continuous progression, bounded run state, and a repository lock. Validation failures leave the TODO unchecked and preserve the isolated branch for diagnosis. Pushes and pull requests require both `--approve` and `ORVILLE_AUTOMATION_APPROVED=1`.

Focused automation tests pass (4), and Python compilation passes for `orville_core`, `tools`, and `windows_gui.py`. The full regression suite currently reports 3 existing shell/connector API failures unrelated to this change plus one pre-existing HTTP-client deprecation warning. The attached project copy is not a Git worktree, so live branch creation and external GitHub operations remain deployment-owned.


## Phase 9 GUI model controls checkpoint — 2026-08-27

The selected GUI model-controls item is complete locally. Existing authenticated API surfaces cover model compatibility and local-model import/activation, provider health, privacy-aware routing, and local model catalog/runtime controls. Added `docs/GUI_MODEL_CONTROLS.md` documenting the GUI control contract, state handling, privacy/fallback rules, approval boundaries, and deployment ownership. Added `tests/test_gui_model_controls.py`; four focused tests, Python compilation of API/model/provider/routing modules, and a precise secret-pattern scan passed. Related regression tests for GUI controls, local models, runtime controls, provider features/providers, routing, and readiness passed: 45 tests. Git metadata and remote are unavailable in the attached worktree, so no branch, commit, or pull request was fabricated.


## Worker Task 1 checkpoint — GUI-to-engine action wiring — 2026-08-27

The selected GUI integration item is complete as a local, authenticated action-wiring contract. `windows_gui.py` now uses the shared `GUI_ENGINE_ACTIONS` map and `build_engine_action_request` helper for objective creation, execute/resume/retry, cancellation, approval, checkpoint reads, verification reads, artifact listing, and the local monitor pause behavior. Run and task identifiers are URL-encoded, unsupported or incomplete requests fail closed, and responses continue through existing bounded/redacted rendering. `docs/GUI_ENGINE_ACTION_WIRING.md` records the route mapping and explicit boundaries. Focused action-wiring, backend-bridge, and API-contract tests passed (11 total); Python compilation passed for `windows_gui.py` and the new test module. The current backend has no first-class pause or verification-mutation route, so pause remains a local polling control and verification/checkpoint actions remain read projections owned by the engine. Live provider execution, GUI display automation, and production deployment were not exercised.

**Automatic roadmap advancement checkpoint — 2026-08-27:** Updated the worker continuation prompt so a task finishes its current validated one-item turn, then the next worker cycle automatically selects the next eligible unchecked roadmap TODO item. Duplicate reservations, claim-before-work, test/compilation, state synchronization, and approval gates remain required. Added prompt-contract coverage; 15 focused worker tests passed and Python compilation passed.



## Automation activation checkpoint — 2026-08-27

The existing Windows Scheduled Task `Orville Manus Todo Worker` was enabled and verified in `Ready` state with a one-minute cadence. It invokes `tools\orville_manus_worker.py` against the absolute Orville repository path with `--max-active 3`. The worker polls only existing recorded task threads and resumes the same thread with one next unchecked TODO item after a stopped turn. Its continuation prompt requires claim-before-work, focused code/tests validation, state and changelog synchronization, and TODO completion only after validation evidence agrees. No replacement task creation, credential persistence, or scale above three active threads was enabled. The attached repository still has no Git metadata, so branch, commit, push, and pull-request delivery remain unavailable locally; this limitation is documented rather than bypassed.


## Worker Task 2 artifact storage checkpoint — 2026-08-27

The pending artifact-storage TODO item is implemented locally. `ArtifactStore` now provides root-bound registration, digest-based durable version history, bounded text previews, metadata-only binary previews, download-safe opening, and non-destructive retention planning. `orville_core/api.py` exposes authenticated preview, version-history, retention-plan, listing, creation, and download routes. Focused artifact tests passed 4/4 and changed-module compilation passed. The full suite reported 747 passed and 3 unrelated pre-existing connector/shell API failures; those remain release-triage blockers. Retention mutation remains intentionally approval-gated and is not implemented.


## Worker Task 1 checkpoint — persistent observability and release evidence — 2026-08-27

The selected observability item is complete as a local, deterministic evidence slice. Existing `JsonlTraceRecorder`, `TelemetryRegistry`, and production metric aggregation are now covered by a consolidated contract document and focused tests; `orville_core/release_thresholds.py` adds validated pass/fail thresholds for sample count, error rate, P95 latency, saturation, security findings, business health, and release quality. `config/release-thresholds.example.json` is non-secret and reproducible. The retained regression fixture manifest and existing security attack-surface/hardening suites are included in the acceptance evidence. Focused observability, evaluation, security, and threshold validation passed (23 tests); Python compilation and JSON parsing passed. OpenTelemetry export, provider-backed collection, production alerting, deployment, and rollback execution remain deployment-owned limitations.


## Worker Task 2 standalone release checkpoint — 2026-08-27

The selected packaging and standalone lifecycle item is implemented locally. `tools/standalone_release.py` provides plan-first package, install, upgrade, migration, rollback, and deployment workflows; migrations are forward-only, backups are versioned, rollback refuses non-empty destinations, and all mutations require explicit `--execute`. `docs/STANDALONE_RELEASE_WORKFLOWS.md` documents prerequisites and commands. Focused tests passed 4/4, compilation passed, package-plan JSON passed, and a local wheel build completed. The broader suite completed with 747 passing tests and 3 unrelated pre-existing connector/shell API failures. No external deployment or production mutation was performed.


## Worker Task 1 checkpoint — clean-environment product validation — 2026-08-27

The selected final product validation item passed as a credential-free local evidence run. A temporary clean configuration cleared optional cloud, relay, hosted-model, and Ollama variables, retained only a synthetic API token in process memory, and exercised configured cloud-shaped API behavior, local endpoint/provider routing behavior, and no-provider safe fallback behavior. The scenario suite passed with 55 tests and one non-product test-client compatibility warning. Compilation of the project-check and standalone-release entry points passed. Sanitized evidence is retained at `artifacts/clean-environment-validation-2026-08-27.json` and the procedure is documented in `docs/CLEAN_ENVIRONMENT_VALIDATION.md`.

Live cloud availability, a user-managed Ollama process, packaged installer execution, production networking, and multi-replica deployment were not exercised. No credentials, external provider calls, deployments, or destructive actions were used.


## Worker Task 2 roadmap heading normalization checkpoint — 2026-08-27

Normalized the primary roadmap section numbering in `TODO.md`: Phase 5 now uses section 10, Phase 6 section 11, Phase 6A section 11A, and Phase 7 section 12, restoring a unique sequential section sequence through Phase 12. GUI and document subsection prefixes were aligned to their normalized parents without changing task text or statuses. Focused heading and roadmap-automation regression tests passed (9 tests), and the heading test module compiled. The repository is not a Git worktree, so no branch, commit, or PR was created.


## Worker Task 1 checkpoint — roadmap phase and increment separation — 2026-08-27

The selected roadmap consistency item is complete locally. Broad phases remain descriptive capability families, while provider work is explicitly mapped to Phase 2.7, environment reliability to Phase 3.1–3.3, and media work to Phase 6.2. The mapping is stored in `config/roadmap-phase-increments.json` and documented in `docs/ROADMAP_PHASE_INCREMENT_MAP.md`. Nine focused roadmap, heading-normalization, and backlog tests passed; Python compilation and JSON parsing passed. The full regression suite was also run before implementation and retained its existing unrelated failures; project build and preview checks passed.


## Worker Task 2 roadmap identifier checkpoint — 2026-08-27

Added unique machine-readable `TODO-xxxxxxxxxxxx` markers to all 996 actionable checklist records in `TODO.md`. `tools/assign_todo_ids.py` provides deterministic, idempotent local regeneration and preserves existing status markers and task text. Documentation and focused tests were added. Identifier, heading-normalization, and TODO-automation regression validation passed 12/12 tests, and the new utility/test modules compiled successfully. The repository is not a Git worktree, so no branch, commit, or PR was created.


## Worker Task 1 checkpoint — priority backlog metadata completeness — 2026-08-27

The selected roadmap item is complete locally. Every record in `config/priority-backlog.json` now includes explicit `status`, `owner`, `dependencies`, reproducible `acceptance_test` checks, and `artifact_reference` paths, while preserving impact, effort, risk, acceptance evidence, and blocker semantics. The catalog schema advanced to version 1.1, the documentation contract was updated, and six focused backlog/roadmap tests passed with Python compilation and JSON metadata validation. Existing full-suite failures remain unrelated to this catalog-only change.


## Worker Task 2 workflow execution policy checkpoint — 2026-08-27

Implemented explicit deterministic and agentic workflow-step modes in `orville_core/automation.py`. Steps default to deterministic mode; agentic handlers are isolated; unknown modes fail closed; and safety-critical, authorization, validation, persistence, and artifact-integrity categories reject agentic implementations before handler invocation. Focused policy and existing automation regression tests passed 9/9, and Python compilation passed. Documentation was added at `docs/WORKFLOW_EXECUTION_POLICY.md`. The repository is not a Git worktree, so no branch, commit, or PR was created.


## Worker Task 2 durable operation checkpoint checkpoint — 2026-08-27

Implemented schema-versioned, secret-safe `OperationCheckpoint` records and integrated before/after boundaries into serial and parallel workflow execution plus approval resolution. Checkpoint schema version 2 remains backward-readable for schema version 1 files. Focused operation and existing automation tests passed 9/9; workflow, acceptance, and core checkpoint regressions passed 18/18; changed modules and tests compiled successfully. Documentation was added at `docs/OPERATION_CHECKPOINTS.md`. The repository is not a Git worktree, so no branch, commit, or PR was created.


## Worker Task 1 checkpoint — execution-record known limitations — 2026-08-27

The selected reusable-template item is complete locally. The Standard Execution Record Template now includes explicit categories for scope limitations, environment/provider limitations, validation limitations, and unresolved risks/follow-up dependencies. `tests/test_execution_record_template.py` verifies the categories and placeholder semantics; two focused tests and Python compilation passed. The checklist remains a reusable template and is not treated as a completed product milestone.
