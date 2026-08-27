# Orville Roadmap Task Graph

**Graph ID:** `orville-platform-roadmap`  
**Status:** Local control plane and model lifecycle foundations completed; Windows Sandbox worker launch/mapping is live-verified; attestation persistence, Linux/GPU isolation, canary work, and infrastructure-dependent milestones remain
  
**Owner:** Orchestration Agent

| ID | Task | Owner | Status | Evidence |
|---|---|---|---|---|
| M0 | Governance, project control files, repository structure, and operating rules | Orchestration Agent | completed-local | `PROJECT.md`, `STATE.md`, `TASK_GRAPH.md`, `AGENTS.md`, `CHANGELOG.md`, predictable directories, and Phase 0 roadmap checks |
| M1 | Assessment, project workspace, tasks, plans, approvals, events | Orchestration Agent | completed | `docs/ai-agent-platform-assessment.md`, `platform.py`, API and platform tests |
| M2 | Agent modes, model selection, approval contracts | Orchestration Agent | completed | `agent_modes.py`, `platform.py`, API contracts |
| M3 | Workspace tools, checksum writes, revisions, validation, bounded repair | Code Synthesis Agent | completed-local | `workspace.py`, `validation.py`, workspace/validation tests |
| M4 | Preview, visual context, deterministic style patches, smoke reports | Prototype Agent | completed-contract | `preview.py`, preview tests; live browser provider remains unavailable |
| M5 | Workflows, triggers, idempotency, retries, dead-letter, skills, plugins, hooks, subagents | Automation Agent | completed-local | `automation.py`, `extensions.py`, tests |
| M6 | Research, CSV analysis, export, deployment handoff | Research/Data Agent | completed-local | `research_data.py`, tests; external provider execution remains gated |
| M7 | Findings, metrics, evaluations, release gates, role authorization | Verification Agent | completed-local | `governance.py`, `identity.py`, tests |
| M8 | Authenticated API integration | IDE Agent | completed-local | `api.py`, API tests; project members and adapter capability routes added |
| M8.1 | Durable membership and least-privilege role authorization | Security Agent | completed-local | `identity.py`, SQLite persistence, revocation tests |
| M8.2 | Adapter capability and health reporting | Orchestration Agent | completed-local | `adapters.py`, explicit blocked/mock/available states, capability tests |
| M8.3 | Secret references, audit records, and API hardening | Security Agent | completed-local | `secrets_audit.py`, value-free references, redaction, audit tests, API routes |
| M8.4 | Durable scheduling, signed inbound events, and recovery intake | Automation Agent | completed-local | `scheduler.py`, interval schedules, signature validation, idempotency tests |
| M8.5 | Local preview runtime, handoff conflict detection, readiness, telemetry | Prototype and Verification Agents | completed-local | `preview_runtime.py`, `handoff.py`, `readiness.py`, `telemetry.py`, tests |
| M9 | Hardened execution infrastructure | Automation Agent and Security Agent | blocked-by-infrastructure | Requires non-root container/VM, quotas, network and package policy |
| M10 | Browser operator and live preview | Prototype Agent | blocked-by-provider | Requires browser runtime, screenshot/DOM instrumentation, login handoff controls |
| M11 | GitHub/GitLab synchronization and deployment | IDE Agent and Deployment Agent | blocked-by-credentials/provider | Requires configured credentials, remote repository, deployment provider, release approval |
| M12 | Persistent GUI, collaboration, notifications, RAG, multimedia, telemetry | IDE Agent and Research Agent | partially specified | Requires GUI runtime, storage/search services, connector configuration, and observability backend |
| M12.1 | Local model storage, deduplication, runtime capability validation, and streaming resume | IDE Agent and Verification Agent | completed-local | `local_models.py`, `model_runtime.py`, `integration.py`, `api.py`, `windows_gui.py`, `docs/LOCAL_MODEL_RUNTIME.md`, focused tests |
| M12.2 | Imported-model metadata preservation and structured diagnostics | IDE Agent and Verification Agent | completed-local | `local_models.py`, `hub_models.py`, `api.py`, `docs/LOCAL_MODEL_RUNTIME.md`, metadata-diagnostics tests |
| M12.7 | Local-model lifecycle coverage and runtime requirement diagnostics | IDE Agent and Verification Agent | completed-local | `tests/test_local_models.py`, `local_models.py`, 8 focused tests, 256-test regression suite |
| M12.13 | Provider retries, circuit breaking, constrained fallback routing, and resilience tests | Automation Agent and Verification Agent | completed-local | `routing.py`, `tests/test_routing.py`, 13 focused routing tests, 321-test regression suite |
| M12.6 | Guided provider setup, inventory refresh, and safe provider health workflow | IDE Agent and Verification Agent | completed-local | `windows_gui.py`, `docs/PROVIDER_SETUP_WORKFLOW.md`, GUI compilation, provider API/health contracts |
| M12.9 | Provider model discovery, persistent privacy-aware routing, and redacted configuration export | IDE Agent and Verification Agent | completed-local | `provider_features.py`, `routing.py`, `integration.py`, `api.py`, `windows_gui.py`, focused tests, `docs/PROVIDER_DISCOVERY_PRIVACY_EXPORT.md` |
| M12.10 | Persisted discovery catalogs, automatic active-model switching, provider rate limits and usage metrics | IDE Agent and Verification Agent | completed-local | `provider_features.py`, `routing.py`, `api.py`, provider-feature/API tests, `docs/PROVIDER_OPERATIONS_ENTERPRISE.md` |
| M12.11 | Enterprise remote policy storage adapter with local fallback | Automation Agent and Security Agent | completed-local-adapter | `provider_features.py`, `api.py`, `docs/PROVIDER_OPERATIONS_ENTERPRISE.md`; remote hosting, tenant identity, and HA service remain deployment-owned |
| M12.14 | Tenant-scoped catalog federation, policy audit/backups, and concurrency load evidence | Automation Agent, Security Agent, and Verification Agent | completed-local-adapter | `provider_features.py`, `api.py`, `tools/load_test_provider_controls.py`, `artifacts/provider_controls_load_test.json`, `docs/PROVIDER_OPERATIONS_ENTERPRISE.md`, 321-test regression suite |
| M12.12 | Provider retries, circuit breaking, constrained fallback routing, and resilience tests | Automation Agent and Verification Agent | completed-local | `routing.py`, `tests/test_routing.py`, `PROVIDER_ROUTING.md`, 13 focused routing tests, 321-test regression suite |
| M12.3 | Windows local-model manager GUI | IDE Agent and Prototype Agent | completed-local | `windows_gui.py`, inventory/validation/runtime/license/activation/deactivation/removal controls |
| M12.4 | Local workflow integration and model safety controls | Code Synthesis Agent and Verification Agent | completed-local | `model_safety.py`, API workflow tests, unsafe-format and base-model diagnostics |
| M12.5 | Standalone release and deployment gates | Automation Agent and Verification Agent | completed-local | `tools/release_gate.py`, `docs/RELEASE_GATES.md`, compilation, regression, and wheel-build evidence |
| M12.8 | Process sandboxing and cryptographic attestation verification | Security Agent and Verification Agent | partially-complete-local | `sandbox.py`, `sandbox_adapters.py`, `attestations.py`, `attestation_service.py`, `local_models.py`, `windows_gui.py`, `tuf_metadata.py`, `tools/tuf_root_ceremony.py`, `config/tuf-trust-root.example.json`, `tests/test_security_hardening.py`, `tests/test_m12_8_m13_8.py`, and `tmp/live-sandbox-test/automatic_mapping_success.txt`; fallback controls, repository-chain TUF verification, trust-store controls, Cosign/in-toto handling, fail-closed integration, negative tests, activation evidence persistence, GUI attestation policy/status presentation, Windows Sandbox host-folder mapping, and automatic `LogonCommand` execution pass; production trust-root ceremony, Linux live execution, and GPU isolation remain pending |

| M12.14 | Cross-process persistent circuit state | Automation Agent and Verification Agent | completed-local | `circuit_state.py`, `routing.py`, `tests/test_circuit_state.py`, `PROVIDER_ROUTING.md`, 321-test regression suite |

| M12.15 | Safe connector transfers, enriched execution history, and Signal Room local UI checks | Connector Agent, Automation Agent, IDE Agent, and Verification Agent | completed-local | `connector_adapters.py`, `scheduler.py`, `api.py`, `signal_room_checks.py`, `webui/index.html`, focused tests, 312-test regression suite |

| M12.16 | Explicit harmless connector capability-audit path | Connector Agent and Verification Agent | completed-local | `connector_capability.py`, `connector_adapters.py`, `CONNECTOR_OPERATIONS.md`, `tests/test_connector_capability.py`, 321-test regression suite; no external calls because `PROJECT.md` declares no required connector IDs |

| M12.17 | Connector mutation governance and safe capability audit | Connector Agent, Security Agent, and Verification Agent | completed-local | `connector_governance.py`, `connector_capability.py`, `api.py`, `CONNECTOR_OPERATIONS.md`, connector connection/governance tests, 324-test regression suite |

| M12.18 | Blackbox developer-support confirmation assessment | Research Agent and Governance Agent | blocked-external | Public documentation is insufficient; external support correspondence is required, and no request was submitted under the no-post/no-external-side-effects constraint |

| M12.19 | Deterministic Blackbox local fallback and actionable unavailable state | Provider Agent and Verification Agent | completed-local | `cloud_relay.py`, `api.py`, `tests/test_cloud_relay.py`, `docs/BLACKBOX_INTEGRATION_RESEARCH.md`; relay failure-state fallback and redacted status tests pass |

| M12.20 | Blackbox API-key endpoint, request, capability, and error-contract validation | Provider Agent and Verification Agent | completed-local | `blackbox_contract.py`, `api.py`, `providers.py`, `tests/test_blackbox_contract.py`, `docs/BLACKBOX_INTEGRATION_RESEARCH.md`; credential-free validation passed, live API-key behavior remains external |

| M12.21 | Blackbox endpoint- and account-plan-aware capability negotiation | Provider Agent and Verification Agent | completed-local | `blackbox_capabilities.py`, `api.py`, `tests/test_blackbox_capabilities.py`; credential-free negotiation and API exposure validated |
| M12.22 | Blackbox model discovery with safe manual-model fallback | Provider Agent and Verification Agent | completed-local | `blackbox_model_discovery.py`, `api.py`, `tests/test_blackbox_model_discovery.py`; normalization, deduplication, endpoint validation, and manual fallback validated |
| M12.23 | Managed-first Blackbox cloud onboarding without mandatory credentials | Orchestration Agent and IDE Agent | completed-local | `cloud_onboarding.py`, `api.py`, `webui/index.html`, `tests/test_cloud_onboarding.py`; managed-first contract, authenticated onboarding API, and no-script guidance validated |
| M12.24 | Optional Blackbox account-connection action | Orchestration Agent and IDE Agent | completed-local | `cloud_onboarding.py`, `webui/index.html`, `tests/test_cloud_onboarding.py`; optional action metadata and accessible connection link validated |
| M12.25 | Credential redaction and independent clean-environment security review | Security Agent and Verification Agent | completed-local | `security.py`, `checkpoint.py`, `persistence.py`, `tools/security_review.py`, `tests/test_credential_redaction.py`; structured/query/exception redaction, checkpoint persistence, and isolated review validated |

## Worker Task 2 checkpoint — Project initialization rules — 2026-08-27

| Field | Value |
|---|---|
| Task | Define project initialization rules for static sites, full-stack web applications, and mobile applications |
| Owner | Worker Task 2 |
| Status | completed-local |
| Dependencies | Existing Phase 6 web/mobile workflow contracts |
| Evidence | `docs/PROJECT_INITIALIZATION_RULES.md`, `tests/test_project_initialization_rules.py`; 4 focused tests and Python compilation passed |
| Limitations | No framework-specific scaffolder or generated application changed; profile-specific commands remain downstream requirements |

The contract records deterministic profile selection, fail-closed ambiguity handling, safe configuration boundaries, common initialization stages, and profile-specific quality and preview requirements for `static_site`, `full_stack_web`, and `mobile_application`.

## Worker Task 2 checkpoint — Asset lifecycle procedures — 2026-08-27

| Field | Value |
|---|---|
| Task | Define asset briefing, generation, editing, licensing, naming, and storage procedures |
| Owner | Worker Task 2 |
| Status | completed-local |
| Dependencies | Existing Phase 6 web/mobile workflow contracts |
| Evidence | `docs/ASSET_LIFECYCLE_PROCEDURES.md`, `tests/test_asset_lifecycle_procedures.py`; 4 focused tests and Python compilation passed |
| Limitations | No media-generation adapter, format-specific validator, or asset repository changed; rights evidence remains task- and provider-specific |

The procedure defines versioned briefs, source-preserving transformations, licensing states, deterministic naming, storage classes, manifests, approvals, and separate verification outcomes for accepted assets.

## Worker Task 2 checkpoint — Automated build, test, and preview procedures — 2026-08-27

| Field | Value |
|---|---|
| Task | Add automated build, test, and preview procedures |
| Owner | Worker Task 2 |
| Status | completed-local-with-regression-blocker |
| Dependencies | Existing release gate, Signal Room checker, preview workflow, and pytest configuration |
| Evidence | `tools/project_checks.py`, `docs/BUILD_TEST_PREVIEW.md`, `tests/test_project_checks.py`; focused tests (4), compilation, build, and credential-free preview passed |
| Limitations | Full test mode correctly fails on an unrelated pre-existing `orville_core/api.py` failure; evidence retained at `tmp/project_checks_failure.txt` |

The unified entrypoint provides `build`, `test`, `preview`, and `all` modes. Build creates a disposable wheel, test runs the configured regression suite, preview defaults to credential-free local UI checks, and optional API smoke is restricted to a user-configured loopback service.

## Worker Task 2 checkpoint — Document templates — 2026-08-27

| Field | Value |
|---|---|
| Task | Define document templates for reports, specifications, runbooks, and research outputs |
| Owner | Worker Task 2 |
| Status | completed-local |
| Dependencies | Existing research evidence standards, delivery runbook, and implementation specification conventions |
| Evidence | `docs/DOCUMENT_TEMPLATES.md`, `tests/test_document_templates.py`; 4 focused tests and Python compilation passed |
| Limitations | Rendered layout, citation correctness, and domain-specific human review remain deliverable-specific |

The shared contract defines metadata, report, specification, runbook, and research templates with evidence, acceptance, security, approval, validation, rollback, citation, and lifecycle requirements.

## Worker Task 2 checkpoint — Presentation procedures — 2026-08-27

| Field | Value |
|---|---|
| Task | Define presentation planning, content validation, design consistency, and export checks |
| Owner | Worker Task 2 |
| Status | completed-local |
| Dependencies | Existing document templates, asset lifecycle procedures, and research evidence standards |
| Evidence | `docs/PRESENTATION_PROCEDURES.md`, `tests/test_presentation_procedures.py`; 4 focused tests and Python compilation passed |
| Limitations | Rendered slide fidelity, exporter-specific behavior, citation correctness, and rights review remain deck-specific |

The contract defines versioned briefs, narrative planning, evidence mapping, content review, design-system consistency, accessibility checks, multi-format export verification, delivery manifests, and approval gates.

## Worker Task 2 checkpoint — Editable source preservation — 2026-08-27

| Field | Value |
|---|---|
| Task | Preserve editable source formats in addition to exported formats when available |
| Owner | Worker Task 2 |
| Status | completed-local |
| Dependencies | Existing document templates, presentation procedures, and asset lifecycle procedures |
| Evidence | `docs/EDITABLE_SOURCE_PRESERVATION.md`, `tests/test_editable_source_preservation.py`; 4 focused tests and Python compilation passed |
| Limitations | Exporter-specific fidelity, format support, rights evidence, and actual source recovery remain artifact-specific |

The contract defines source/export manifests, immutable source versions, derivative relationships, no-source fallback, deterministic naming, storage boundaries, fidelity checks, approvals, and handoff evidence.

## Worker Task 2 checkpoint — GUI information architecture and user journeys — 2026-08-27

| Field | Value |
|---|---|
| Task | Define the target users, primary workflows, navigation model, information architecture, and user journeys |
| Owner | Worker Task 2 |
| Status | completed-local |
| Dependencies | Existing GUI product requirement, project/task/artifact contracts, and approval boundaries |
| Evidence | `docs/GUI_INFORMATION_ARCHITECTURE.md`, `tests/test_gui_information_architecture.py`; 4 focused tests and Python compilation passed |
| Limitations | Visual design, wireframes, implemented route coverage, and live accessibility behavior remain subsequent GUI tasks |

The contract defines Builder, Operator, Reviewer, and Project owner roles; lifecycle workflows; stable navigation and object hierarchy; contextual detail layout; journey acceptance criteria; and safe interaction boundaries.

## Worker Task 2 checkpoint — GUI wireframes and high-fidelity mockup — 2026-08-27

| Field | Value |
|---|---|
| Task | Produce wireframes and high-fidelity mockups before implementation |
| Owner | Worker Task 2 |
| Status | completed-local |
| Dependencies | Existing GUI information architecture and visual design system |
| Evidence | `docs/GUI_WIREFRAMES.md`, `docs/mockups/orville-control-center.html`, `tests/test_gui_wireframes_mockup.py`; 4 focused tests and Python compilation passed |
| Limitations | Cross-browser visual comparison, implemented route coverage, full assistive-technology testing, and user research remain subsequent GUI tasks |

The low-fidelity wireframes define primary surfaces and responsive/state behavior; the standalone high-fidelity HTML mockup applies the design tokens, semantic structure, responsive thresholds, focus behavior, reduced motion, and touch-target rules.

## Worker Task 2 checkpoint — Theme preferences and status indicators — 2026-08-27

| Field | Value |
|---|---|
| Task | Support light and dark themes, user preference persistence, and clear visual status indicators |
| Owner | Worker Task 2 |
| Status | completed-local |
| Dependencies | Existing visual design system, GUI mockup, and information architecture |
| Evidence | `docs/mockups/orville-control-center.html`, `docs/THEME_AND_STATUS_BEHAVIOR.md`, `tests/test_theme_and_status_behavior.py`; 4 focused tests and Python compilation passed |
| Limitations | Cross-browser storage, system preference integration, complete contrast review, and desktop GUI adoption remain subsequent tasks |

The mockup supports light/dark semantic tokens, an accessible persisted local preference, invalid-value fallback, reduced motion, and text-backed status indicators with bounded actions.

## Worker Task 2 checkpoint — Task composer prototype — 2026-08-27

| Field | Value |
|---|---|
| Task | Create a task composer where users can describe software requirements, attach files, define constraints, select models, and specify acceptance criteria |
| Owner | Worker Task 2 |
| Status | completed-local |
| Dependencies | Existing GUI information architecture, wireframes, themes, and approval boundaries |
| Evidence | `docs/mockups/task-composer.html`, `tests/test_task_composer.py`; 4 focused tests and Python compilation passed |
| Limitations | Backend task creation, upload service, provider discovery, authenticated persistence, and full accessibility testing remain subsequent integration tasks |

The standalone prototype captures requirements, deliverables, local file references, context, constraints, target environment, model preference, acceptance criteria, and safe review-gated draft persistence.

## Worker Task 2 checkpoint — Secret-safe model configuration — 2026-08-27

| Field | Value |
|---|---|
| Task | Create a model configuration flow accepting user-supplied API credentials or endpoint URLs without exposing secrets in the interface |
| Owner | Worker Task 2 |
| Status | completed-local |
| Dependencies | Existing provider setup workflow, approval boundaries, and local API contract |
| Evidence | `docs/mockups/model-configuration.html`, `docs/MODEL_CONFIGURATION_FLOW.md`, `tests/test_model_configuration_flow.py`; 4 focused tests and Python compilation passed |
| Limitations | Production secret-store integration, endpoint allowlisting, capability discovery, authenticated persistence, and desktop GUI integration remain subsequent tasks |

The prototype provides provider presets, endpoint/model validation, masked credential input, redacted review, credential clearing, explicit health-check review, and approval messaging without making network requests.

## Worker Task 2 checkpoint — Capability-aware generation workspace — 2026-08-27

| Field | Value |
|---|---|
| Task | Create a generation workspace for supported text, code, image, audio, video, vision, embedding, and other modalities based on model capability |
| Owner | Worker Task 2 |
| Status | completed-local |
| Dependencies | Existing model manager, configuration flow, imported-model workflow, asset lifecycle, and approval boundaries |
| Evidence | `docs/mockups/generation-workspace.html`, `docs/GENERATION_WORKSPACE.md`, `tests/test_generation_workspace.py`; 4 focused tests and Python compilation passed |
| Limitations | Backend execution, capability discovery, artifact persistence, streaming progress, content policy enforcement, and output fidelity remain integration tasks |

The prototype provides eight capability choices, compatibility-filtered models, modality-specific inputs/outputs, local draft persistence, redacted review, and explicit execution gating without network requests.

## Worker Task 2 checkpoint — Artifact browser prototype — 2026-08-27

| Field | Value |
|---|---|
| Task | Create an artifact browser for viewing, downloading, exporting, versioning, and organizing generated code, documents, media, logs, and reports |
| Owner | Worker Task 2 |
| Status | completed-local |
| Dependencies | Existing generation workspace, editable-source preservation, asset lifecycle, and approval boundaries |
| Evidence | `docs/mockups/artifact-browser.html`, `docs/ARTIFACT_BROWSER.md`, `tests/test_artifact_browser.py`; 4 focused tests and Python compilation passed |
| Limitations | Production indexing, access control, large-file handling, safe untrusted-content rendering, checksum enforcement, and backend integration remain subsequent tasks |

The prototype provides search and type/status filters, safe local preview, source/export metadata, download preparation, explicit export, version comparison, and non-destructive revision actions.

## Worker Task 2 checkpoint — Settings workspace — 2026-08-27

| Field | Value |
|---|---|
| Task | Create settings for providers, models, privacy routing, storage paths, resource limits, schedules, notifications, and user preferences |
| Owner | Worker Task 2 |
| Status | completed-local |
| Dependencies | Existing model configuration, provider setup, theme preferences, storage, scheduling, and approval contracts |
| Evidence | `docs/mockups/settings-workspace.html`, `docs/SETTINGS_WORKSPACE.md`, `tests/test_settings_workspace.py`; 4 focused tests and Python compilation passed |
| Limitations | Backend schema/authorization, path validation, scheduler durability, notification redaction, and desktop GUI integration remain subsequent tasks |

The prototype provides sectioned settings, bounded controls, allowlisted local persistence, non-destructive reset, protected credential references, and approval messaging.

## Validation gate

The current regression suite status is recorded in `STATE.md`: 359 tests pass with one existing HTTP-client deprecation warning, and Python compilation passes for `orville_core` and `windows_gui.py`.
 Connector repair, durable checkpoints, provider routing, streaming resume, local-model lifecycle, provenance, and diagnostics are represented as completed-local where validated. Package and deployment limitations remain explicit.
 Phase 0 control-file validation confirms required files and directories exist and all Phase 0 roadmap items are marked complete.
 Every local implementation has focused tests for positive behavior, authorization or safety boundaries, and failure handling. Windows Sandbox mapping and automatic startup execution are live-verified with the quoted `.wsb` invocation; Linux platform execution, GPU isolation, production trust-root bootstrap, persisted activation/GUI evidence, broader GUI workflow coverage, and production deployment remain infrastructure or hardening gates. Adapter construction and fail-closed capability checks are completed locally.

## Artifact contract

Every completed task identifies changed files, interfaces, commands, tests, limitations, and verification evidence. Unsupported provider-backed features remain blocked or mock/local rather than being represented as production-complete.


## M13 — Security hardening and automated canary deployments

**Specification:** `docs/NEXT_MILESTONE_SECURITY_CANARY.md`

| ID | Task | Owner | Dependencies | Status |
|---|---|---|---|---|
| M13.1 | Security baseline, threat model, and platform matrix | Security Agent | Existing governance and hardening plan | completed-local | `docs/M13_SECURITY_BASELINE_PLATFORM_MATRIX.md`; Windows Sandbox mapping/startup is live-verified, Linux/GPU and production trust-root boundaries are documented |
| M13.2 | Windows isolated worker adapter | Security Agent / Prototype Agent | M13.1 | completed-local-adapter | `sandbox_adapters.py`, `.wsb` generation, live mapping/startup evidence; IPC/GPU validation remains host-dependent |
| M13.3 | Linux isolated worker adapter | Security Agent | M13.1 | completed-local-contract | `sandbox_adapters.py`, fail-closed bubblewrap construction and policy validation; live runtime execution remains host-dependent |
| M13.4 | Sandbox execution integration | Code Synthesis Agent / IDE Agent | M13.2, M13.3 | partially-complete-local | `sandbox.py`, `sandbox_adapters.py`, `worker_protocol.py`, `model_worker.py`, `local_execution.py`, `local_models.py`; canonical JSON-lines protocol, active-attestation/checksum execution boundary, and Windows guest-marker verification are implemented locally; production-path routing, automated guest completion evidence, and Linux live IPC remain pending |
| M13.5 | Persistent trust-store lifecycle | Security Agent | M13.1 | completed-local | `attestations.py`, `attestation_service.py`; production trust-root ceremony remains pending |
| M13.6 | Cosign/in-toto and optional TUF adapters | Security Agent | M13.5 | completed-local-adapter | `attestations.py`, `tuf_metadata.py`, signed/tamper fixtures; external verifier availability remains environment-dependent |
| M13.7 | Security release gate | Verification Agent / Automation Agent | M13.4, M13.6 | completed-local | `orville_core/security_release_gate.py`, `tools/release_gate.py`, `tests/test_m13_7_gate_and_gui.py`; consumes sandbox, required-attestation, dependency, source-integrity, and audit-evidence results with fail-closed diagnostics |
| M13.8 | Versioned canary policy schema | Automation Agent | M13.1, M13.7 | completed-local | `orville_core/canary_policy.py`, `config/canary-policy.example.json`, `tests/test_m12_8_m13_8.py`; cohort monotonicity, bounded holds, minimum samples, health thresholds, approval mode, fresh decisions, rollback target, and rollback limits validated |
| M13.9 | Provider-neutral deployment adapter | Automation Agent / Code Synthesis Agent | M13.8 | completed-local-contract | `orville_core/canary.py`, `SyntheticDeploymentAdapter`; live provider adapter remains deployment-owned |
| M13.10 | Durable canary controller state machine | Automation Agent | M13.8, M13.9 | completed-local | `orville_core/canary.py`, SQLite state, API routes, restart/idempotency tests |
| M13.11 | Canary health evaluator | Verification Agent | M13.10 | completed-local | `CanaryHealthEvaluator`, minimum-sample and critical-security fail-closed tests |
| M13.12 | Automated rollback and release quarantine | Automation Agent / Security Agent | M13.10, M13.11 | completed-local | `orville_core/canary.py`, `tools/m13_12_fault_runner.py`, `artifacts/m13_12_fault_injection.json`, `docs/M13_12_FAULT_INJECTION_AND_DEPLOYMENT_READINESS.md`; all 18 synthetic fault-injection scenarios pass, including threshold breaches, sparse data, security findings, restart/idempotency, rollback failure, policy rejection, and audit redaction; live provider rollback remains deployment-dependent |
| M13.13 | Canary observability and audit | Verification Agent | M13.10, M13.11 | completed-local | Durable canary status and secret-filtered audit event APIs |
| M13.14 | Standalone synthetic canary runner | Prototype Agent | M13.9–M13.13 | completed-local-contract | `SyntheticDeploymentAdapter`, deterministic canary test harness, local fault-boundary tests |
| M13.15 | Production deployment integration | Automation Agent | M13.7, M13.9–M13.14, enterprise credentials | infrastructure-dependent |

**Parallelization:** M13.2–M13.3 and M13.5 may proceed in parallel after M13.1. M13.8–M13.9 may proceed in parallel once the security gate contract is defined. M13.15 is intentionally last.

**Milestone gate:** No production deployment integration is accepted until security negative-boundary tests, required-attestation fail-closed tests, release-gate checks, synthetic canary fault injection, restart/idempotency tests, and a non-production rollback drill pass.


## M14 — Enterprise production readiness

**Specification:** `docs/NEXT_MILESTONE_ENTERPRISE_PRODUCTION.md`

| ID | Task | Owner | Dependencies | Status |
|---|---|---|---|---|
| M14.1 | Enterprise environment and responsibility matrix | Automation / Security Agents | Approved target environment | completed-local-contract | `orville_core/enterprise_readiness.py`, `config/enterprise-environment.example.json`, `docs/M14_ENTERPRISE_ENVIRONMENT.md`, 2 focused tests; actual environment provisioning and operator assignment remain deployment-owned |
| M14.2 | Production trust-root ceremony | Security Agent | M13 trust-store and TUF contracts | partially-complete-local | `orville_core/trust_root_ceremony.py`, `config/production-trust-root-ceremony.example.json`, `docs/M14_PRODUCTION_TRUST_ROOT_CEREMONY.md`, 3 focused tests; live operator approval, production root material, and rotation/revocation drill remain pending |
| M14.3 | Live Windows/Linux sandbox validation | Security / Verification Agents | M13 adapters and supported hosts | partially-complete-local | `artifacts/m14_3_sandbox_validation_2026-08-27.md`; targeted tests pass, but Windows Sandbox/WSL binaries and Linux `bwrap` are unavailable on the approved hosts, so live runtime enforcement remains pending |
| M14.4 | Enterprise identity and authorization | Security / IDE Agents | Tenant environment | partially-complete-local | `orville_core/enterprise_identity.py`, `tests/test_enterprise_identity.py`, `docs/M14_ENTERPRISE_IDENTITY.md`; tenant-scoped scopes, approvals, revocation, bounded claims, and audit are local; live OIDC/SAML, MFA, issuer/audience verification, and revocation propagation remain pending |
| M14.5 | Protected secret management | Automation / Security Agents | Enterprise secret manager | completed-local-contract | `orville_core/protected_secrets.py`, `orville_core/secrets_audit.py`, `tests/test_protected_secrets.py`, `docs/M14_PROTECTED_SECRET_MANAGEMENT.md`; runtime-only resolver, metadata-only rotation/revocation, redacted export, and scrubbing are covered; enterprise provider provisioning, workload identity, scheduled rotation, and access-review evidence remain deployment-owned |
| M14.6 | Reviewed deployment-provider adapter | Automation / Security Agents | M13 canary adapter, M14.1, M14.5 | completed-local-contract | `orville_core/reviewed_deployment_provider.py`, `tests/test_reviewed_deployment_provider.py`, `docs/M14_REVIEWED_DEPLOYMENT_PROVIDER.md`; dry-run, bounded operations, deterministic idempotency, traffic validation, status redaction, and protected credential-reference checks are covered; provider-specific backend, workload identity, provider-side cancellation/idempotency, and rollback drill remain deployment-owned |
| M14.7 | Production metrics and health sources | Verification / Security Agents | M14.4, M14.6 | completed-local-contract | `orville_core/production_metrics.py`, `tests/test_production_metrics.py`, `docs/M14_PRODUCTION_METRICS.md`; explicit tenant/cohort/release scope, freshness cutoff, health aggregation, cross-scope rejection, and canary normalization are covered; production monitoring backend, alerting/SLO policy, completeness checks, and business-health source remain deployment-owned |
| M14.8 | Non-production canary and rollback drill | Automation / Verification Agents | M14.2–M14.7 | in-progress-local | `TODO-45ea939505f7`; `tools/m13_12_fault_runner.py` is the local synthetic-drill baseline. No retained M14.8 non-production evidence bundle is present in this clone. The task remains incomplete pending approved non-production execution and sanitized restart, duplicate-event, partial-failure, injected-fault, rollback-failure, and deterministic-recovery evidence. |
| P6.1 | Deployment and rollback instructions | Automation / Verification Agents | Existing delivery topology and release gates | completed-local | `docs/DELIVERY_RUNBOOK.md`; Compose promotion, backup, health, approval-gated rollback, volume-preserving restore, evidence retention, and non-Compose fallback documented and focused-checked; live provider rollback and production evidence remain deployment-owned |
 |
| A14.1 | Persistent Manus roadmap worker with bounded concurrency | Automation / Orchestration Agents | Existing TODO, task API, and repository control files | completed-local | `tools/orville_manus_worker.py`, `tools/install_orville_manus_worker.ps1`, `docs/ORVILLE_MANUS_WORKER.md`, `tests/test_orville_manus_worker.py`; three active-task slots, reserved TODO selection, refill-after-stop, state recovery, and focused tests pass; persistent hosting and live credentials remain deployment-owned |
| M14.9 | Backup, restore, and disaster recovery operations | Automation / Security Agents | M14.1, M14.4 | planned |
| M14.10 | Production readiness and load gates | Verification Agent | M14.3, M14.8, M14.9 | planned |
| M14.11 | Controlled production canary | Automation Agent | M14.1–M14.10 and explicit approval | infrastructure-dependent |

**Gate:** M14.11 cannot begin until live sandbox, trust-root, identity, secrets, deployment, monitoring, rollback, backup/restore, load, and non-production canary evidence is retained and reviewed.



## 2026-08-27 — Phase 4 delivery checkpoint

| ID | Task | Owner | Dependencies | Status |
|---|---|---|---|---|
| P4.3/P4.4 | Core tests, external-boundary integration tests, smoke validation, independent review, delivery runbook, and evidence manifest | Orchestration Agent with Verification Agent | Blackbox relay/security implementation and documented policies | completed-local |

**Evidence:** `tests/test_external_boundaries.py`, `tests/test_smoke_workflow.py`, `docs/DELIVERY_RUNBOOK.md`, `artifacts/phase4-independent-review.md`, `artifacts/phase4-validation-record.md`, and `artifacts/phase4-delivery-manifest.md`.

**Validation:** 365 pytest tests passed, 159 unittest cases passed, Python compilation passed, Signal Room checks passed, and the clean-workspace main workflow persisted a checkpoint. No live credentials, external account actions, or destructive operations were used.

**Boundary:** Official third-party Blackbox OAuth remains blocked pending documented provider flow. The supplied workspace is not a Git working tree, so commit/status inspection was unavailable.

**Next eligible roadmap item:** TODO 577, define the research source hierarchy by task type and risk level.

## 2026-08-27 — Frontend-backend contract checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P6.3 | Frontend-backend contracts and environment-specific configuration | IDE / Code Synthesis / Verification Agents | Existing API bridge and governance controls | completed-local-contract | `docs/FRONTEND_BACKEND_CONTRACTS.md`, `config/frontend-backend.example.json`, `tests/test_frontend_backend_contract.py`; 3 focused tests, JSON parsing, and Python compilation passed |

The contract defines the `/api/v1` route surface, stable safe error envelopes with operation identifiers, frontend token-storage boundaries, runtime API base URL handling, environment variable ownership, bounded retry/timeout settings, and deployment-owned TLS/origin controls. No live credentials or external services were used.

## 2026-08-27 — Operation-aware API error checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P4.7 | Error messages identify failed operations without exposing secrets | Code Synthesis / Security / Verification Agents | Existing API bridge and secret-redaction boundary | completed-local | `orville_core/api.py`, `tests/test_api_error_messages.py`; 3 focused API tests and Python compilation passed |

The API now returns stable HTTP and validation error envelopes with route-template operation names, bounded retryability, safe messages, compatibility `detail`, and no request payload, dynamic identifier, raw exception, or credential echo.

## 2026-08-27 — Media provenance checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P6.11 | Preserve prompts, source assets, generated outputs, and transformation history | Media / Security / Verification Agents | Asset lifecycle procedures and repository redaction boundary | completed-local-contract | `orville_core/media_provenance.py`, `docs/MEDIA_PROVENANCE.md`, `tests/test_media_provenance.py`; 3 focused tests, compilation, and public-import verification passed |

The local contract copies source and generated assets into a bounded root, records checksums and ordered transformations, redacts prompts and metadata, preserves a prompt digest, and prevents source mutation or path escape. Remote storage, signing, and multi-process coordination remain deployment or hardening boundaries.

## 2026-08-27 — Media validation checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P6.12 | Format, resolution, duration, accessibility, and usage-rights checks | Media / Security / Verification Agents | Media provenance and asset lifecycle procedures | completed-local-contract | `orville_core/media_validation.py`, `docs/MEDIA_VALIDATION_CHECKS.md`, `tests/test_media_validation.py`; 5 focused tests, compilation, and public-import verification passed |

The local validator applies modality format allowlists, file-size bounds, declared dimension and duration thresholds, alt-text/transcript/caption requirements, and explicit license/rights-holder/source requirements. Codec decoding, caption quality, remote rights validation, and legal clearance remain outside this contract.

## 2026-08-27 — Media visual verification checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P6.13 | Define visual verification and media quality checks appropriate to each artifact | Media / Verification / Security Agents | Asset lifecycle procedures and media provenance/validation contracts | completed-local-contract | `docs/MEDIA_VISUAL_VERIFICATION.md`, `tests/test_media_visual_verification.py`; 3 focused tests, compilation, structural checks, and secret-safe wording checks passed |

The local contract defines complete-artifact inspection and modality-specific checks for image, audio, video, document, animation, and mixed artifacts, with severity-based rejection, accessibility/provenance evidence, and second-review requirements. Live media-provider decoding, publication playback, and external rights clearance remain outside this local contract.

## 2026-08-27 — Document and presentation verification checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P6.21 | Verify page or slide counts, citations, links, charts, images, and legibility | Document / Presentation / Verification Agents | Document templates and presentation procedures | completed-local-contract | `orville_core/document_verification.py`, `docs/DOCUMENT_VERIFICATION.md`, `tests/test_document_verification.py`; 5 focused tests, compilation, and public-import verification passed |

The local verifier checks supported artifact formats, structural page/slide counts, citation/link/image/chart presence, Markdown legibility, and alt text. PDF/PPTX rendered legibility, OCR, font inspection, remote link reachability, citation quality, and human accessibility review remain explicit review gates.

## 2026-08-27 — Visual design-system checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P14.2 | Cohesive visual design system for product interfaces | IDE / Prototype / Verification Agents | GUI information architecture and web/mobile acceptance criteria | completed-local-contract | `config/design-system.example.json`, `docs/VISUAL_DESIGN_SYSTEM.md`, `tests/test_visual_design_system.py`; 3 focused tests, JSON parsing, and compilation passed |

The shared contract covers typography, semantic light/dark colors, spacing, elevation, icons, controls, forms, tables, cards, notifications, dialogs, empty states, status indicators, motion, responsive breakpoints, accessibility, security, and review rules. Existing clients are not claimed as fully migrated; wireframes and implementation-level visual regression remain later gates.

## 2026-08-27 — Reusable components and interaction patterns checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P14.3 | Define reusable components and interaction patterns so the interface remains consistent as features expand | IDE / Prototype / Verification Agents | Visual design system, GUI information architecture, and web/mobile acceptance criteria | completed-local-contract | `docs/REUSABLE_COMPONENTS_INTERACTIONS.md`, `tests/test_reusable_components_interactions.py`; 3 focused tests, compilation, structural checks, and secret-safe wording checks passed |

The local contract defines component families, public state behavior, deterministic mutation/loading/error patterns, composition rules, shared accessibility/responsive requirements, and review evidence. Existing GUI and web screens are not claimed as fully migrated; implementation-level visual regression and platform-specific accessibility evidence remain follow-up gates.

## 2026-08-27 — Task-plan view checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P14.4 | Create a task-plan view showing the generated task graph, dependencies, assigned agents, statuses, blockers, retries, and verification gates | IDE / Prototype / Verification Agents | Task graph, GUI information architecture, visual design system, reusable components, and web/mobile acceptance criteria | completed-local-contract | `docs/TASK_PLAN_VIEW.md`, `tests/test_task_plan_view.py`; 3 focused tests, compilation, structural checks, and secret-safe wording checks passed |

The local contract defines the read-only plan projection, graph fields, dependency readiness, assignment metadata, status vocabulary, blocker and retry evidence, verification gates, accessible tree fallback, bounded rendering, and safe mutating-control boundaries. The existing GUI does not claim this view is implemented; live visual regression and integration with durable task data remain follow-up gates.

## 2026-08-27 — Imported-model workflow checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P14.5 | Create an imported-model workflow for selecting local files or folders, scanning metadata, validating compatibility, activating models, and viewing diagnostics | IDE / Prototype / Verification Agents | Local model catalog, model validation, asset lifecycle, security, and GUI model-manager contracts | completed-local-contract | `docs/IMPORTED_MODEL_WORKFLOW.md`, `tests/test_imported_model_workflow.py`; 3 focused tests, compilation, structural checks, and secret-safe wording checks passed |

The local contract defines safe file/folder selection, reference/copy/link storage, metadata scanning without executing model code, compatibility and resource validation, approval-gated activation, stable diagnostics, lifecycle states, and non-destructive removal. Live GPU/runtime provisioning, provider upload, and full GUI integration remain follow-up gates.

## 2026-08-27 — Safe defaults and advanced settings checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P14.6 | Minimize unnecessary configuration by providing safe defaults while keeping advanced settings available | IDE / Prototype / Verification Agents | Settings workspace, visual design system, privacy routing, resource limits, and approval contracts | completed-local-contract | `config/settings-defaults.example.json`, `docs/SAFE_DEFAULTS_AND_ADVANCED_SETTINGS.md`, `tests/test_safe_defaults.py`; 3 focused tests, JSON parsing, compilation, structural checks, and secret-safe wording checks passed |

The local contract defines local-first, manual, bounded, system-aware defaults, explicit override precedence, progressive advanced settings boundaries, fail-closed validation, non-destructive reset, and approval requirements for consequential changes. Production provisioning, live schedules, external notifications, and full client migration remain follow-up gates.

## 2026-08-27 — Polished visual-style checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P14.3 | Professional, modern, consistent, clear visual style with performance and usability safeguards | IDE / Prototype / Verification Agents | Visual design system, GUI information architecture, and wireframes | completed-local-contract | `config/visual-style.example.json`, `docs/VISUAL_STYLE_GUIDE.md`, `tests/test_visual_style_guide.py`; 3 focused tests, JSON parsing, and compilation passed |

The style profile defines hierarchy, density, status semantics, performance budgets, 44 px controls, reduced-motion behavior, responsive expectations, theme parity, and review gates. Existing clients are not claimed as fully migrated; rendered visual regression and live accessibility/performance evidence remain later gates.

## 2026-08-27 — Operational dashboard checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P14.4 | Dashboard for active tasks, recent runs, model availability, health, failures, and artifacts | Prototype / IDE / Verification Agents | GUI information architecture, visual design system, and existing API bridge | completed-local-implementation | `windows_gui.py`, `docs/DASHBOARD_SPECIFICATION.md`, `tests/test_dashboard.py`; 3 focused tests and compilation passed |

The desktop control center now presents six bounded aggregate cards and refreshes them asynchronously from existing read-only routes. Failures degrade to safe labels without exposing raw payloads or exceptions. Per-provider live health, web/mobile parity, and visual regression remain later gates.

## 2026-08-27 — Unified model-manager checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P14.7 | Model manager for cloud, endpoint, Ollama, and imported local models | Prototype / IDE / Security / Verification Agents | Provider setup, imported-model workflow, model routing, and GUI design system | completed-local-implementation | `windows_gui.py`, `docs/MODEL_MANAGER_SPECIFICATION.md`, `tests/test_model_manager.py`; 3 focused tests and compilation passed |

The desktop model manager unifies provider setup and local inventory with direct setup/import actions, lifecycle controls, and explicit secret/file-retention boundaries. Provider health and compatibility remain API-owned checks; no model files are deleted by registration removal.

## 2026-08-27 — Execution monitor checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P14.6 | Execution monitor for progress, logs, agent/tool activity, elapsed time, and lifecycle controls | Prototype / IDE / Verification Agents | Task plan view, execution controls, event persistence, and GUI design system | completed-local-implementation | `windows_gui.py`, `docs/EXECUTION_MONITOR_SPECIFICATION.md`, `tests/test_execution_monitor.py`; 3 focused tests and compilation passed |

The desktop monitor reads persisted run/event endpoints, bounds event rendering to 80 entries, derives elapsed time from timestamps, and provides safe observation, approval-resume, retry, and cancellation controls. Backend hard pause remains a future engine capability.

## 2026-08-27 — Verification and review checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P14.9 | Verification/review view for acceptance criteria, test/source/visual evidence, defects, risks, and approval | IDE / Verification / Security Agents | Task plan, execution monitor, document/media verification, and GUI design system | completed-local-implementation | `windows_gui.py`, `docs/VERIFICATION_REVIEW_SPECIFICATION.md`, `tests/test_verification_review.py`; 3 focused tests and compilation passed |

The review surface is read-only, bounded, URL-safe, and secret-safe. It presents persisted evidence without claiming to certify evidence quality or approval authorization.

## 2026-08-27 — Plain-language workflow checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P14.10 | Make primary workflows understandable without agent-framework, task-graph, or provider-API knowledge | UX / IDE / Verification Agents | GUI information architecture, visual design system, safety and API contracts | completed-local-implementation | `windows_gui.py`, `docs/PLAIN_LANGUAGE_WORKFLOWS.md`, `tests/test_plain_language_workflows.py`; 3 focused tests and compilation passed |

The first-run path now follows Describe, Prepare, Work, and Review in plain language. Technical terms remain available in specialist views, while sensitive actions, credentials, approvals, and safe error boundaries remain authoritative.


## 2026-08-27 — Progressive-disclosure checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P14.11 | Use progressive disclosure so complex options do not overwhelm first-time users | UX / IDE / Verification Agents | Plain-language workflows, safe defaults, visual design system, and GUI provider/model surfaces | completed-local-implementation | `windows_gui.py`, `docs/PROGRESSIVE_DISCLOSURE.md`, `tests/test_progressive_disclosure.py`; 3 focused tests and compilation passed |

Provider setup now shows only provider type and model name initially. Endpoint, credentials, timeout, capabilities, privacy, and provider identity controls are revealed through an explicit reversible disclosure control without losing entered values. Approval, credential, recovery, and accessibility boundaries remain visible and authoritative.

## 2026-08-27 — Accessibility acceptance checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P14.13 | Provide keyboard navigation, visible focus states, semantic controls, screen-reader labels, sufficient color contrast, reduced-motion support, and accessible error feedback | UX / IDE / Verification Agents | Visual design system, web/mobile acceptance criteria, reusable components, and error/recovery contracts | completed-local-contract | `docs/ACCESSIBILITY_ACCEPTANCE_CRITERIA.md`, `tests/test_accessibility_acceptance.py`; 3 focused tests, compilation, structural checks, and secret-safe wording checks passed |

The local contract defines criteria and evidence for keyboard operation, focus visibility, semantic naming, announcements, contrast, reduced motion, zoom/reflow, alternatives, touch targets, and accessible error recovery across critical workflows. Live assistive-technology, browser, mobile, and production visual testing remain follow-up gates.


## 2026-08-27 — GUI accessibility checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P14.12 | Provide keyboard navigation, visible focus states, semantic controls, screen-reader labels, sufficient contrast, reduced-motion support, and accessible error feedback | UX / IDE / Verification Agents | Visual design system, plain-language workflows, API error boundary, and native GUI surfaces | completed-local-implementation | `windows_gui.py`, `docs/GUI_ACCESSIBILITY.md`, `tests/test_gui_accessibility.py`; 3 focused tests and compilation passed |

The desktop control center now exposes predictable keyboard entry points, visible focus indication, descriptive workspace labeling, contrast-aware non-color focus treatment, no-animation accessibility feedback, and operation-specific secret-safe recovery messages. Platform-specific screen-reader, keyboard, and rendered contrast evidence remain follow-up review gates.


## 2026-08-27 — Responsive-layout checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P14.14 | Support responsive layouts for desktop, tablet, and smaller screens where the target application permits it | UX / IDE / Verification Agents | Visual design system, GUI wireframes, accessibility contract, and desktop shell | completed-local-implementation | `windows_gui.py`, `docs/RESPONSIVE_LAYOUTS.md`, `tests/test_responsive_layouts.py`; 3 focused tests and compilation passed |

The native control center now uses width-aware dashboard reflow, wrapping labels, a row-aware refresh action, and existing context/sidebar collapse thresholds. The primary objective workspace remains available in the smallest supported native window; web/mobile parity and pixel-level review remain follow-up gates.

## 2026-08-27 — Destructive-action confirmation checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P14.15 | Prevent destructive actions from occurring without clear confirmation and explain their consequences | UX / IDE / Verification Agents | Execution controls, approval gates, idempotency, accessibility, and delivery recovery contracts | completed-local-contract | `docs/DESTRUCTIVE_ACTION_CONFIRMATIONS.md`, `tests/test_destructive_action_confirmations.py`; 3 focused tests, compilation, structural checks, and secret-safe wording checks passed |

The local contract requires explicit action/scope previews, consequence explanations, reversible alternatives, approval and authorization boundaries, single-use expiry, stale-preview rejection, non-advancing failure states, accessible dialogs, and safe recovery diagnostics. Live provider authorization and production destructive-action exercises remain follow-up gates.

## 2026-08-27 — Localization-ready text checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P14.16 | Add localization-ready text handling and avoid embedding user-visible copy directly in business logic | UX / IDE / Verification Agents | Plain-language workflows, accessibility, error/recovery, and settings contracts | completed-local-contract | `orville_core/localization.py`, `config/locales/en-US.json`, `tests/test_localization.py`; 3 focused tests and Python compilation passed |

The local text boundary resolves stable keys through locale resources, falls back to the default locale, safely interpolates parameters, returns missing keys without raising, and keeps workflow/error copy outside orchestration logic. Additional locale translation, full UI migration, and translator review remain follow-up gates.

## 2026-08-27 — Degraded GUI availability checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P14.17 | Ensure the GUI remains usable when cloud providers, local endpoints, connectors, or model runtimes are unavailable | UX / IDE / Verification Agents | Provider routing, connector health, runtime compatibility, workflow state, localization, and recovery contracts | completed-local-implementation | `windows_gui.py`, `docs/GUI_DEGRADED_AVAILABILITY.md`, `tests/test_gui_degraded_availability.py`; 3 focused tests, compilation, structural checks, and secret-safe wording checks passed |

The desktop GUI now maps unavailable dependency categories to stable titles, plain-language explanations, and safe recovery actions. Drafts, task plans, local artifacts, diagnostics, and review remain usable; cloud failure does not broaden privacy routing, retries are bounded, and mutating retries require idempotency. Live provider, connector, runtime, and external recovery remain deployment-owned.

## Worker Task 2 checkpoint — Help, errors, onboarding, and recovery guidance — 2026-08-27

| Field | Value |
|---|---|
| Task | Provide contextual help, meaningful error messages, onboarding guidance, tooltips, confirmation dialogs, and recovery actions |
| Owner | Worker Task 2 |
| Status | completed-local |
| Dependencies | `docs/ACCESSIBILITY_ACCEPTANCE_CRITERIA.md`, `docs/DESTRUCTIVE_ACTION_CONFIRMATIONS.md`, and `docs/GUI_INFORMATION_ARCHITECTURE.md` |
| Evidence | `docs/HELP_AND_RECOVERY_GUIDANCE.md`, `docs/mockups/help-recovery.html`, `tests/test_help_and_recovery.py`; 4 focused tests and Python compilation passed |
| Limitations | The prototype is standalone and synthetic; live assistive-technology review and production GUI integration remain downstream validation work |

The contract defines contextual help, first-run onboarding, safe operation-specific errors, distinct loading/empty/offline/blocked/failed/partial/long-running states, accessible confirmations, state-aware recovery, localization readiness, and secret-safe diagnostics. The prototype performs no external requests or state-changing operations.
s.


## 2026-08-27 — GUI architecture boundary checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P14.17 | Select a GUI architecture and document presentation, orchestration, model-service, storage, and external-integration boundaries | UX / IDE / Security / Verification Agents | GUI information architecture, frontend-backend contracts, core platform architecture, and standalone rules | completed-local-contract | `docs/GUI_ARCHITECTURE_BOUNDARIES.md`, `tests/test_gui_architecture_boundaries.py`; 3 focused tests and compilation passed |

Orville now has an explicit layered native-client architecture. The GUI is a client of authenticated API capabilities; orchestration, model services, storage, and external adapters retain authoritative state, policy, credentials, and side-effect responsibilities. Future web/mobile clients reuse versioned API contracts rather than GUI internals.


## Worker Task 2 checkpoint — GUI quality and major-journey test coverage — 2026-08-27

| Field | Value |
|---|---|
| Task | Add component tests, workflow tests, accessibility checks, responsive-layout tests, and end-to-end tests for the major user journeys |
| Owner | Worker Task 2 |
| Status | completed-local |
| Dependencies | Existing GUI mockups, workflow specifications, accessibility criteria, responsive-layout contract, and reusable-component guidance |
| Evidence | `docs/GUI_TEST_STRATEGY.md`, `tests/test_gui_quality.py`; 5 focused tests and Python compilation passed |
| Limitations | Coverage is deterministic and credential-free; live browser automation, screenshot comparison, screen-reader testing, performance measurement, and backend-integrated e2e execution remain separate release gates |

The aggregate suite verifies shared component contracts, individual workflow surfaces, accessibility and secret-safety markers, responsive behavior, and the ordered objective-to-delivery journey with explicit review and approval boundaries.

## 2026-08-27 — GUI performance measurement checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P14.18 | Measure startup time, interaction latency, memory usage, and performance with large task graphs and artifact collections | IDE / Prototype / Verification Agents | GUI architecture, workflow state, artifact contracts, and supported Windows runtime | completed-local-measurement | `tools/measure_gui_performance.py`, `docs/GUI_PERFORMANCE_MEASUREMENT.md`, `docs/GUI_PERFORMANCE_BASELINE.json`, `tests/test_gui_performance_measurement.py`; 4 focused tests, compilation, and 1,000-task/500-artifact benchmark passed |

The reproducible offline harness measures fresh `windows_gui` import startup, representative state-handling latency, peak traced Python memory, and serialization for a fixed large workload. The Windows-target baseline measured 328.055 ms startup, 2.185 ms average interaction handling, and 100,235 peak traced bytes; all local gates passed. Window painting, disk/network latency, and production hardware variance remain outside this local measurement.


## 2026-08-27 — Visual regression checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P14.18 | Add visual regression checks for the design system and critical screens | UX / IDE / Verification Agents | Visual design system, visual style guide, GUI mockup, accessibility, and responsive contracts | completed-local-implementation | `tools/visual_regression.py`, `artifacts/visual_regression_baseline.json`, `docs/VISUAL_REGRESSION.md`, `tests/test_visual_regression.py`; 3 focused tests, baseline check, and compilation passed |

The repository now has a deterministic fail-closed baseline for design tokens and the canonical control-center mockup. Baseline changes require explicit review; pixel-perfect cross-platform screenshot comparison and web/mobile baselines remain follow-up gates.


## Worker Task 2 checkpoint — Standalone GUI operations documentation — 2026-08-27

| Field | Value |
|---|---|
| Task | Document how to run, build, package, update, and deploy the GUI independently of Manus |
| Owner | Worker Task 2 |
| Status | completed-local |
| Dependencies | `docs/GUI_ARCHITECTURE_BOUNDARIES.md`, `docs/DELIVERY_RUNBOOK.md`, release hardening contract, PyInstaller spec, packaging script, and installer script |
| Evidence | `docs/GUI_STANDALONE_OPERATIONS.md`, `tests/test_gui_standalone_operations.py`; 3 focused tests and Python compilation passed |
| Limitations | Code signing, live provider/browser verification, production deployment, and infrastructure-owned rollback evidence remain target-environment responsibilities |

The guide documents source execution, local API startup, validation, PyInstaller builds, portable packaging, installed-mode updates, data preservation, Compose deployment, rollback, recovery, and standalone security boundaries.


## 2026-08-27 — GUI sensitive-data exposure checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P14.19 | Verify that logs, prompts, API keys, local paths, and sensitive data are not unintentionally exposed in the interface | Security / UX / IDE / Verification Agents | GUI architecture boundaries, API error contracts, localization, degraded availability, and state handling | completed-local-implementation | `windows_gui.py`, `docs/GUI_SENSITIVE_DATA.md`, `tests/test_gui_sensitive_data.py`; 3 focused tests and compilation passed |

The native GUI now applies a bounded safe display projection, redacts sensitive keys and credential-like strings, hides local endpoint/path values, suppresses raw manager exceptions, and does not echo submitted objectives into output or context widgets. Live traffic, secret-store, crash/clipboard, and web/mobile exposure review remain separate release gates.


## Worker Task 2 checkpoint — Workload classification — 2026-08-27

| Field | Value |
|---|---|
| Task | Classify tasks as one-shot, recurring, event-triggered, webhook-driven, or persistent-service workloads |
| Owner | Worker Task 2 |
| Status | completed-local |
| Evidence | `docs/WORKLOAD_CLASSIFICATION.md`, `orville_core/agent_contracts.py`, `orville_core/__init__.py`, `tests/test_workload_classification.py`; 5 focused tests and Python compilation passed |
| Classification precedence | Persistent runtime, schedule, webhook, event/data/connector/task-event, then manual/unspecified |
| Limitations | Classification is descriptive and side-effect-free; scheduler, event intake, webhook authentication, and persistent supervision remain execution-owned controls |

Added the typed `WorkloadClassification` result and `classify_workload` API. Explicit workload types must agree with inferred trigger/runtime semantics; unsupported or conflicting values fail closed.


## 2026-08-27 — Schedule ownership and lifecycle checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P15.2 | Define schedule ownership, timezone handling, expiration, pause, resume, and failure notification behavior | Automation / Security / Verification Agents | Workload classification, scheduler lease semantics, persistence, notification policy, and approval boundaries | completed-local-contract | `docs/SCHEDULE_OWNERSHIP_LIFECYCLE.md`, `tests/test_schedule_ownership_lifecycle.py`; 3 focused tests and compilation passed |

The schedule contract now defines owner/delegation responsibility, IANA timezone and UTC normalization rules, expiration and lifecycle transitions, pause/resume and missed-run policy, durable failure-before-notification ordering, bounded notification retries, deduplication, and secret-safe notification payloads. Runtime schema migration and live delivery remain follow-up implementation gates.


## Worker Task 2 checkpoint — Scheduled workflow idempotency — 2026-08-27

| Field | Value |
|---|---|
| Task | Ensure scheduled workflows are idempotent and safe to retry |
| Owner | Worker Task 2 |
| Status | completed-local |
| Evidence | `orville_core/scheduler.py`, `orville_core/automation.py`, `tests/test_scheduled_idempotency.py`, `docs/SCHEDULED_WORKFLOW_IDEMPOTENCY.md`; 6 focused scheduler/automation tests and compilation passed |
| Behavior | Deterministic occurrence keys, durable execution records, completed-run deduplication, failure retry without schedule advancement, success-only schedule advancement, and bounded leases |
| Limitations | Provider-side idempotency and compensation remain handler responsibilities; missed-interval catch-up and configurable backoff remain separate scheduling work |

The dispatcher now reuses the same occurrence key and execution slot across retries. A failed occurrence remains due, while a successful occurrence advances the schedule only after completion and releases its lease.


## 2026-08-27 — Long-running job state checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P15.3 | Define state storage for long-running jobs and recovery after restart | Automation / Storage / Security / Verification Agents | Schedule lifecycle, scheduled idempotency, workflow store, scheduler leases, artifact provenance, and recovery policy | completed-local-contract | `docs/LONG_RUNNING_JOB_STATE.md`, `tests/test_long_running_job_state.py`; 3 focused tests and compilation passed |

The contract defines durable workflow/task/event/lease/artifact/recovery records, atomic state and event transitions, checkpoint sequencing, stale-lease protection, restart reconciliation, deterministic recovery, retention, and fail-closed handling for unproven external side effects. Runtime supervisor implementation and crash/multi-process testing remain follow-up gates.


## Worker Task 2 checkpoint — Execution target selection — 2026-08-27

| Field | Value |
|---|---|
| Task | Define when to use sandbox execution, web hosting, attached desktop execution, or persistent computing |
| Owner | Worker Task 2 |
| Status | completed-local |
| Evidence | `docs/EXECUTION_TARGET_SELECTION.md`, `tests/test_execution_target_selection.py`; 3 focused tests and Python compilation passed |
| Decision | Choose the smallest target satisfying persistence, interface, operating-system, network, resource, and data-residency requirements |
| Limitations | Environment-specific capacity, live deployment, provider verification, and infrastructure approval remain target-environment checks |

The decision contract distinguishes ephemeral sandbox runs, managed browser/API hosting, connected Windows desktop execution, and persistent computing. It records lifecycle, data, secret, resource, recovery, and escalation boundaries and prefers managed hosting over self-managed infrastructure when requirements fit.


## 2026-08-27 — Health monitoring, structured logging, and runbook checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P15.5 | Add health monitoring, structured logs, and operational runbooks | Operations / Security / Reliability / Verification Agents | Production metrics, usage health, readiness, secret-safe audit, long-running state, and delivery runbook contracts | completed-local-contract | `docs/HEALTH_MONITORING_LOGGING_RUNBOOKS.md`, `tests/test_health_monitoring_logging_runbooks.py`; 3 focused tests and compilation passed |

The local contract defines stable health states, safe signal thresholds, bounded structured JSON events, correlation and redaction boundaries, retention/access rules, operational ownership, and standalone runbooks for unavailable services, elevated failures, saturation, security findings, and release/canary failures. Live alerting and hosted monitoring remain deployment-owned.


## Worker Task 2 checkpoint — Workflow dry-run mode — 2026-08-27

| Field | Value |
|---|---|
| Task | Add dry-run mode for workflows that can mutate external state |
| Owner | Worker Task 2 |
| Status | completed-local |
| Evidence | `orville_core/automation.py`, `docs/WORKFLOW_DRY_RUN.md`, `tests/test_workflow_dry_run.py`; 3 focused tests and Python compilation passed |
| Behavior | Mutating steps marked `mutates_external_state=True` are skipped in preview and returned as `dry_run_actions`; safe local steps may execute; live approval rules remain unchanged |
| Limitations | Provider availability, permission, quota, payload acceptance, and deployment success require separate live validation; handlers remain responsible for provider-side idempotency and compensation |

The dry-run path performs no provider or network call for skipped mutations, does not fabricate mutation success output, does not satisfy approval, and exposes an explicit `_dry_run` marker for callers.


## 2026-08-27 — Approval checkpoint milestone

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P15.7 | Add approval checkpoints for irreversible or high-impact actions | Orchestration / Security / Authorization / Verification Agents | Destructive-action confirmations, dry-run, workflow executor, audit boundary, and long-running state | completed-local-implementation | `orville_core/automation.py`, `docs/APPROVAL_CHECKPOINTS.md`, `tests/test_approval_checkpoints.py`; 3 focused tests and compilation passed |

The workflow store now persists deterministic approval checkpoints with bounded action/target summaries, pending and terminal decisions, approver references, first-decision preservation, and idempotent creation/resolution. The contract requires exact scope confirmation, single-use approval, fail-closed behavior, dry-run separation, and safe evidence. Live identity-provider and production destructive-action exercises remain deployment-owned.


## Worker Task 2 checkpoint — Secret-handling rules — 2026-08-27

| Field | Value |
|---|---|
| Task | Define secret-handling rules for environment variables, configuration files, logs, artifacts, and screenshots |
| Owner | Worker Task 2 |
| Status | completed-local |
| Evidence | `docs/SECRET_HANDLING_RULES.md`, `tests/test_secret_handling_rules.py`; 3 focused tests and Python compilation passed |
| Contract | Protected runtime injection, non-secret references, server-side consumption, pre-retention redaction, artifact and screenshot review, rotation/revocation, and fail-safe recovery |
| Limitations | Provider secret managers, live deployment permissions, and incident response execution remain environment-owned controls |

The contract covers environment variables, configuration files, logs, artifacts, reports, screenshots, recordings, GUI fields, backups, and packaged outputs. It prohibits raw credentials in source, task prompts, client bundles, retained diagnostics, screenshots, and evidence.


## 2026-08-27 — External-boundary validation checkpoint

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P16.2 | Add input validation and output sanitization at external boundaries | Security / API / Provider / Verification Agents | Secret handling, API contracts, provider boundaries, cloud relay, connector policy, and sensitive GUI display | completed-local-implementation | `orville_core/boundary.py`, `docs/EXTERNAL_BOUNDARY_VALIDATION.md`, `tests/test_external_boundaries.py`; 6 focused tests and compilation passed |

The shared boundary module now validates bounded text, safe identifiers, HTTP(S) URLs without embedded credentials, and explicit local-host permission; it recursively bounds and sanitizes external output, credential-like text, bearer tokens, sensitive keys, and local paths. Existing provider/cloud-relay tests remain passing. Live fuzzing, browser payload review, parser hardening, and production traffic inspection remain release gates.


## Worker Task 2 checkpoint — Core unit-test coverage — 2026-08-27

| Field | Value |
|---|---|
| Task | Add unit tests for task parsing, graph validation, routing, state transitions, and artifact registration |
| Owner | Worker Task 2 |
| Status | completed-local |
| Evidence | `tests/test_core_unit_contracts.py`; 5 focused tests and Python compilation passed |
| Coverage | `TaskNode` parsing round-trip, graph dependency/owner validation, endpoint and routing-request fail-closed validation, persisted engine state transitions, and artifact hash/media-type/explicit-ID registration |
| Limitations | Existing broader suites remain separate regression coverage; this item adds representative unit-level contract checks without external services |

The focused unit tests use temporary local state and synthetic inputs only. No credentials, external providers, or destructive operations were used.


## Worker Task 2 checkpoint — Regression fixtures — 2026-08-27

| Field | Value |
|---|---|
| Task | Add regression fixtures for previously fixed failures |
| Owner | Worker Task 2 |
| Status | completed-local |
| Evidence | `tests/fixtures/regressions/manifest.json`, `scheduled-retry-same-slot.json`, `workflow-dry-run-mutation.json`, `nested-secret-redaction.json`, and `tests/test_regression_fixtures.py`; 4 focused tests and Python compilation passed |
| Covered fixes | Scheduled retry identity and success-only advancement, workflow dry-run mutation suppression, and nested credential redaction |
| Limitations | Fixtures cover local deterministic regressions; external-provider, browser, connector, and deployment regressions remain separate integration scope |

The retained fixture manifest maps each fixture to its prior fix and expected behavior. Tests load the fixtures, exercise the corrected behavior with synthetic local handlers, and assert no external calls or credentials are required.


## 2026-08-27 — Boundary integration-test milestone

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P16.4 | Add integration tests for filesystem, GitHub, browser, model, connector, and scheduling boundaries where available | Integration / Security / Verification Agents | Workspace, local model, browser, provider, connector bridge, webhook, scheduler, and API contracts | completed-local-fixture-coverage | `tests/test_boundary_integrations.py`; 6 focused tests and compilation passed |

The discoverable suite uses temporary directories, synthetic model assets, patched local connector transport, browser JSON persistence, local SQLite workflow/schedule stores, provider error fixtures, and synthetic webhook signatures. It covers filesystem, model, GitHub/connector, browser, scheduling, provider, and webhook boundary behavior without external credentials or live side effects. Existing specialized suites remain complementary.


## Worker Task 2 checkpoint — Deterministic test data and mock services — 2026-08-27

| Field | Value |
|---|---|
| Task | Add deterministic test data and mock external services where practical |
| Owner | Worker Task 2 |
| Status | completed-local |
| Evidence | `tests/fixtures/deterministic_external_cases.json`, `tests/fixtures/mock_external_service.py`, and `tests/test_deterministic_mocks.py`; 3 focused tests and Python compilation passed |
| Coverage | Deterministic health, echo, and unavailable HTTP responses; JSON client success/error handling; credential-free fixture scanning |
| Limitations | The mock is local-only and does not replace provider-specific, browser, connector, or deployment integration tests |

The fixture service binds only to loopback on an ephemeral port, returns stable JSON, suppresses request logging, and shuts down with a bounded thread join. No credentials or external network calls are required.


## 2026-08-27 — Performance-test milestone

| ID | Task | Owner | Dependencies | Status | Evidence |
|---|---|---|---|---|---|
| P16.6 | Add performance tests for graph size, parallel fan-out, retries, and artifact volume | Performance / Orchestration / Verification Agents | Task graph engine, bounded worker pool, retry policy, checkpoint store, and artifact store | completed-local-smoke-gates | `tests/test_performance_boundaries.py`; 4 focused tests and compilation passed in 4.23 seconds |

The suite covers 100-task graph execution, four-worker fan-out over twelve independent tasks, transient retry completion capped at three attempts, and 100-artifact registration/listing. Thresholds are bounded smoke gates rather than production capacity claims; load calibration remains a separate operational activity.


## Worker Task 2 checkpoint — Security attack-surface tests — 2026-08-27

| Field | Value |
|---|---|
| Task | Add security tests for secret leakage, prompt injection, path traversal, unsafe commands, and unauthorized actions |
| Owner | Worker Task 2 |
| Status | completed-local |
| Evidence | `tests/test_security_attack_surfaces.py`; 5 focused tests and Python compilation passed |
| Coverage | Secret redaction, bounded prompt-injection-as-data handling, filesystem traversal/write rejection, sandbox shell syntax and secret-environment rejection, and allowlist/approval enforcement |
| Limitations | These are local policy tests; live browser, connector, provider, deployment, and production telemetry security validation remain separate scope |

The tests use synthetic values, temporary directories, and local policy objects. They do not execute unsafe commands, contact external services, use credentials, or authorize side effects.


## Worker Task 2 checkpoint — Failed-test triage gate — 2026-08-27

| Field | Value |
|---|---|
| Task | Require all failed tests to be triaged before release |
| Owner | Worker Task 2 |
| Status | completed-local |
| Evidence | `tools/test_triage.py`, `config/test_triage_manifest.json`, `docs/TEST_FAILURE_TRIAGE.md`, `tests/test_test_triage.py`, and `tools/project_checks.py` integration; 3 focused tests, validator CLI, and Python compilation passed |
| Gate | Project checks now require a valid triage manifest after the regression suite and before release acceptance |
| Fail-closed rules | Missing fields, duplicate test IDs, unsupported or untriaged statuses, malformed schema, and missing manifest reject the gate |
| Limitations | Automatic failure discovery and live release-system integration remain downstream work |

The checked-in manifest is empty because no failure is currently declared by this task. Any failed test must be recorded with an owner, classification, action, and secret-free evidence before release validation can pass.


## Worker Task 1 checkpoint — Representative workflow acceptance tests — 2026-08-27

| Field | Value |
|---|---|
| Task | Add acceptance tests for complete representative workflows |
| Owner | Worker Task 1 |
| Status | completed-local |
| Dependencies | Existing `TaskIntake`, `OrchestrationEngine`, checkpoint, verification, and artifact contracts |
| Evidence | `tests/test_acceptance_workflows.py`; 2 focused tests and Python compilation passed |
| Coverage | Credential-free coding workflow and research workflow from local intake/evidence through execution, independent verification, durable checkpoint state, and artifact/source preservation |
| Limitations | Live provider, browser, connector, deployment, production, and GUI acceptance remain environment-specific and were not exercised |


## Worker Task 2 checkpoint — Deployment commands by target — 2026-08-27

| Field | Value |
|---|---|
| Task | Create deployment scripts or commands for each supported target |
| Owner | Worker Task 2 |
| Status | completed-local |
| Evidence | `deploy.ps1`, `docs/DEPLOYMENT_TARGET_COMMANDS.md`, and `tests/test_deployment_commands.py`; 3 focused tests, PowerShell parser validation, and Python compilation passed |
| Targets | Sandbox, web hosting, attached desktop, and persistent computing |
| Safety | Dry-run by default; `-Execute` is explicit and target-scoped; no credentials, endpoint discovery, or live deployment performed |
| Limitations | Live host capacity, Docker availability, code signing, infrastructure approval, and post-deployment smoke tests remain downstream gates |

The dispatcher reuses existing project-check, Compose, release-builder, and installer commands. It validates required files before execution and preserves documented approval and release-hardening boundaries.


## Worker Task 1 checkpoint — Deployment targets and environment variables — 2026-08-27

| Field | Value |
|---|---|
| Task | Define supported deployment targets and required environment variables |
| Owner | Worker Task 1 |
| Status | completed-local |
| Dependencies | Existing runtime configuration, delivery runbook, portable release hardening, and environment template |
| Evidence | `docs/DEPLOYMENT_TARGETS_AND_ENVIRONMENT.md`, `.env.example`, `tests/test_deployment_targets.py`; 3 focused tests and Python compilation passed |
| Targets | Local Python process, installed Windows release, portable Windows release, Docker Compose small-team topology, and disposable container check |
| Limitations | Managed cloud, Kubernetes, serverless, public multi-replica, and live production promotion are explicitly excluded or deployment-owned |


## Worker Task 2 checkpoint — Pre-deployment and post-deployment smoke checks — 2026-08-27

| Field | Value |
|---|---|
| Task | Add pre-deployment validation and post-deployment smoke tests |
| Owner | Worker Task 2 |
| Status | completed-local |
| Evidence | `tools/deployment_validation.py`, `tests/test_deployment_validation.py`, and updated `deploy.ps1`; 7 focused deployment tests, PowerShell syntax validation, and Python compilation passed |
| Preflight | Validates target-specific repository prerequisites for sandbox, web hosting, attached desktop, and persistent computing without credentials or deployment |
| Smoke | Performs bounded HTTP health checks, returns safe evidence, and rejects remote hosts unless `--allow-remote` is explicit |
| Limitations | Live deployment, production host availability, code signing, provider authentication, and infrastructure-owned smoke checks remain downstream gates |

The dispatcher now runs preflight before target actions and local HTTP smoke checks after web-hosting and persistent-computing execution. Dry-run remains the default.


## Worker Task 1 checkpoint — Versioning and release notes — 2026-08-27

| Field | Value |
|---|---|
| Task | Add versioning and release notes |
| Owner | Worker Task 1 |
| Status | completed-local |
| Dependencies | Existing `pyproject.toml` version, release artifacts, delivery runbook, and changelog conventions |
| Evidence | `docs/VERSIONING_AND_RELEASE_NOTES.md`, `RELEASE_NOTES.md`, `tests/test_versioning_release_notes.py`; 3 focused tests and Python compilation passed |
| Version baseline | `0.1.0`, sourced from `[project].version` in `pyproject.toml` |
| Limitations | Live target promotion, provider authorization, and production release evidence remain environment-specific |


## Worker Task 1 checkpoint — Least-privilege permissions — 2026-08-27

| Field | Value |
|---|---|
| Task | Add permission minimization for connectors, repositories, files, and remote systems |
| Owner | Worker Task 1 |
| Status | completed-local |
| Dependencies | Existing `PermissionSet`, `FilesystemPolicy`, `NetworkPolicy`, connector, workspace, and approval contracts |
| Evidence | `orville_core/security.py`, `docs/LEAST_PRIVILEGE_PERMISSIONS.md`, `tests/test_least_privilege_permissions.py`; 4 focused tests and Python compilation passed |
| Enforcement | Default-deny task grants, connector scope allowlists, repository ID/write separation, root-bound file resolution, and normalized remote host/action allowlists |
| Limitations | Live connector, repository, remote-system, and deployment enforcement remains environment-specific and was not exercised |


## Worker Task 2 checkpoint — Explicit sensitive-operation confirmation — 2026-08-27

| Field | Value |
|---|---|
| Task | Add explicit confirmation for payments, publishing, deletion, account changes, and other sensitive operations |
| Owner | Worker Task 2 |
| Status | completed-local |
| Implementation | `orville_core/confirmations.py` and `docs/DESTRUCTIVE_ACTION_CONFIRMATIONS.md` |
| Validation | `tests/test_confirmations.py` plus existing destructive-action tests: 7 passed; Python compilation passed; precise secret-pattern scan passed |
| Safety | Exact operation, target, scope, requester, fingerprint, expiry, and single-use receipt; fail-closed mismatch, expiry, invalid, and reuse behavior |
| Limitations | UI integration, provider authorization, and deployment-specific audit persistence remain caller/deployment responsibilities |


## Worker Task 1 checkpoint — Sensitive-domain safe handling — 2026-08-27

| Field | Value |
|---|---|
| Task | Add safe handling for medical, legal, tax, financial, insurance, real-estate, gambling, and major life decisions |
| Owner | Worker Task 1 |
| Status | completed-local |
| Dependencies | Existing `TaskIntake`, clarification gates, approval controls, and safety boundaries |
| Evidence | `orville_core/workflow.py`, `orville_core/__init__.py`, `tests/test_sensitive_domain_safety.py`; 4 focused tests and Python compilation passed |
| Enforcement | Stable domain classification, informational-only metadata, professional-review requirement, consequential-action approval gate, and prohibited autonomous behavior list |
| Limitations | No domain advice, emergency triage, jurisdiction-specific legal/tax analysis, professional review, or live policy evaluation is provided by this local contract |


## Worker Task 2 checkpoint — Untrusted-content execution boundary — 2026-08-27

| Field | Value |
|---|---|
| Task | Add untrusted-content detection and prevent tool execution based solely on external instructions |
| Owner | Worker Task 2 |
| Status | completed-local |
| Implementation | `orville_core/untrusted_content.py`, `tests/test_untrusted_content.py` |
| Validation | 5 focused untrusted-content tests plus existing external-boundary tests passed; Python compilation and precise secret-pattern scan passed |
| Safety | External, tool-result, model-output, and downloaded-artifact origins cannot authorize execution; trusted origins still require separate explicit endorsement |
| Limitations | Provider-specific adapter wiring and durable audit persistence remain follow-up integration work |


## Worker Task 2 checkpoint — Incident response, credential rotation, and recovery — 2026-08-27

| Field | Value |
|---|---|
| Task | Define incident response, credential rotation, and recovery procedures |
| Owner | Worker Task 2 |
| Status | completed-local |
| Implementation | `docs/INCIDENT_RESPONSE_CREDENTIAL_ROTATION_RECOVERY.md`, `tests/test_incident_response_procedures.py` |
| Validation | 4 focused documentation tests passed; Python compilation and precise secret-pattern scan passed |
| Coverage | Severity, intake, containment, rotation/revocation, backup/checkpoint restoration, staged recovery, failure handling, closure, and post-incident review |
| Safety | No secrets in evidence; external instructions cannot authorize recovery; sensitive operations require explicit confirmation |
| Limitations | Live provider rotation, infrastructure recovery, and production incident exercises remain deployment-owned |


## Worker Task 1 checkpoint — Dependency and supply-chain review — 2026-08-27

| Field | Value |
|---|---|
| Task | Add dependency and supply-chain review for downloaded packages, scripts, and artifacts |
| Owner | Worker Task 1 |
| Status | completed-local |
| Dependencies | Existing package manifest, download manager, artifact store, sandbox, release gates, and untrusted-content controls |
| Evidence | `orville_core/supply_chain.py`, `docs/SUPPLY_CHAIN_REVIEW.md`, `tests/test_supply_chain_review.py`; 4 focused tests and Python compilation passed |
| Enforcement | Approved-root containment, SHA-256 matching, provenance requirement, independent script review gate, and non-executing value-only review results |
| Limitations | No packages installed, scripts executed, artifacts downloaded, or external vulnerability/index/repository scanners invoked; live supply-chain validation remains environment-specific |


## Worker Task 2 checkpoint — Orchestration test matrix — 2026-08-27

| Field | Value |
|---|---|
| Task | Create a test matrix covering orchestration, delegation, graph dependencies, retries, failures, approvals, and integration |
| Owner | Worker Task 2 |
| Status | completed-local |
| Implementation | `docs/ORCHESTRATION_TEST_MATRIX.md`, `tests/test_orchestration_test_matrix.py` |
| Validation | 4 focused matrix-completeness tests passed; Python compilation and precise secret-pattern scan passed |
| Coverage | Orchestration, delegation, graph dependencies, retries, failures, approvals, integration, and safety-integration rows with executable test references |
| Limitations | Live provider, browser, deployment, infrastructure, and production-account behavior remains deployment-owned |


## Worker Task 1 checkpoint — Rollback and recovery verification — 2026-08-27

| Field | Value |
|---|---|
| Task | Add rollback procedures and recovery verification |
| Owner | Worker Task 1 |
| Status | completed-local |
| Dependencies | Existing delivery runbook, deployment validation, canary rollback controller, checkpoint persistence, backup, and health contracts |
| Evidence | `orville_core/recovery.py`, `docs/ROLLBACK_AND_RECOVERY_VERIFICATION.md`, `tests/test_rollback_recovery.py`; 4 focused tests and Python compilation passed |
| Enforcement | Explicit approval reference, named rollback target, evidence preservation, backup checksum verification, authenticated health, read-only state, and smoke-workflow checks |
| Limitations | No deployment command, database restore, external service, credential operation, or live rollback drill was executed; target-specific recovery remains deployment-owned |


## Worker Task 2 checkpoint — Structured correlation logging — 2026-08-27

| Field | Value |
|---|---|
| Task | Add structured logs with correlation IDs for multi-agent executions |
| Owner | Worker Task 2 |
| Status | completed-local |
| Implementation | `orville_core/structured_logging.py`, `tests/test_structured_logging.py` |
| Structured fields | UTC timestamp, level, event, correlation ID, execution ID, optional task and agent IDs, bounded sanitized fields |
| Validation | 4 focused logging tests plus existing credential-redaction tests passed with `ResourceWarning` treated as an error; Python compilation passed |
| Safety | Existing nested secret sanitizer reused; JSONL writer closes handles; no credentials or external services used |
| Limitations | Adapter-specific logger wiring and centralized log transport remain follow-up integration work |


## Worker Task 1 checkpoint — Execution metrics — 2026-08-27

| Field | Value |
|---|---|
| Task | Add metrics for task duration, success rate, retry count, failure class, and verification outcomes |
| Owner | Worker Task 1 |
| Status | completed-local |
| Dependencies | Existing dependency-free `TelemetryRegistry`, execution, retry, failure, and verification contracts |
| Evidence | `orville_core/telemetry.py`, `tests/test_telemetry_metrics.py`; 3 focused tests and Python compilation passed |
| Metrics | Duration mean, success/failure rates, aggregate retries, bounded failure classes, and verification outcome counts |
| Limitations | Existing adapter-specific instrumentation and production dashboard/report export remain follow-up work |


## Worker Task 2 checkpoint — Operational dashboards and reports — 2026-08-27

| Field | Value |
|---|---|
| Task | Add operational dashboards or reports where the target environment supports them |
| Owner | Worker Task 2 |
| Status | completed-local |
| Implementation | `tools/operational_report.py`, `docs/OPERATIONAL_DASHBOARDS_AND_REPORTS.md`, `tests/test_operational_report.py` |
| Report fields | Target, event count, execution count, failure count, success rate, duration statistics, status counts, and data-quality flags |
| Validation | 4 focused report tests passed; Python compilation and precise secret-pattern scan passed |
| Safety | Bounded input, malformed-record rejection, empty-log semantics, no raw event payloads, and no sensitive follow-up actions |
| Limitations | Hosted log collection, live dashboards, alert delivery, and infrastructure SLO collection remain deployment-owned |


## Worker Task 1 checkpoint — Maintenance ownership and upgrade cadence — 2026-08-27

| Field | Value |
|---|---|
| Task | Define maintenance ownership and upgrade cadence |
| Owner | Worker Task 1 |
| Status | completed-local |
| Dependencies | Existing operations, release, security, supply-chain, rollback, telemetry, and project-state contracts |
| Evidence | `docs/MAINTENANCE_OWNERSHIP_AND_UPGRADE_CADENCE.md`, `tests/test_maintenance_ownership.py`; 3 focused tests and Python compilation passed |
| Ownership | Core, integrations, security, GUI, release/deployment, documentation, incident recovery, Orchestration Agent, and environment owner boundaries documented |
| Cadence | Every change, weekly, monthly, quarterly, pre-release, and post-release activities defined |
| Limitations | Live owner assignment, alerting, dependency scanners, infrastructure monitoring, and recovery exercises remain environment-specific |


## Worker Task 2 checkpoint — Standalone README — 2026-08-27

| Field | Value |
|---|---|
| Task | Write a standalone README with prerequisites, installation, configuration, usage, examples, and troubleshooting |
| Owner | Worker Task 2 |
| Status | completed-local |
| Implementation | `README.md`, `tests/test_standalone_readme.py` |
| Coverage | Prerequisites, installation, configuration, usage, examples, testing, deployment, troubleshooting, security boundaries, and standalone limitations |
| Validation | 4 focused README tests passed; Python compilation and precise secret-pattern scan passed |
| Safety | No live credentials, external services, destructive actions, or unsupported production claims |
| Limitations | Provider authorization, live deployment, hosted monitoring, and external-service availability remain environment-owned |


## Worker Task 1 checkpoint — Architecture document — 2026-08-27

| Field | Value |
|---|---|
| Task | Write an architecture document describing agents, graph state, tools, artifacts, and security boundaries |
| Owner | Worker Task 1 |
| Status | completed-local |
| Dependencies | Existing agent registry, task graph, orchestration engine, checkpoint, artifact, telemetry, security, approval, and recovery contracts |
| Evidence | `docs/ARCHITECTURE.md`, `tests/test_architecture_document.py`; 3 focused tests and Python compilation passed |
| Coverage | Agents, handoffs, DAG state, execution, checkpoints, tools, providers, artifacts, verification, recovery, observability, and security boundaries documented |
| Limitations | Architecture claims implemented local contracts; live provider, browser, connector, infrastructure, and production validation remain environment-specific |


## Worker Task 2 checkpoint — Operator runbook — 2026-08-27

| Field | Value |
|---|---|
| Task | Write an operator runbook for health checks, failures, connector issues, and recovery |
| Owner | Worker Task 2 |
| Status | completed-local |
| Implementation | `docs/OPERATOR_RUNBOOK.md`, `tests/test_operator_runbook.py` |
| Coverage | Health/readiness, failure triage, connector diagnosis, fallback, credential exposure handling, checkpoint/backup recovery, staged restoration, escalation, and closure |
| Validation | 4 focused runbook tests passed; Python compilation and precise secret-pattern scan passed |
| Safety | Untrusted instructions cannot authorize action; secrets stay out of evidence; sensitive operations remain confirmation-gated |
| Limitations | Live provider, connector, infrastructure, and production recovery actions remain deployment-owned |


## Worker Task 2 checkpoint — Task template catalog — 2026-08-27

| Field | Value |
|---|---|
| Task | Write task templates for research, coding, automation, web development, media, documents, and deployments |
| Owner | Worker Task 2 |
| Status | completed-local |
| Implementation | `config/task-templates.json`, `docs/TASK_TEMPLATES.md`, `tests/test_task_templates.py` |
| Coverage | Seven requested workload types with objective, deliverables, constraints, acceptance criteria, and verification fields |
| Validation | 4 focused tests passed; Python compilation, JSON parsing, seven-template count, and precise secret-pattern scan passed |
| Safety | Synthetic, standalone starting contracts; sensitive operations remain approval-gated and external instructions remain untrusted |
| Limitations | Templates do not authorize live providers, deployments, or external side effects; task-specific refinement remains required |


## Worker Task 1 checkpoint — Contributor guide — 2026-08-27

| Field | Value |
|---|---|
| Task | Write a contributor guide covering local development, tests, review, and release procedures |
| Owner | Worker Task 1 |
| Status | completed-local |
| Dependencies | Existing README, repository rules, test tooling, release notes, delivery runbook, security, supply-chain, rollback, and maintenance contracts |
| Evidence | `docs/CONTRIBUTING.md`, `tests/test_contributor_guide.py`; 3 focused tests and Python compilation passed |
| Coverage | Standalone setup, repository layout, development workflow, tests, review, security, release/deployment, handoffs, completion, and troubleshooting |
| Limitations | Live ownership, hosted infrastructure, provider authorization, and production release actions remain environment-specific |


## Worker Task 2 checkpoint — Standalone examples — 2026-08-27

| Field | Value |
|---|---|
| Task | Provide examples that run without Manus-specific functionality |
| Owner | Worker Task 2 |
| Status | completed-local |
| Implementation | `examples/README.md`, `examples/basic_run.py`, `examples/local_operational_report.py`, `tests/test_standalone_examples.py` |
| Coverage | Deterministic checkpointed workflow and local operational-report generation using temporary data |
| Validation | 3 focused example tests passed; Python compilation and precise credential-pattern scan passed |
| Safety | No Manus/MCP/browser dependency, provider credential loading, external service, or sensitive action |
| Limitations | Provider, connector, browser, deployment, and infrastructure behavior remains separately documented and environment-owned |


## Worker Task 1 checkpoint — Graceful degradation — 2026-08-27

| Field | Value |
|---|---|
| Task | Document graceful-degradation behavior when connectors or websites are unavailable |
| Owner | Worker Task 1 |
| Status | completed-local |
| Dependencies | Existing GUI degraded-availability, workflow-state, connector, provider-routing, browser, approval, privacy, retry, and recovery contracts |
| Evidence | `docs/GRACEFUL_DEGRADATION.md`, `tests/test_graceful_degradation.py`; 3 focused tests and Python compilation passed |
| Coverage | Stable unavailable states, safe recovery, local/offline continuity, fallback restrictions, bounded idempotent retry, partial evidence, escalation, and security boundaries |
| Limitations | Live connector recovery, website availability, browser authentication, provider failover, alert delivery, and production network behavior remain environment-specific |


## Worker Task 2 checkpoint — Canonical glossary — 2026-08-27

| Field | Value |
|---|---|
| Task | Maintain a glossary for task graph, agent role, artifact, verification gate, connector, and execution state |
| Owner | Worker Task 2 |
| Status | completed-local |
| Implementation | `docs/GLOSSARY.md`, `tests/test_glossary.py` |
| Coverage | Required six terms plus execution, correlation, task-node, dependency, handoff, approval, checkpoint, retry, dry-run, provider, and runbook terms |
| Validation | 4 focused glossary tests passed; Python compilation and precise secret-pattern scan passed |
| Safety | Definitions preserve approval gates, untrusted-content boundaries, and identifier usage without credentials |
| Maintenance | Contract or state-name changes must update the glossary and run its focused test |


## Worker Task 1 checkpoint — Repeated failure pattern review — 2026-08-27

| Field | Value |
|---|---|
| Task | Review completed task graphs for repeated failure patterns |
| Owner | Worker Task 1 |
| Status | completed-local |
| Dependencies | Existing checkpoint event history, structured logs, telemetry, operational reports, and failure-triage contracts |
| Evidence | `orville_core/failure_patterns.py`, `tests/test_failure_patterns.py`, `docs/REPEATED_FAILURE_REVIEW.md`; 3 focused tests and Python/package compilation passed |
| Coverage | Terminal-run filtering, recognized failure events, sanitized class aggregation, distinct run/task counts, repetition thresholds, bounded output, and secret-safe reporting |
| Limitations | No causal inference, cross-installation aggregation, alerting, automatic remediation, or production analytics; findings do not authorize policy or operational changes |


## Worker Task 2 checkpoint — Reusable fixes catalog — 2026-08-27

| Field | Value |
|---|---|
| Task | Convert recurring fixes into reusable templates, tests, skills, or automation |
| Owner | Worker Task 2 |
| Status | completed-local |
| Implementation | `config/reusable-fixes.json`, `docs/REUSABLE_FIXES.md`, `tests/test_reusable_fixes.py` |
| Categories | Release validation; sensitive-operation safety; operator recovery; standalone delivery; terminology and observability |
| Validation | 4 focused tests passed; Python compilation, JSON validation, referenced-asset checks, and precise secret-pattern scan passed |
| Safety | Reuse does not authorize sensitive actions; external instructions remain untrusted; credentials stay in protected runtime boundaries |
| Limitations | Catalog is guidance and linkage, not a new execution engine; live provider, deployment, and account behavior remains environment-owned |


## Worker Task 1 checkpoint — Lifecycle phase-duration metrics — 2026-08-27

| Field | Value |
|---|---|
| Task | Measure time spent in planning, execution, verification, and recovery |
| Owner | Worker Task 1 |
| Status | completed-local |
| Dependencies | Existing `TelemetryRegistry`, task metrics, workflow lifecycle, verification, recovery, checkpoint, and operational-report contracts |
| Evidence | `orville_core/telemetry.py`, `tests/test_phase_duration_metrics.py`; 3 focused tests and Python compilation passed |
| Coverage | Normalized planning, execution, verification, and recovery phase aggregates; mean durations; invalid-value rejection; coexistence with existing task metrics |
| Limitations | Automatic instrumentation at every production lifecycle boundary and hosted time-series collection remain environment-specific follow-up work |


## Worker Task 1 checkpoint — Agent-assignment performance review — 2026-08-27

| Field | Value |
|---|---|
| Task | Review whether agent assignments match actual task performance |
| Owner | Worker Task 1 |
| Status | completed-local |
| Dependencies | Existing task ownership, agent registry, handoff, telemetry, failure-pattern, and phase-duration contracts |
| Evidence | `orville_core/assignment_review.py`, `docs/AGENT_ASSIGNMENT_REVIEW.md`, `tests/test_assignment_review.py`; 3 focused tests, Python compilation, and export validation passed |
| Coverage | Aggregate assignment outcomes, completion/failure rates, verification failures, attempt and duration means, terminal-run filtering, and bounded secret-safe reporting |
| Limitations | No ranking, blame, causal inference, automatic reassignment, cross-installation aggregation, production analytics, or live routing changes |


## Worker Task 2 checkpoint — Cleanup blocked — 2026-08-27

| Field | Value |
|---|---|
| Task | Remove obsolete dependencies, connectors, instructions, and artifacts |
| Status | blocked |
| Blocker | Explicit confirmation is required before destructive deletion; candidate paths need named-path review and retention checks |
| Actions taken | Inspection only; no files or directories deleted |
| Risk | Deleting runtime data, active logs, release evidence, or required connectors without scoped approval |



## Worker Task 2 checkpoint — Readiness report update — 2026-08-27

| Field | Value |
|---|---|
| Task | Update the readiness report after material environment or architecture changes |
| Owner | Worker Task 2 |
| Status | completed-local |
| Implementation | `docs/READINESS_REPORT.md`, `tests/test_readiness_report.py` |
| Coverage | Current architecture, local checks, target readiness, security, observability, deployment gates, and known blockers |
| Validation | 4 focused readiness-report tests passed; Python compilation and precise secret-pattern scan passed |
| Known blockers | Full regression collection fails on `task_status` default binding; cleanup remains approval-blocked |
| Limitations | Production readiness, provider authorization, live infrastructure, hosted monitoring, and external recovery remain environment-owned |


## Worker Task 1 checkpoint — Prioritized backlog — 2026-08-27

| Field | Value |
|---|---|
| Task | Maintain a prioritized backlog with impact, effort, dependencies, and risk |
| Owner | Worker Task 1 |
| Status | completed-local |
| Dependencies | Existing TODO roadmap, task graph, maintenance cadence, failure-pattern review, and approval/blocker contracts |
| Evidence | `config/priority-backlog.json`, `docs/PRIORITIZED_BACKLOG.md`, `tests/test_prioritized_backlog.py`; 3 focused tests, JSON parsing, and Python compilation passed |
| Coverage | Traceable existing TODO records, status and priority vocabulary, impact/effort/risk scores, dependency and blocker overrides, acceptance evidence, and review cadence |
| Limitations | Planning catalog only; it does not create tasks, change TODO status automatically, execute work, or authorize destructive actions |


## Worker Task 2 checkpoint — Milestone roadmap review — 2026-08-27

| Field | Value |
|---|---|
| Task | Conduct a quarterly roadmap review or an equivalent milestone review |
| Owner | Worker Task 2 |
| Status | completed-local |
| Implementation | `docs/MILESTONE_ROADMAP_REVIEW_2026-08-27.md`, `tests/test_milestone_roadmap_review.py` |
| Review coverage | Completed-local capabilities, conditional targets, P0/P1/P2 priorities, dependencies, risks, blockers, next-milestone gates, and maintenance cadence |
| Validation | 4 focused review tests passed; Python compilation and precise secret-pattern scan passed |
| Known blockers | Full-suite collection defect at `task_status`; cleanup requires explicit confirmation and named-path review |
| Limitations | Live provider, identity, browser, deployment, infrastructure, monitoring, and production recovery evidence remains environment-owned |


## Worker Task 1 checkpoint — GUI-to-engine API contract — 2026-08-27

| Field | Value |
|---|---|
| Task | Define the GUI-to-engine API contract for objectives, task graphs, runs, checkpoints, providers, local models, verification records, artifacts, approvals, and event streams |
| Owner | Worker Task 1 |
| Status | completed-local |
| Dependencies | Existing API routes, models, checkpoint persistence, provider/local-model services, artifact store, approval gates, event streams, and GUI state contracts |
| Evidence | `docs/GUI_ENGINE_API_CONTRACT.md`, `tests/test_gui_engine_api_contract.py`; 3 focused tests and Python compilation passed |
| Coverage | Versioned envelopes, resource ownership/projections, engine-controlled transitions, authentication/authorization, approval separation, redaction, idempotency, event replay, degraded states, and additive compatibility |
| Limitations | Authenticated backend bridge and GUI action wiring remain separate implementation items; no external services or credentials were exercised |


## Worker Task 2 checkpoint — Authenticated GUI backend bridge — 2026-08-27

| Field | Value |
|---|---|
| Task | Add an authenticated backend bridge for the GUI with authorization, request validation, CORS policy, rate limits, and redacted audit logging |
| Owner | Worker Task 2 |
| Status | completed-local |
| Implementation | Existing `orville_core/api.py` security bridge; `docs/GUI_BACKEND_BRIDGE.md`; `tests/test_gui_backend_bridge.py` |
| Controls | Exact bearer authentication; route and mutation authorization; bounded Pydantic validation; explicit CORS allowlist; credentials disabled; one-minute rate limiting; redacted audit persistence; safe error responses |
| Validation | 4 focused tests passed; API/audit Python compilation and precise documentation secret scan passed |
| Safety | Synthetic audit values only; no external credentials, provider, browser, account, or destructive operation used |
| Limitations | TLS, identity lifecycle, secret management, centralized retention, alerting, backups, and infrastructure policy remain deployment-owned |


## Worker Task 2 checkpoint — Real-time execution events — 2026-08-27

| Field | Value |
|---|---|
| Task | Add real-time execution event delivery through a documented polling, SSE, or WebSocket contract |
| Owner | Worker Task 2 |
| Status | completed-local |
| Implementation | Existing authenticated API polling and SSE routes; `docs/REALTIME_EXECUTION_EVENTS.md`; `tests/test_realtime_execution_events.py` |
| Contract | Polling returns checkpoint events; SSE emits ordered sequence IDs and supports `Last-Event-ID`/`last_event_id` resume |
| Validation | 4 focused tests passed; API/test Python compilation and precise documentation secret scan passed |
| Safety | Authentication required; event data is untrusted; GUI must reconcile state and approval from checkpoints and contracts |
| Limitations | Live deployment, proxy buffering, reconnect behavior, and infrastructure readiness remain environment-owned; WebSocket is not required |

## TODO Autopilot checkpoint — 2026-08-27

| Field | Value |
|---|---|
| Task | Begin automatic TODO completion with post-validation state transitions |
| Owner | Automation Agent and Verification Agent |
| Status | completed-local |
| Dependencies | Git worktree, configured editing agent, repository validation commands |
| Evidence | `tools/todo_autopilot.py`, `tests/test_todo_autopilot.py`, `docs/TODO_AUTOPILOT.md`, `config/todo-autopilot.example.json`; 4 focused tests and Python compilation passed |
| Safety gates | TODO completion occurs only after all validations pass; failed work remains isolated; push and pull-request actions require explicit approval |
| Limitations | Current attached project copy is not a Git worktree; live branch creation, pushes, pull requests, and other external changes require deployment-owned credentials and approval |

The worker advances to the next eligible unchecked item only after a successful validation-and-commit cycle when `--continuous` is enabled. It records bounded run metadata in `.orville_todo_autopilot.json` and refuses concurrent invocations with a repository-local lock.


## Worker Task 2 checkpoint — GUI model catalog and routing controls — 2026-08-27

| Field | Value |
|---|---|
| Task | Add model catalog, local-model import, activation, provider health, and routing controls to the GUI |
| Owner | Worker Task 2 |
| Status | completed-local |
| Implementation | Existing authenticated API model/provider/runtime controls; `docs/GUI_MODEL_CONTROLS.md`; `tests/test_gui_model_controls.py` |
| Coverage | Catalog metadata, local import and activation, provider health, capability/privacy-aware routing, fallback states, licensing, provenance, and GUI safety boundaries |
| Validation | 4 focused tests passed; API/model/provider/routing Python compilation passed; 45 related regression tests passed; precise documentation secret scan passed |
| Git status | Repository has no usable Git metadata or remote in the attached worktree; no branch, commit, or pull request created |
| Limitations | Live model downloads, provider health, runtime activation, identity, credentials, and deployment behavior remain environment-owned |


## Worker Task 1 checkpoint — GUI-to-engine action wiring — 2026-08-27

| Field | Value |
|---|---|
| Task | Connect GUI run creation, pause, resume, cancel, approval, retry, checkpoint, verification, and artifact actions to the engine |
| Owner | Worker Task 1 |
| Status | completed-local |
| Dependencies | GUI-to-engine API contract; authenticated backend bridge; existing run, approval, checkpoint, verification, and artifact routes |
| Evidence | `windows_gui.py`, `docs/GUI_ENGINE_ACTION_WIRING.md`, `tests/test_gui_action_wiring.py`; 11 focused tests across action wiring, backend bridge, and API contract; Python compilation passed |
| Limitations | Current API has no first-class backend pause or verification-mutation endpoint. Pause therefore stops monitor polling only; checkpoint and verification are read projections. Live provider execution and production GUI automation remain untested. |

The shared action builder rejects unknown or incomplete actions, URL-encodes identifiers, selects the existing authenticated routes, and applies streaming execution payloads for execute/resume/retry. The GUI controls now use this mapping rather than duplicating route construction.


## Automation activation checkpoint — 2026-08-27

| Field | Value |
|---|---|
| Task | Automatically continue one-item-at-a-time TODO completion after each stopped task turn |
| Owner | Orchestration Agent / Windows Scheduled Task |
| Status | activated-local |
| Dependencies | `tools/orville_manus_worker.py`, existing recorded task-thread state, `TODO.md`, interactive user session, `MANUS_API_KEY` supplied through process environment |
| Evidence | Enabled `Orville Manus Todo Worker`; one-minute trigger; `--repo` absolute path; `--max-active 3`; `docs/TODO_AUTOPILOT.md`; read-only dry-run outputs |
| Completion gate | The continuation playbook requires claim-before-work, focused code/tests validation, state/changelog synchronization, and `[x]` only after validation evidence agrees. |
| Limitations | No replacement task creation; no live credential call was made during activation; attached repository has no Git metadata, so branch/commit/push/PR delivery is unavailable locally. |

The scheduled task is in `Ready` state and will poll the existing Worker Task 1–10 records. When a recorded thread reaches `stopped`, it resumes that same thread with one next eligible unchecked TODO item. If no task record is available or the process environment lacks the required credential, the worker remains idle or records a blocked state instead of making an unsafe fallback.

## Worker Task 2 checkpoint — Artifact storage and lifecycle controls — 2026-08-27

| Field | Value |
|---|---|
| Task | Add artifact storage, preview, download, versioning, and retention controls |
| Owner | Worker Task 2 |
| Status | completed-local-with-regression-blocker |
| Dependencies | Existing authenticated artifact creation, listing, and download routes |
| Evidence | `orville_core/artifacts.py`, `orville_core/api.py`, `docs/ARTIFACT_STORAGE.md`, `tests/test_artifact_storage.py`; 4 focused tests, Python compilation passed |
| Limitations | Full regression reported 747 passed and 3 unrelated pre-existing connector/shell API failures; retention is plan-only and requires a future approval-gated mutation workflow |

The artifact store now maintains root-bound metadata and digest-based version history in a durable manifest, provides bounded text previews and metadata-only binary previews, excludes its manifest from artifact exposure, and exposes authenticated preview, version-history, download, listing, and non-destructive retention-plan routes.


## Worker Task 1 checkpoint — persistent observability and release evidence — 2026-08-27

| Field | Value |
|---|---|
| Task | Add persistent observability traces, metrics, evaluation fixtures, security regression tests, and release thresholds |
| Owner | Worker Task 1 / Verification Agent |
| Status | completed-local |
| Dependencies | Existing telemetry, trace recorder, production metric aggregation, security gates, regression fixture manifest, and release gate |
| Evidence | `orville_core/release_thresholds.py`, `config/release-thresholds.example.json`, `docs/OBSERVABILITY_EVALUATION_RELEASE_THRESHOLDS.md`, `tests/test_observability_release_evidence.py`; 23 focused tests, Python compilation, and JSON parsing passed |
| Thresholds | Minimum samples 1; maximum error rate 5%; maximum P95 latency 2,000 ms; maximum saturation 90%; maximum security findings 0; minimum business health 0.80; minimum release quality 0.90 |
| Limitations | OpenTelemetry export, provider-backed metric collection, production alerting, live deployment, and rollback execution remain deployment-owned. |

The release-threshold evaluator returns per-check pass/fail evidence and fails closed for missing business-health or release-quality values. It does not contact providers or mutate deployment state.


## Worker Task 2 checkpoint — Standalone release workflows — 2026-08-27

| Field | Value |
|---|---|
| Task | Add packaging, installation, configuration migration, upgrade, rollback, and deployment workflows for standalone use |
| Owner | Worker Task 2 |
| Status | completed-local-with-regression-blocker |
| Dependencies | Existing `pyproject.toml`, `deploy.ps1`, deployment validation, and release gates |
| Evidence | `tools/standalone_release.py`, `tests/test_standalone_release.py`, `docs/STANDALONE_RELEASE_WORKFLOWS.md`; 4 focused tests, Python compilation, plan JSON, and local wheel build passed |
| Limitations | Full suite retains 3 unrelated pre-existing connector/shell API failures; live provider deployment and production rollback remain approval- and infrastructure-owned |

The standalone release utility is plan-only by default, supports explicit execution for package/install/upgrade/migration/rollback/deployment actions, applies forward-only configuration migration, creates versioned backups, refuses rollback into non-empty destinations, and delegates target deployment to the existing preflight and smoke-test workflow.


## Worker Task 1 checkpoint — clean-environment product validation — 2026-08-27

| Field | Value |
|---|---|
| Task | Validate the complete product in a clean environment with configured cloud, local endpoint, and no-provider fallback scenarios |
| Owner | Worker Task 1 / Verification Agent |
| Status | completed-local |
| Evidence | `docs/CLEAN_ENVIRONMENT_VALIDATION.md`, `artifacts/clean-environment-validation-2026-08-27.json`; 55 scenario tests passed, one compatibility warning, and project-check/standalone-release compilation passed |
| Cloud scenario | Synthetic authenticated API smoke and provider-neutral cloud-shaped configuration; no live cloud call |
| Local scenario | Local/Ollama-compatible provider configuration and routing/provider tests with external endpoint variables cleared |
| No-provider scenario | Optional provider variables cleared; authenticated API, safe defaults, deployment target, standalone, and fallback behavior exercised |
| Limitations | Live provider availability, user-managed Ollama process, packaged installer execution, production networking, and multi-replica deployment remain environment-owned. |

The validation used only a temporary clean configuration and synthetic credentials held in process memory. No external provider call or deployment mutation was performed.


## Worker Task 2 checkpoint — Roadmap heading normalization — 2026-08-27

| Field | Value |
|---|---|
| Task | Renumber and normalize duplicated or inconsistent phase headings before the roadmap becomes the source for automated task generation |
| Owner | Worker Task 2 |
| Status | completed-local |
| Dependencies | Existing `TODO.md` roadmap and TODO automation parser/tests |
| Evidence | `TODO.md`, `tests/test_todo_heading_normalization.py`; 3 heading tests and 9 heading/automation regression tests passed, Python compilation passed |
| Limitations | Historical phase-letter backlog sections after the primary roadmap remain intentionally distinct; task semantics and historical evidence text were not rewritten |

The primary phase sequence is now unique and ordered from Phase 0 through Phase 12 using sections 5–17, with Phase 6A represented as section 11A. The Phase 5, Phase 6, Phase 6A, and Phase 7 subsection prefixes were aligned with their normalized parent sections. The roadmap remains parseable by the existing automated TODO-selection tests.


## Worker Task 1 checkpoint — roadmap phase and increment separation — 2026-08-27

| Field | Value |
|---|---|
| Task | Split broad phase labels from implementation increments so provider work and media work are not conflated |
| Owner | Worker Task 1 / Orchestration Agent |
| Status | completed-local |
| Dependencies | Existing normalized Phase 0–12 headings, provider integration slices, environment reliability slices, and media workflow slices |
| Evidence | `config/roadmap-phase-increments.json`, `docs/ROADMAP_PHASE_INCREMENT_MAP.md`, `tests/test_roadmap_phase_increments.py`; 9 focused tests, Python compilation, and JSON parsing passed |
| Mapping | Phase 2.7 = Model Provider Integration; Phase 3.1–3.3 = runtime, connector, and endpoint reliability; Phase 6.2 = image, audio, and video workflows |
| Limitations | This milestone normalizes roadmap ownership and evidence; it does not alter provider, endpoint, or media runtime behavior. |

The mapping keeps broad phase labels descriptive and assigns implementation increments to distinct dependency and acceptance scopes.


## Worker Task 2 checkpoint — Machine-readable TODO identifiers — 2026-08-27

| Field | Value |
|---|---|
| Task | Add a machine-readable task identifier to every backlog item |
| Owner | Worker Task 2 |
| Status | completed-local |
| Dependencies | Existing `TODO.md` checklist grammar and TODO automation parser |
| Evidence | `TODO.md`, `tools/assign_todo_ids.py`, `docs/ROADMAP_TASK_IDENTIFIERS.md`, `tests/test_todo_identifiers.py`; 12 focused identifier/heading/automation tests and Python compilation passed |
| Limitations | Identifiers are derived from current checklist text and occurrence order for duplicate bodies; future task edits should preserve or intentionally regenerate markers |

All 996 actionable checklist records now carry a unique inline `TODO-xxxxxxxxxxxx` marker. Existing status prefixes remain unchanged, valid markers are preserved on regeneration, and TODO automation regression tests pass.


## Worker Task 1 checkpoint — priority backlog metadata completeness — 2026-08-27

| Field | Value |
|---|---|
| Task | Add explicit status, owner, dependency, acceptance test, and artifact reference to every priority item |
| Owner | Worker Task 1 / Orchestration Agent |
| Status | completed-local |
| Dependencies | Existing prioritized backlog schema, TODO wording, task graph, and retained evidence paths |
| Evidence | `config/priority-backlog.json` schema 1.1, `docs/PRIORITIZED_BACKLOG.md`, `tests/test_prioritized_backlog.py`; 6 focused tests, Python compilation, JSON parsing, and artifact-reference existence checks passed |
| Scope | Four existing priority records normalized; no new roadmap task created and no runtime behavior changed |
| Limitations | The broader backlog still contains roadmap items not represented in this legacy priority catalog; this item only makes every existing priority record explicit and internally traceable. |

The catalog now carries planning ownership and reproducible acceptance metadata for each record while retaining dependency and blocker precedence over numeric priority.


## Worker Task 2 checkpoint — Deterministic workflow execution policy — 2026-08-27

| Field | Value |
|---|---|
| Task | Separate deterministic workflow steps from agentic steps and require deterministic implementations for safety-critical, authorization, validation, persistence, and artifact-integrity operations |
| Owner | Worker Task 2 |
| Status | completed-local |
| Dependencies | Existing `WorkflowStep`, `WorkflowStore`, `WorkflowExecutor`, approval, dry-run, and boundary controls |
| Evidence | `orville_core/automation.py`, `tests/test_workflow_execution_policy.py`, `docs/WORKFLOW_EXECUTION_POLICY.md`; 9 focused policy/automation tests and Python compilation passed |
| Limitations | Agentic execution remains handler- and caller-owned; live provider behavior and production authorization infrastructure remain separate release concerns |

Workflow steps now default to deterministic mode. Explicit agentic handlers are isolated from deterministic handlers, unknown modes fail closed, protected safety categories reject agentic implementations before handler invocation, and policy validation occurs before persistence and execution.


## Worker Task 2 checkpoint — Durable operation checkpoints — 2026-08-27

| Field | Value |
|---|---|
| Task | Implement durable checkpoints before and after material agent, tool, model, approval, and artifact operations |
| Owner | Worker Task 2 |
| Status | completed-local |
| Dependencies | Existing `Checkpoint`, `CheckpointStore`, `OrchestrationEngine`, approval, idempotency, and verification contracts |
| Evidence | `orville_core/models.py`, `orville_core/engine.py`, `orville_core/__init__.py`, `tests/test_operation_checkpoints.py`, `docs/OPERATION_CHECKPOINTS.md`; 5 focused tests, 4 automation tests, 18 workflow/acceptance/core regressions, and Python compilation passed |
| Limitations | Operation records prove local before/after boundaries but do not prove remote provider commit; provider idempotency and reconciliation remain required |

Checkpoint schema version 2 now persists secret-safe operation records with deterministic IDs, operation kind, phase, status, attempt, and sequence. Before records are saved before handler invocation; terminal after records are saved on success or failure; approval resolution and parallel task boundaries are covered.


## Worker Task 1 checkpoint — execution-record known limitations — 2026-08-27

| Field | Value |
|---|---|
| Task | Known limitations recorded |
| Owner | Worker Task 1 / Verification Agent |
| Status | completed-local |
| Dependencies | Existing execution-record template, project state, task graph, and reusable validation conventions |
| Evidence | `TODO.md` structured limitation categories and `tests/test_execution_record_template.py`; 2 focused tests and Python compilation passed |
| Categories | Scope, environment/provider, validation, unresolved risks, and follow-up dependencies |
| Boundary | The checklist remains a reusable template placeholder and does not represent a product feature completion. |

Each future execution record now has a consistent place to state what was not tested, what remains environment-owned, and which risks or dependencies remain open.
