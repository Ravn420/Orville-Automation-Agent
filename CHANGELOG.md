# Orville Changelog

## 2026-08-27 — Guarded TODO automation

### Added

- Added `tools/todo_autopilot.py` for one-item-at-a-time autonomous TODO completion with isolated branches, configurable editing commands, validation gates, durable sanitized run state, continuous progression, and fail-closed external GitHub actions.
- Added `tests/test_todo_autopilot.py` covering checkbox integrity, line-movement protection, validation failure behavior, branch isolation, and post-validation commits.
- Added `docs/TODO_AUTOPILOT.md` and `config/todo-autopilot.example.json` with setup, operation, approval, recovery, and architecture guidance.

### Validation

Four focused TODO-automation tests and Python compilation passed. No credentials, network calls, pushes, pull requests, or destructive actions were performed. The attached project copy is not currently a Git worktree, so live branch/PR execution remains deployment-owned.

## 2026-08-27 — Plain-language primary workflows

### Added

- Replaced technical-first home-workspace copy with a plain-language objective prompt and “How Orville works” guidance.
- Added terminology mapping and progressive-disclosure guidance in `docs/PLAIN_LANGUAGE_WORKFLOWS.md`.
- Added `tests/test_plain_language_workflows.py` covering entry copy, workflow stages, technical-term mapping, safety, accessibility, and recovery language.

### Validation

Three focused plain-language workflow unittest cases and Python compilation for the modified GUI and test module passed. No credentials, external services, or destructive actions were used.

## 2026-08-27 — Settings workspace

### Added

- Added `docs/mockups/settings-workspace.html`, a standalone settings workspace covering providers and models, privacy routing, storage paths, resource limits, schedules, notifications, and user preferences.
- Added `docs/SETTINGS_WORKSPACE.md`, defining typed settings, allowlisted local persistence, path and resource bounds, secret boundaries, reset behavior, and approval gates.
- Added `tests/test_settings_workspace.py` with four focused tests for section coverage, bounded controls, local persistence, non-destructive reset, and secret safety.

### Validation

Four focused unittest cases passed, and Python compilation passed for the new test module. No credentials, external services, or destructive actions were used.

## 2026-08-27 — Verification and review view

### Added

- Added a desktop Verification & Review view reachable from workspace navigation.
- Added evidence sections for acceptance criteria, test results, source evidence, visual checks, defects, residual risks, and approval state.
- Added bounded 4,000-character section rendering, URL-encoded run IDs, safe unavailable-run messaging, and `docs/VERIFICATION_REVIEW_SPECIFICATION.md`.
- Added `tests/test_verification_review.py` covering section and persisted-context coverage.

### Validation

Three focused verification-review unittest cases and Python compilation for the modified GUI and test module passed. No credentials, external services, or destructive actions were used. Evidence quality and approval authorization remain review responsibilities.

## 2026-08-27 — Artifact browser prototype

### Added

- Added `docs/mockups/artifact-browser.html`, a standalone artifact library with search and type/status filters, safe local preview, metadata, download, export, version comparison, and non-destructive revision actions.
- Added `docs/ARTIFACT_BROWSER.md`, defining artifact states, source/export relationships, preview and retrieval boundaries, versioning, organization, approval gates, and validation requirements.
- Added `tests/test_artifact_browser.py` with four focused tests for supported artifact types, filters, preview metadata, non-destructive actions, approval boundaries, and secret safety.

### Validation

Four focused unittest cases passed, and Python compilation passed for the new test module. No credentials, external services, or destructive actions were used.

## 2026-08-27 — Execution monitor

### Added

- Added a desktop Execution Monitor reachable from Active tasks and Recent activity.
- Added persisted run/event polling for task progress, agent activity, tool event classifications, elapsed time, and bounded event history.
- Added Refresh, Pause monitor, Resume waiting task, Retry run, and Cancel run controls with secret-safe unavailable-run handling.
- Added `docs/EXECUTION_MONITOR_SPECIFICATION.md` and `tests/test_execution_monitor.py`.

### Validation

Three focused execution-monitor unittest cases and Python compilation for the modified GUI and test module passed. No credentials, external services, or destructive actions were used. Backend hard pause and cooperative handler interruption remain future engine work.

## 2026-08-27 — Capability-aware generation workspace

### Added

- Added `docs/mockups/generation-workspace.html`, a standalone generation workspace with capability selection for text, code, image, audio, video, vision, embedding, and other modalities; compatible-model filtering; modality-specific inputs; local draft persistence; redacted request review; and explicit execution gating.
- Added `docs/GENERATION_WORKSPACE.md`, defining modality inputs and outputs, capability compatibility, lifecycle states, local-file custody, artifact evidence, and external-side-effect boundaries.
- Added `tests/test_generation_workspace.py` with four focused tests for modality coverage, model compatibility, redacted review, explicit execution, and local-only safety.

### Validation

Four focused unittest cases passed, and Python compilation passed for the new test module. No credentials, external services, or destructive actions were used.

## 2026-08-27 — Unified model manager

### Added

- Unified provider setup and imported local-model inventory under the `Model Manager` desktop window.
- Added direct actions for cloud/endpoint/Ollama provider setup and local model import alongside refresh, validation, activation, deactivation, and registration removal.
- Added `docs/MODEL_MANAGER_SPECIFICATION.md` and `tests/test_model_manager.py` covering supported sources, routes, secret-safe wording, and file-retention behavior.

### Validation

Three focused model-manager unittest cases and Python compilation for the modified GUI and test module passed. No credentials, external services, or destructive actions were used. Runtime compatibility and provider health remain API-owned checks.

## 2026-08-27 — Secret-safe model configuration flow

### Added

- Added `docs/mockups/model-configuration.html`, a standalone configuration flow with provider presets, endpoint and model validation, masked credential input, redacted review, credential clearing, explicit health-check review, and approval messaging.
- Added `docs/MODEL_CONFIGURATION_FLOW.md`, defining configuration states, endpoint and credential boundaries, safe persistence, redacted health checks, and acceptance criteria.
- Added `tests/test_model_configuration_flow.py` with four focused tests for provider presets, required fields, endpoint validation, redacted review, credential safety, and approval boundaries.

### Validation

Four focused unittest cases passed, and Python compilation passed for the new test module. No credentials, external services, or destructive actions were used.

## 2026-08-27 — Operational dashboard

### Added

- Added a responsive six-card dashboard to `windows_gui.py` for active tasks, recent runs, model availability, system health, failures, and generated artifacts.
- Added asynchronous refresh through existing read-only API routes with bounded safe degraded values and no raw payload or exception display.
- Added `docs/DASHBOARD_SPECIFICATION.md` and `tests/test_dashboard.py` documenting and testing card coverage, supported payload shapes, and UI-safe fallback behavior.

### Validation

Three focused dashboard unittest cases and Python compilation for the modified GUI and test module passed. No credentials, external services, or destructive actions were used. Per-provider live health, web/mobile parity, and rendered visual regression remain future work.

## 2026-08-27 — Task composer prototype

### Added

- Added `docs/mockups/task-composer.html`, a standalone task composer for software requirements, deliverables, local file references, context, constraints, target environment, model preference, and acceptance criteria.
- Added local draft persistence, safe review gating, reset behavior, and a structured draft payload preview without external requests or credential capture.
- Added `tests/test_task_composer.py` with four focused tests for composer fields, attachments, acceptance criteria, review gating, persistence, and safety boundaries.

### Validation

Four focused unittest cases passed, and Python compilation passed for the new test module. No credentials, external services, or destructive actions were used.

## 2026-08-27 — Degraded GUI availability

### Added

- Added stable dependency-state classification and safe recovery actions in `windows_gui.py` for unavailable cloud providers, local endpoints, connectors, and model runtimes.
- Added `docs/GUI_DEGRADED_AVAILABILITY.md`, defining preserved local workflows, privacy-safe fallback, bounded retry, idempotency, safe diagnostics, and deployment-owned limits.
- Added `tests/test_gui_degraded_availability.py` with three focused tests covering dependency mapping, recovery actions, and secret-safe behavior.

### Validation

Three focused unittest cases passed, Python compilation passed for the GUI and test module, and structural checks confirmed all four dependency categories, preserved-work assertions, bounded retry, idempotency, and safe fallback wording.

## 2026-08-27 — Localization-ready text boundary

### Added

- Added `orville_core/localization.py` with stable-key text resolution, default-locale fallback, safe parameter interpolation, and missing-key behavior.
- Added `config/locales/en-US.json` with non-secret workflow, status, action, notification, and error copy.
- Added `tests/test_localization.py` with three focused tests for resource loading, locale fallback, safe interpolation, missing keys, and secret-safe resources.

### Validation

Three focused unittest cases passed and Python compilation passed. Additional locale translation, full UI migration, and translator review remain follow-up work.

## 2026-08-27 — Destructive-action confirmation contract

### Added

- Added `docs/DESTRUCTIVE_ACTION_CONFIRMATIONS.md`, defining consequence previews, exact target/scope confirmation, reversible alternatives, approval boundaries, single-use expiry, stale-preview rejection, accessible dialogs, safe diagnostics, and recovery actions for destructive or high-impact operations.
- Added `tests/test_destructive_action_confirmations.py` with three focused tests covering action classes, fail-closed confirmation states, accessibility, and secret-safe diagnostics.

### Validation

Three focused unittest cases passed, Python compilation passed, and structural checks confirmed all destructive-action classes, confirmation states, recovery rules, accessibility requirements, and a single references section. Live provider authorization and production destructive-action exercises remain outside the local contract.

## 2026-08-27 — Accessibility acceptance contract

### Added

- Added `docs/ACCESSIBILITY_ACCEPTANCE_CRITERIA.md`, defining keyboard operation, focus visibility and restoration, semantic controls, screen-reader announcements, contrast thresholds, reduced-motion behavior, zoom/reflow, alternatives, touch targets, and accessible error feedback across critical workflows.
- Added `tests/test_accessibility_acceptance.py` with three focused tests covering the criteria matrix, workflow review states, and secret-safe error boundaries.

### Validation

Three focused unittest cases passed, Python compilation passed, and structural checks confirmed all ten accessibility criteria, seven critical workflow review paths, one references section, and secret-safe error wording. Live assistive-technology, browser, mobile, and production visual testing remain follow-up gates.

## 2026-08-27 — Safe defaults and advanced settings

### Added

- Added `config/settings-defaults.example.json` with non-secret local-first, manual, bounded, and system-aware defaults for providers, models, privacy routing, storage paths, resource limits, schedules, notifications, preferences, and telemetry.
- Added `docs/SAFE_DEFAULTS_AND_ADVANCED_SETTINGS.md`, defining default explanations, optional advanced overrides, precedence, fail-closed validation, non-destructive reset, and approval boundaries.
- Added `tests/test_safe_defaults.py` with three focused tests covering all settings areas, optional advanced values, bounds, and secret safety.

### Validation

Three focused unittest cases passed, JSON parsing passed, Python compilation passed, and structural checks confirmed all requested settings areas and security boundaries. Production provisioning, live schedules, external notifications, and full client migration remain outside the local contract.

## 2026-08-27 — Imported-model workflow contract

### Added

- Added `docs/IMPORTED_MODEL_WORKFLOW.md`, defining local file/folder selection, storage modes, metadata scanning, compatibility validation, activation approval, stable diagnostics, lifecycle states, and safe deactivation/removal.
- Added `tests/test_imported_model_workflow.py` with three focused tests covering workflow stages, lifecycle/diagnostic states, and security/acceptance boundaries.

### Validation

Three focused unittest cases passed, Python compilation passed, and structural checks confirmed all workflow stages, diagnostic and lifecycle coverage, safety boundaries, and a single references section. Live GPU/runtime provisioning, provider upload, and full GUI integration remain outside the local contract.

## 2026-08-27 — Task-plan view contract

### Added

- Added `docs/TASK_PLAN_VIEW.md`, defining the task-plan projection model, graph/dependency presentation, agent assignments, status semantics, blocker and retry details, verification gates, safe interactions, accessibility fallback, and bounded rendering requirements.
- Added `tests/test_task_plan_view.py` with three focused tests covering graph fields, statuses/interactions, accessibility/security boundaries, and secret-safe wording.

### Validation

Three focused unittest cases passed, Python compilation passed, and structural checks confirmed required graph fields, status coverage, interaction sections, accessible fallback, and a single references section. The existing GUI is not claimed as fully integrated.

## 2026-08-27 — Reusable components and interaction patterns

### Added

- Added `docs/REUSABLE_COMPONENTS_INTERACTIONS.md`, defining component families, state contracts, deterministic interaction patterns, composition rules, accessibility/responsive requirements, and review evidence.
- Added `tests/test_reusable_components_interactions.py` with three focused tests covering component families, state and interaction behavior, accessibility/security boundaries, and secret-safe wording.

### Validation

Three focused unittest cases passed, Python compilation passed, and structural checks confirmed the required component families, interaction sections, and single references section. Existing screens are not claimed as fully migrated.

## 2026-08-27 — Theme preferences and status indicators

### Added

- Added persisted light/dark theme behavior to `docs/mockups/orville-control-center.html`, including semantic dark tokens, an accessible toggle, local preference validation, and reduced-motion support.
- Added `docs/THEME_AND_STATUS_BEHAVIOR.md`, defining allowed preference values, semantic status states, contrast and non-color requirements, and verification gates.
- Added `tests/test_theme_and_status_behavior.py` with four focused tests for theme persistence, token coverage, status semantics, and secret safety.

### Validation

Four focused unittest cases passed, and Python compilation passed for the new test module. No credentials, external services, or destructive actions were used.

## 2026-08-27 — Polished visual style profile

### Added

- Added `config/visual-style.example.json` with professional/modern/clear style qualities, composition and hierarchy constraints, performance budgets, usability safeguards, and review gates.
- Added `docs/VISUAL_STYLE_GUIDE.md` covering visual language, content density, status semantics, responsive behavior, accessibility, performance, security, and visual regression review.
- Added `tests/test_visual_style_guide.py` covering profile safeguards, required style domains, component review boundaries, and security/performance requirements.

### Validation

Three focused visual-style unittest cases passed. JSON parsing and Python compilation passed. No credentials, external services, or destructive actions were used. Existing clients are not claimed as fully migrated; rendered regression, live accessibility review, and performance telemetry remain subsequent work.

## 2026-08-27 — GUI wireframes and high-fidelity mockup

### Added

- Added `docs/GUI_WIREFRAMES.md`, defining low-fidelity layouts for the global shell, home/readiness, objective intake, run/verification, artifact, and provider surfaces, including responsive and state behavior.
- Added `docs/mockups/orville-control-center.html`, a standalone high-fidelity control-center mockup aligned with the existing design tokens, semantic structure, responsive thresholds, focus behavior, reduced motion, and touch-target rules.
- Added `tests/test_gui_wireframes_mockup.py` with four focused tests for surface coverage, semantic HTML, responsive/design-system behavior, visual-review gates, and secret safety.

### Validation

Four focused unittest cases passed, and Python compilation passed for the new test module. No credentials, external services, or destructive actions were used.

## 2026-08-27 — Media visual verification and quality checks

### Added

- Added `docs/MEDIA_VISUAL_VERIFICATION.md` with complete-artifact inspection, image/audio/video/document/animation/mixed quality checks, severity-based disposition, accessibility and provenance evidence, and second-review requirements.
- Added `tests/test_media_visual_verification.py` with three focused contract tests covering review records, artifact coverage, fail-closed defects, and secret-safe wording.

### Validation

Three focused unittest cases passed, Python compilation passed, and structural checks confirmed one references section plus all six artifact classes. Live media-provider decoding, publication playback, and external rights clearance remain outside the local contract.

## 2026-08-27 — Cohesive visual design system

### Added

- Added `config/design-system.example.json` with light/dark semantic tokens for typography, color, spacing, elevation, icons, controls, motion, and responsive breakpoints.
- Added `docs/VISUAL_DESIGN_SYSTEM.md` covering reusable states and interaction patterns for controls, forms, tables, cards, notifications, dialogs, empty states, status indicators, and navigation, with accessibility, security, theme, and responsive rules.
- Added `tests/test_visual_design_system.py` covering token completeness, theme roles, touch-target minimums, component/state coverage, and security/responsive boundaries.

### Validation

Three focused visual-design-system unittest cases passed. JSON parsing and Python compilation passed. No credentials, external services, or destructive actions were used. Existing clients are not claimed as fully migrated; wireframes, mockups, and visual regression evidence remain subsequent work.

## 2026-08-27 — GUI information architecture and user journeys

### Added

- Added `docs/GUI_INFORMATION_ARCHITECTURE.md`, defining target users, primary workflows, navigation, object hierarchy, user journeys, acceptance criteria, and safe interaction boundaries.
- Added `tests/test_gui_information_architecture.py` with four focused tests for user roles, workflow coverage, navigation and information architecture, journey acceptance, and safety boundaries.

### Validation

Four focused unittest cases passed, and Python compilation passed for the new test module. No credentials, external services, or destructive actions were used.

## 2026-08-27 — Document and presentation verification

### Added

- Added `orville_core/document_verification.py` with deterministic Markdown, PDF, and PPTX checks for format, page/slide counts, numeric citations, links, charts, images, alt text, and basic legibility.
- Exported the verification contracts through `orville_core/__init__.py` and documented evidence procedures and rendered-review limitations in `docs/DOCUMENT_VERIFICATION.md`.
- Added 5 focused tests covering successful and failing evidence checks, count mismatches, legibility findings, unsupported formats, missing files, and documentation coverage.

### Validation

Five focused document-verification unittest cases passed. Python compilation and public-import verification passed. No credentials, external services, or destructive actions were used. Binary rendering, remote-link reachability, citation quality, OCR, font-size inspection, and human accessibility review remain separate verification responsibilities.

## 2026-08-27 — Editable source preservation

### Added

- Added `docs/EDITABLE_SOURCE_PRESERVATION.md`, defining source/export manifests, immutable source versions, derivative relationships, no-source fallback, deterministic naming, storage boundaries, fidelity checks, and handoff requirements.
- Added `tests/test_editable_source_preservation.py` with four focused tests for manifest fields, source/export relationships, fallback behavior, storage safety, and fail-closed validation gates.

### Validation

Four focused unittest cases passed, and Python compilation passed for the new test module. No credentials, external services, or destructive actions were used.

## 2026-08-27 — Presentation procedures

### Added

- Added `docs/PRESENTATION_PROCEDURES.md`, defining presentation briefs, narrative planning, evidence and content validation, design-system consistency, accessibility review, export checks, delivery manifests, and approval boundaries.
- Added `tests/test_presentation_procedures.py` with four focused tests for planning fields, claim integrity, design/accessibility checks, export coverage, and secret safety.

### Validation

Four focused unittest cases passed, and Python compilation passed for the new test module. No credentials, external services, or destructive actions were used.

## 2026-08-27 — Media validation checks

### Added

- Added `orville_core/media_validation.py` with deterministic modality policies and stable results for format, size, resolution, duration, alt text, transcript/captions, license, rights holder, and source checks.
- Exported the media validation contracts through `orville_core/__init__.py` and documented default formats, evidence, thresholds, and limitations in `docs/MEDIA_VALIDATION_CHECKS.md`.
- Added focused tests covering all required validation domains, missing files, invalid modalities, source-size limits, and documentation coverage.

### Validation

Five focused media-validation unittest cases passed. Python compilation and public package-import verification passed. No credentials, external services, or destructive actions were used. Codec inspection, transcription, caption-quality review, remote rights validation, and legal clearance remain outside the local checker.

## 2026-08-27 — Document templates

### Added

- Added `docs/DOCUMENT_TEMPLATES.md`, defining shared metadata and Markdown templates for reports, specifications, runbooks, and research outputs, including evidence, validation, safety, approval, and lifecycle rules.
- Added `tests/test_document_templates.py` with four focused tests for template coverage, metadata, operational boundaries, review requirements, deterministic naming, and secret safety.

### Validation

Four focused unittest cases passed, and Python compilation passed for the new test module. No credentials, external services, or destructive actions were used.

## 2026-08-27 — Media provenance and transformation history

### Added

- Added `orville_core/media_provenance.py` with checksum-addressed source/generated asset retention, redacted prompt and metadata persistence, ordered transformation lineage, size bounds, filename sanitization, and repository-root containment.
- Exported the provenance contracts through `orville_core/__init__.py` and documented storage/workflow behavior in `docs/MEDIA_PROVENANCE.md`.
- Added `tests/test_media_provenance.py` covering asset/output retention, lineage persistence, prompt and metadata redaction, source immutability on size rejection, sanitization, and containment.

### Validation

Three focused media-provenance unittest cases passed. Python compilation and public package-import verification passed. No credentials, external services, or destructive actions were used. Multi-process locking, remote object storage, signing, and perceptual hashes remain future hardening or deployment work.

## 2026-08-27 — Automated build, test, and preview procedures

### Added

- Added `tools/project_checks.py` with reproducible `build`, `test`, `preview`, and `all` modes. Build compiles sources and creates a disposable wheel; test runs the configured pytest suite; preview runs credential-free Signal Room checks and optionally the existing loopback API smoke workflow.
- Added `docs/BUILD_TEST_PREVIEW.md` documenting prerequisites, commands, expected outputs, local-only API constraints, failure handling, and disposable-artifact cleanup.
- Added `tests/test_project_checks.py` with four focused tests for command coverage, reproducible build/test wiring, credential-free preview defaults, and optional API-smoke safety boundaries.

### Validation

Focused automation tests passed (4), Python compilation passed, the credential-free preview procedure passed with the repository's existing contrast warnings, and the build procedure passed with a wheel produced under `tmp/project-check-wheels/`. The full test procedure was invoked and exposed a pre-existing unrelated failure in `orville_core/api.py` (`Request` keyword incompatibility followed by an undefined `HTTPError`); failure evidence is retained at `tmp/project_checks_failure.txt`.

## 2026-08-27 — Operation-aware secret-safe API errors

### Added

- Added centralized FastAPI handlers in `orville_core/api.py` for HTTP and request-validation failures. Responses now identify the failed operation, provide stable error codes and retryability, preserve a safe compatibility `detail` field, and never echo request payloads, dynamic path values, raw exceptions, or credentials.
- Added `tests/test_api_error_messages.py` covering invalid authentication, invalid payloads containing a synthetic API key, and missing resources containing a sensitive path value.

### Validation

Focused API error tests passed: 3. Python compilation passed for the modified API module and focused test module. The existing HTTP-client deprecation warning remains non-blocking. No live credentials, external services, or destructive actions were used.

## 2026-08-27 — Asset lifecycle procedures

### Added

- Added `docs/ASSET_LIFECYCLE_PROCEDURES.md`, defining asset briefs, generation and editing custody, licensing/provenance states, naming, storage classes, manifests, approvals, and validation records.
- Added `tests/test_asset_lifecycle_procedures.py` with four focused tests for required metadata, source preservation, fail-closed licensing, naming, storage, and secret boundaries.

### Validation

Four focused unittest cases passed, and Python compilation passed for the new test module. No credentials, external services, or destructive actions were used.

## 2026-08-27 — Web and mobile acceptance criteria

### Added

- Defined `docs/WEB_MOBILE_ACCEPTANCE_CRITERIA.md` with target viewport classes, responsive reflow and touch requirements, WCAG 2.2 Level AA accessibility criteria, keyboard and assistive-technology checks, frontend security boundaries, secret-safe error handling, and measurable performance budgets.
- Added focused documentation tests in `tests/test_web_mobile_acceptance_criteria.py` covering required quality domains, target widths, measurable thresholds, unique acceptance IDs, and explicit secret exclusion.

### Validation

Three focused unittest cases passed and Python compilation passed. No credentials, external services, or destructive actions were used. Live device testing, production headers, assistive-technology sessions, telemetry, and network measurements remain release-evidence responsibilities.

## 2026-08-27 — Deployment and rollback instructions

### Added

- Expanded `docs/DELIVERY_RUNBOOK.md` with the supported Docker Compose promotion sequence, preflight and backup gates, effective configuration review, authenticated health verification, approval-gated rollback, volume-preserving recovery, database restore evidence, and non-Compose fallback instructions.
- Documented secret-injection boundaries, one-replica SQLite constraints, retained release evidence, diagnostic preservation, and explicit deployment-owned limitations.

### Validation

Focused documentation assertions passed for deployment, rollback, Compose promotion, health checks, backup instructions, volume-preserving recovery, secret boundaries, and evidence retention. No live deployment, provider-side rollback, credentials, or destructive actions were used.

## 2026-08-27 — Project initialization rules

### Added

- Added `docs/PROJECT_INITIALIZATION_RULES.md`, defining deterministic initialization inputs, fail-closed classification, common stages, and profile-specific rules for static sites, full-stack web applications, and mobile applications.
- Added `tests/test_project_initialization_rules.py` to verify profile coverage, required inputs, security boundaries, and build/test/preview acceptance requirements.

### Validation

Four focused unittest cases passed, and Python compilation passed for the new test module. No credentials, external services, or destructive actions were used.

## 2026-08-27 — Frontend-backend contracts and environment configuration

### Added

- Defined the standalone frontend-backend contract in `docs/FRONTEND_BACKEND_CONTRACTS.md`, including the `/api/v1` route surface, stable response and error envelopes, operation identifiers, safe error-message rules, runtime configuration, and environment-specific ownership boundaries.
- Added the non-secret `config/frontend-backend.example.json` fixture and focused coverage in `tests/test_frontend_backend_contract.py` for configuration parsing, route/environment documentation, bounded operation names, and synthetic secret-redaction expectations.

### Validation

Three focused unittest cases passed, JSON parsing passed, and Python compilation passed. No live credentials, external services, or destructive actions were used. Production TLS, identity, origin allowlisting, rate limiting, secret injection, and frontend hosting remain deployment-owned.

## 2026-08-27 — Task status endpoint and worker-state reset

### Fixed

- Replaced the non-working `task.listMessages` status poll with the documented `GET /v2/task.detail?task_id=...` request and `task.status` parsing.
- Migrated and then reset legacy persisted active-task state after retaining a backup at `artifacts/orville_manus_worker_state_backup_2026-08-27.json`.

### Validation

Focused worker tests passed: 5. A live worker cycle created three fresh tasks and successfully received `running` status responses from task.detail for all three. No credentials were printed or persisted.

## 2026-08-27 — Immediate worker startup fill

### Changed

- The roadmap worker now fills available task slots immediately at startup before polling existing task statuses.
- Legacy single-task state is migrated into the bounded active-task list to prevent duplicate startup selection.

### Validation

Focused worker tests passed: 4. Python compilation passed. The startup-first behavior was verified with a mocked status endpoint failure; task creation still occurred before status polling.

## 2026-08-27 — Worker repository-path launch fix

### Fixed

- Added an explicit `--repo` CLI option and `ORVILLE_REPO` fallback so launches from protected working directories such as `C:\\Windows\\System32` do not attempt to create worker state in System32.
- Updated the Windows installer to pass the repository root explicitly and documented both root-relative and absolute-path invocations.

### Validation

A credential-free dry run succeeded when launched from `C:\\Windows\\System32` with the attached Orville repository supplied through `--repo`. Focused worker tests passed (3), Python compilation passed, and the PowerShell installer parser reported no errors.

## 2026-08-27 — Three-slot persistent roadmap worker

### Added

- Extended `tools/orville_manus_worker.py` from one active Manus task to a persisted maximum of three active tasks, with reserved TODO entries, refill after stopped-task detection, and bounded state recovery.
- Updated the Windows scheduled-task installer and added `docs/ORVILLE_MANUS_WORKER.md` with setup, recovery, security, validation, and limitation guidance.
- Added focused tests for three-slot refill behavior, duplicate avoidance, persisted-state capping, and credential-free dry-run behavior.

### Validation

Focused worker tests passed: 3. Python compilation passed for the worker and focused tests. Tests used synthetic environment values and mocked API boundaries; no external credentials or network calls were used.

## 2026-08-27 — Pre-execution provider and privacy context

### Added

- Added provider, model, endpoint-family, privacy-mode, and remote-location fields to the redacted cloud admission summary.
- Added regression coverage proving the summary is available before remote execution and contains no provider credential.

### Validation

Focused onboarding/cloud-relay API tests passed: 7. Python compilation passed. Signal Room static checks passed with the existing contrast warning. No credentials or external account action was used.


## 2026-08-27 — Blackbox connection lifecycle actions

### Added

- Added onboarding metadata for connection testing, provider/model selection, credential replacement, disconnect, and credential deletion.
- Added a local credential-free connection-test API route and a credential-deletion route that preserves managed access and local mode.
- Added focused tests for lifecycle action metadata, redaction, safe testing, deletion, and state preservation.

### Validation

Focused onboarding/cloud-relay API tests passed: 7. Python compilation passed. Signal Room static checks passed with the existing contrast warning. No credentials or external account action was used.


## 2026-08-27 — Documented Blackbox API-key connection fallback

### Added

- Added explicit `Connect with Blackbox API key` onboarding metadata and the official Blackbox API authentication documentation link.
- Updated the accessible Signal Room fallback to present API-key connection as optional and separate from managed cloud access.
- Preserved the no-OAuth claim boundary because official third-party OAuth/device authorization remains unconfirmed.

### Validation

Focused onboarding and cloud-relay API tests passed: 6. Python compilation passed. Signal Room static checks and required-link checks passed with the existing contrast warning. No credentials, external authorization, or account action was used.


## 2026-08-27 — Blackbox capability negotiation

### Added

- Added `BlackboxCapabilityNegotiator`, `BlackboxCapabilityResult`, and `BlackboxCapabilityError`.
- Negotiation now exposes only explicitly advertised capabilities permitted by the selected standard or enterprise endpoint family and account plan.
- Added authenticated credential-free `/api/v1/cloud/blackbox/capabilities` presentation with actionable unavailable reasons and no credential fields.

### Validation

Focused capability tests pass: 34. Full regression suite passes 341 tests with one existing HTTP-client deprecation warning. No live Blackbox API call or external credential was used.

## 2026-08-27 — Managed-first Blackbox cloud onboarding

### Added

- Added `initial_cloud_onboarding()` and authenticated `GET /api/v1/cloud/blackbox/onboarding`.
- The initial experience now presents managed cloud access as the default and explicitly keeps Blackbox account connection optional; no API key or sign-in is required to start.
- Added accessible no-script Signal Room guidance for managed access, optional connection, service limits, privacy terms, and availability.

### Validation

Focused onboarding/cloud tests pass: 13. Full regression suite passes 347 tests with one existing HTTP-client deprecation warning. Signal Room static audit passes with the existing contrast warning reported. No credentials or external side effects were used.

## 2026-08-27 — Blackbox model discovery

### Added

- Added `BlackboxModelDiscovery` and `/api/v1/cloud/blackbox/models` for credential-free model-catalog normalization.
- Added bounded identifier filtering, deduplication, active-model selection, and deterministic manual-model fallback for unavailable or empty discovery responses.

### Validation

Focused discovery and capability tests pass: 11. Full regression suite passes 345 tests with one existing HTTP-client deprecation warning. No external credentials or network calls were used.

## 2026-08-27 — Blackbox API-key contract validation

### Added

- Added `BlackboxApiKeyContract` for credential-free validation of documented public and enterprise endpoint families, HTTPS requirements, model identifiers, timeout/capability metadata, and safe error envelopes.
- Applied local validation before the Blackbox API-key connection record is stored and exported the contract through the public package API.
- Added tests for endpoint rejection, endpoint-family selection, model validation, capability metadata, and redacted error normalization.

### Validation

Focused Blackbox contract, relay, and API tests pass: 27. Full regression suite passes 334 tests with one existing HTTP-client deprecation warning. No Blackbox API key, live API call, or external side effect was used.

## 2026-08-27 — Deterministic Blackbox local fallback

### Added

- Added `BlackboxFallbackPolicy` and `FallbackDecision` for disconnected, unavailable, rate-limited, expired, invalid, disabled, and unconfigured managed relay states.
- The policy selects the first explicitly configured local provider without exposing credentials and returns an actionable remediation reason when no local provider exists.
- Extended `/api/v1/cloud/blackbox/status` with redacted fallback status and exported the policy through the public package API.

### Validation

Focused Blackbox relay and API tests pass: 21. Full regression suite passes 328 tests with one existing HTTP-client deprecation warning. No Blackbox credentials, external provider calls, or external side effects were used.

## 2026-08-27 — Blackbox support-confirmation assessment

### Blocked

- Reviewed the first actionable Blackbox TODO item requiring explicit developer-support confirmation for third-party OAuth, device authorization, CLI token interoperability, scopes, redirects, refresh tokens, rate limits, and redistribution.
- Marked the item `blocked-external` because public documentation is insufficient and obtaining confirmation would require an external support request. No post, credential submission, or provider-side action was performed.

## 2026-08-27 — Connector mutation governance

### Added

- Added `ConnectorMutationPolicy`, `ConnectorMutationRequest`, and `ConnectorGovernanceError`.
- Connector defaults, manual/OAuth connections, refresh, revoke, and disconnect now require a concrete project requirement, explicit approval, and a non-secret approval reference.
- Updated synthetic connector API fixtures and added governance rejection/acceptance tests.

### Validation

Focused connector governance and connection tests pass: 7. Full regression suite passes 324 tests with one existing HTTP-client deprecation warning. Python compilation passes for `orville_core`, `tests`, and `tools`.

## 2026-08-27 — Safe connector capability audit

### Added

- Added `ConnectorCapabilityAudit` and `CapabilityCallResult` for concrete-project connector requirements.
- The audit selects only enabled `read` operations, defaults to no external invocation, and rejects connectors without a harmless read-only capability.
- Added fixture-based invocation and sensitive-operation rejection tests; no external capability call was made because `PROJECT.md` declares no required connector IDs.

### Validation

Focused connector capability tests pass: 2. Full regression suite passes 321 tests with one existing HTTP-client deprecation warning. Python compilation passes for `orville_core`, `tests`, and `tools`.

## 2026-08-27 — Began M14.8 automated canary and rollback completion

### Progress

- Marked M14.8, the next eligible milestone, `in-progress-local`.
- Ran the existing 18-scenario synthetic canary fault-injection baseline successfully and retained its evidence at `artifacts/m13_12_fault_injection.json`.
- Focused canary and policy tests passed: 7 tests.

### Boundary

M14.8 is not yet complete. Dedicated non-production drill evidence and acceptance coverage for restart, duplicate events, partial failure, and rollback-failure recovery remain to be completed. No production deployment or external credential was used.

## 2026-08-27 — Automatic milestone progression with bounded concurrency

### Added

- Configured the primary Orville runtime to run up to three independent tasks concurrently within the active TaskGraph milestone.
- Preserved immediate dependency-driven advancement after verified task completion, together with approval, verification, cancellation, and blocker gates.
- Added regression coverage proving the default runtime does not exceed three simultaneous tasks.

### Validation

Focused orchestration tests: 16 passed. Full regression suite: 319 passed with one pre-existing HTTP-client deprecation warning. Python compilation passed for the changed modules and tests.

## 2026-08-27 — M14.7 production metrics and health-source checkpoint

### Added

- Added `orville_core/production_metrics.py` with explicit tenant, cohort, and release scoping for request/error rate, latency, saturation, business health, security findings, and release quality metrics.
- Added freshness cutoffs, sample validation, cross-scope rejection, bounded in-memory health-source support, and normalization into the existing canary `HealthObservation` contract.
- Added focused tests in `tests/test_production_metrics.py` and documentation in `docs/M14_PRODUCTION_METRICS.md`.

### Boundary

The local implementation does not claim a production monitoring backend, alerting/SLO policy, metric-completeness checks, or business-health source. Those remain deployment-owned.


## 2026-08-27 — Connector transfers, execution history, and Signal Room checks

### Added

- Added `ConnectorTransferRequest` and `FileTransferPolicy.prepare()` for explicit upload/download intent validation, approved-root containment, MIME and size enforcement, and staged download handling.
- Extended `ScheduleExecution` persistence with bounded JSON outputs, artifacts, cost units/currency, connector actions, and approval records; the authenticated schedule history API now returns these fields.
- Added credential-free connector transfer tests, execution-history persistence/API tests, and `tools/signal_room_checks.py` for local HTML smoke, document-language, focus, reduced-motion, and contrast auditing.
- Added an accessible Signal Room HTML fallback with a semantic execution-history section for no-script environments.

### Validation

Focused connector/history/UI tests pass: 10 tests. The full regression suite passes 312 tests with one existing HTTP-client deprecation warning. Python compilation passes for `orville_core`, `tests`, and `tools`.

### Known limitation

The bundled stylesheet contains one existing normal-text contrast warning. The local audit reports it without treating the bundled palette as silently compliant; full runtime accessibility and visual checks remain broader than this static audit.

## 2026-08-27 — M14.6 reviewed deployment-provider checkpoint

### Added

- Added `orville_core/reviewed_deployment_provider.py` as a provider-neutral safety wrapper for deploy, traffic split, pause, rollback, and status operations.
- Added dry-run defaults, bounded provider calls, deterministic idempotency, release and traffic validation, protected credential-reference checks, and redacted status output.
- Added focused tests in `tests/test_reviewed_deployment_provider.py` and documentation in `docs/M14_REVIEWED_DEPLOYMENT_PROVIDER.md`.

### Validation and boundary

Focused M14.6 tests pass: 5. The local adapter does not contact a real provider by default. Provider-specific backend implementation, workload identity, provider-side cancellation/idempotency verification, and non-production rollback evidence remain deployment-owned.


## 2026-08-27 — M14.5 protected secret management checkpoint

### Added

- Added `orville_core/protected_secrets.py` for runtime-only resolution through an injected resolver, metadata-only rotation and revocation, fail-closed behavior, redacted metadata export, and explicit runtime scrubbing.
- Added focused tests in `tests/test_protected_secrets.py` and documented the enterprise integration boundary in `docs/M14_PROTECTED_SECRET_MANAGEMENT.md`.

### Validation and boundary

No secret values are persisted in the protected-secret SQLite table or emitted by the metadata export. Enterprise secret-manager provisioning, workload identity, scheduled rotation, and production access-review evidence remain deployment-owned. Full regression: **300 passed, 1 pre-existing Starlette/httpx deprecation warning**.


## 2026-08-27 — M14.4 enterprise identity and authorization

### Added

- Added tenant-scoped `IdentityClaims` and `SQLiteEnterpriseAuthorizationStore` with bounded claim lifetimes, active membership, narrow action scopes, explicit approval references for sensitive actions, revocation, fail-closed unknown-action handling, and sanitized audit records.
- Added `docs/M14_ENTERPRISE_IDENTITY.md` and two focused regression tests.

### Validation

Python compilation passed and the full regression suite passed 297 tests with one existing Starlette/httpx deprecation warning. Live OIDC/SAML gateway integration, MFA, issuer/audience verification, and production revocation propagation remain pending.

## 2026-08-27 — M14.2 production trust-root ceremony workflow

### Added

- Added `orville_core.trust_root_ceremony.ProductionTrustRootCeremony` for approval-gated bootstrap, rotation, and revocation evidence.
- Added canonical out-of-band SHA-256 pin verification, increasing-version rotation checks, reasoned revocation records, atomic writes, and secret-free ceremony status.
- Added `config/production-trust-root-ceremony.example.json`, operator documentation, and three focused regression tests.

### Validation

Python compilation passed and the full regression suite passed 295 tests with one existing Starlette/httpx deprecation warning. The live operator ceremony and production root material remain pending.

## 2026-08-27 — M14.1 enterprise environment contract

### Added

- Added `orville_core.enterprise_readiness` for validating enterprise environment identifiers, tenant boundaries, data classifications, bounded RTO/RPO, named operational owners, rollback authority, and escalation channels.
- Added `config/enterprise-environment.example.json` and `docs/M14_ENTERPRISE_ENVIRONMENT.md` with non-secret configuration and acceptance evidence.

### Validation

Python compilation passed, the M14.1 focused tests passed, and the full regression suite passed 292 tests with one existing Starlette/httpx deprecation warning. Environment provisioning, operator assignment, and production credentials remain deployment-owned.

## 2026-08-27 — M14 enterprise production-readiness roadmap

### Planned

- Defined M14 tasks for enterprise environment provisioning, production trust-root ceremony, live sandbox validation, tenant identity/authorization, protected secret management, reviewed deployment adapters, production metrics, non-production canary/rollback drills, disaster recovery, and production load gates.
- Added explicit dependencies, acceptance gates, and infrastructure-dependent boundaries in `docs/NEXT_MILESTONE_ENTERPRISE_PRODUCTION.md`.

### Scope boundary

M14 implementation remains infrastructure-dependent. No production credentials, live tenant environments, or official deployment-provider accounts are assumed to be available in the local repository.

## 2026-08-27 — M13 local security hardening and canary controls

### Added

- Added the provider-neutral `orville_core.canary` module with durable SQLite state, synthetic deployment adapter, minimum-sample health evaluation, approval-gated advancement, pause/quarantine, idempotent rollback, and secret-filtered audit events.
- Added authenticated `/api/v1/canary/runs` creation, deployment, observation, rollback, status, and audit inspection routes.
- Reconciled M13 security statuses for Windows/Linux adapter contracts, trust-store lifecycle, verification adapters, and the local security release gate.
- Added focused canary regression tests and documented the local implementation checkpoint and production boundaries.

### Validation

Python compilation passed. The full regression suite passed 287 tests with one existing Starlette/httpx deprecation warning. Production deployment-provider integration, worker IPC, GPU isolation, production trust-root ceremony, and non-production rollback drills remain infrastructure-dependent.

## 2026-08-27 — M13 security hardening and automated canary roadmap

### Planned

- Defined M13 security tasks for the threat-model refresh, Windows and Linux isolated workers, sandbox integration, trust-store lifecycle, Cosign/in-toto and optional TUF verification, and security release gates.
- Defined M13 canary tasks for policy schemas, provider-neutral deployment adapters, durable state transitions, health evaluation, rollback and quarantine, observability, synthetic fault injection, and production integration.
- Added explicit dependencies, parallelization boundaries, approval gates, restart/idempotency requirements, failure handling, and non-production rollback-drill criteria in `docs/NEXT_MILESTONE_SECURITY_CANARY.md`.

### Scope boundary

The roadmap specification does not claim that process isolation, production deployment, live traffic control, or production credentials are available. Those remain implementation and infrastructure-dependent work.

## 2026-08-27 — Enterprise catalog federation, audit, backups, and concurrency

### Added

- Added tenant-scoped remote catalog federation using `ORVILLE_CATALOG_STORE_URL`, `ORVILLE_CATALOG_STORE_TOKEN`, and `ORVILLE_TENANT_ID`.
- Added startup synchronization, explicit catalog synchronization, and remote publish status with local fallback.
- Added sanitized audit events for discovery, model selection, policy updates, catalog synchronization, and backup creation.
- Added atomic checksum-verified policy/discovery backups with backup listing APIs.
- Added `tools/load_test_provider_controls.py` for local concurrent rate-limit and active-model switching validation.

### Validation

Python compilation passed. The full regression suite passed 276 tests with one existing HTTP-client deprecation warning. The 16-worker/200-operation load test admitted exactly 100 calls under a 100-call limit and completed all 200 active-model switches.

### Limitations

The remote catalog and policy services remain deployment-owned. Enterprise deployments must provide tenant authentication, authorization, high availability, encrypted off-host backup retention, restore drills, and disaster recovery controls.

## 2026-08-27 — Persistent cross-process circuit state

### Added

- Added `SQLiteCircuitStateStore` with WAL mode, durable failure counters, cooldown timestamps, atomic increments, and short-lived connections suitable for independent worker processes and restarts.
- Added `ProviderRouter(circuit_store=...)` integration with in-memory behavior preserved when no store is configured.
- Exported `SQLiteCircuitStateStore` through the public package API.
- Added cross-process visibility, open/half-open/closed recovery, and router suppression tests in `tests/test_circuit_state.py`.

### Compatibility

Existing router construction remains compatible. SQLite is the standalone default persistence option when explicitly configured; Redis is not required and remains a future adapter for network-shared deployments.

### Validation

Focused circuit-state and routing tests pass: 16 tests. Full regression passes 276 tests with one existing HTTP-client deprecation warning. Python compilation passes for `orville_core`, `tests`, and `windows_gui.py`.

## 2026-08-27 — Provider operations and enterprise policy storage

### Added

- Added atomic persisted provider discovery catalogs with automatic activation of the first discovered model when the configured model is unavailable.
- Added explicit discovered-model selection through `POST /api/v1/providers/{provider_id}/models/select`.
- Added SQLite-backed provider call/token rate limits, provider-scoped usage metrics, and inspection routes for limits and usage.
- Added an authenticated enterprise remote policy storage adapter with local JSON fallback and secret-safe policy-store status.

### Validation

Python compilation passes for modified modules. The full regression suite passes 272 tests with one existing HTTP-client deprecation warning.

### Limitations

Remote policy service hosting, tenant identity, high availability, audit retention, and disaster recovery remain deployment-owned. Provider discovery catalogs are persisted locally; remote catalog federation remains future work.

## 2026-08-27 — Provider resilience and constrained fallback routing

### Added

- Added configurable bounded retries with transient-error classification and exponential backoff to `ProviderRouter`.
- Added circuit-state reporting with `closed`, `open`, and `half_open` states, cooldown suppression, and successful-call recovery.
- Applied resilience behavior to generation, media, and embedding operations while preserving capability, privacy, health, rate-limit, and `allow_fallback` constraints.
- Added 5 focused routing tests covering retry backoff, non-retryable failures, circuit transitions, local-only fallback boundaries, and invalid resilience limits.
- Documented provider resilience behavior and remaining streaming/persistent-state limitations in `PROVIDER_ROUTING.md`.

### Compatibility

Existing `ProviderRouter` construction and routing calls remain compatible. Default behavior adds up to two retries for classified transient failures; callers can disable retries with `retry_attempts=0`. Streaming does not retry after partial output.

### Validation

Focused routing tests pass: 13 tests. Full regression passes 270 tests with one existing HTTP-client deprecation warning. Python compilation passes for `orville_core`, `tests`, and `windows_gui.py`.

## 2026-08-27 — Provider discovery, privacy-aware routing, and redacted export

### Added

- Added provider model discovery for Ollama, OpenAI-compatible providers, and Gemini through `GET /api/v1/providers/{provider_id}/models`, with manual model entry for unsupported provider families.
- Added atomic JSON persistence for `local_only`, `cloud_approved`, and `restricted` routing policies.
- Added privacy-class propagation from objective intake into model execution; local-only and restricted classes force local-provider routing.
- Added `GET /api/v1/config/export/redacted` and desktop export controls that exclude raw API keys and credential-bearing headers.

### Validation

Focused provider-feature, routing, and API tests pass. Full regression passes 261 tests with one existing HTTP-client deprecation warning. Python compilation passes for all modified modules and `windows_gui.py`.

### Limitations

Provider discovery does not yet persist discovered catalogs or automatically change the active model. Rate-limit accounting, provider-specific retry policy, and remote production policy storage remain follow-up work.

## 2026-08-27 — Local-model lifecycle coverage and runtime requirement diagnostics

### Added

- Added `tests/test_local_models.py` with eight focused tests covering metadata preservation, duplicate detection, copy storage, checksum changes, unsupported formats, resource and hardware diagnostics, dry-run immutability, activation/deactivation, safe removal, and directory-model metadata.
- Added deterministic `runtime_matches_requirement` validation and `runtime_mismatch` diagnostics when a configured local runtime does not satisfy a caller-required runtime.

### Compatibility

Existing catalogs and validation calls remain compatible. Runtime mismatch checks are only restrictive when `required_runtime` is explicitly supplied; deletion of model files remains blocked behind an external confirmation flow.

### Validation

Focused local-model tests pass: 8 tests. Full regression passes 256 tests with one existing HTTP-client deprecation warning. Python compilation passes for `orville_core`, `tests`, and `windows_gui.py`.

## 2026-08-27 — Guided provider setup, GUI model manager, safety controls, and release gates

### Added

- Added a Windows local-model manager with inventory, validation diagnostics, runtime selection, license-restriction acceptance, activation, deactivation, and approval-gated registration removal that never deletes model files.
- Added a guided Provider setup window for Ollama, Gemini, OpenAI-compatible local servers, and Anthropic, with masked API-key entry, endpoint/model configuration, inventory refresh, and redacted provider health checks.
- Added non-executing model safety classification for safe, unsafe, and unknown serialization formats, script detection, adapter/base-model mismatch diagnostics, and preserved optional attestation metadata.
- Added API-level end-to-end coverage for local import, provenance, validation, license review, activation, objective routing, deactivation, and safe removal.
- Added `tools/release_gate.py` and `docs/RELEASE_GATES.md` for standalone compilation, regression, wheel packaging, safety, security, and deployment readiness checks.

### Limitations

Process-level sandboxing, GPU isolation, cryptographic attestation verification, full GUI task/execution workflow coverage, provider model discovery, privacy-aware routing persistence, and production deployment controls remain explicit follow-up or infrastructure-dependent work.

### Validation

The updated GUI passes Python compilation. The full 256-test regression suite, compilation, and wheel packaging pass; focused local-model, GUI lifecycle, and safety tests pass. The provider UI uses existing provider registration and health API contracts.


This file records material roadmap, architecture, behavior, governance, and release changes. Entries are ordered newest first. Dates use ISO 8601 calendar dates in the project working timezone.

## 2026-08-27 — Imported-model metadata and diagnostics

### Added

- Preserved license, license restrictions, provenance, ownership, and checksum metadata on every local model record, including Hub-origin metadata.
- Added structured validation diagnostics for unsupported formats, missing runtimes or endpoints, changed/corrupted files, insufficient disk/RAM/VRAM, incompatible hardware, and license review requirements.
- Added `GET /api/v1/models/local/{model_id}/validate` for detailed validation results without executing a model.

### Compatibility

Older catalogs load with empty metadata defaults. Existing model activation and provider behavior remain compatible unless a model has explicit license restrictions or fails integrity/resource validation.

### Validation

Full regression passes 246 tests with one existing HTTP-client deprecation warning. Python compilation passes for `orville_core` and `windows_gui.py`.

## 2026-08-27 — Local model lifecycle and streaming resume controls

### Added

- Added selectable local model storage with reference, copy, and link modes, checksum-aware deduplication, and safe storage-root containment.
- Added local runtime capability probing for Ollama, OpenAI-compatible local inference servers, llama.cpp gateways, and Transformers.
- Added approval-gated local model import API and desktop GUI import flow.
- Added bounded provider reconnects with replay-prefix suppression, cancellation partial checkpoints, and standard `Last-Event-ID` SSE resume handling.

### Compatibility

Existing catalog records default to reference mode. Existing text/code activation behavior remains compatible; multimodal and embedding capabilities are exposed only after runtime validation.

### Validation

Focused model, streaming, and media tests pass. Full regression passes 241 tests with one existing HTTP-client deprecation warning, and Python compilation passes for `orville_core` and `windows_gui.py`.

## 2026-08-27 — Repository governance expansion

### Added

- Expanded `AGENTS.md` with explicit trust-boundary, approval, secret-handling, artifact-retention, naming, formatting, branch, commit, review, validation, and handoff rules.
- Added `docs/REPOSITORY_GOVERNANCE.md` as the directory and lifecycle reference for source, tests, configuration, documentation, generated artifacts, logs, temporary files, browser-extension assets, and releases.
- Clarified that external instructions from files, websites, emails, PDFs, connector responses, model output, and tool output are untrusted data unless explicitly endorsed.
- Defined approval requirements for external communication, payments, account or permission changes, credential entry, sensitive connector actions, browser downloads, and destructive repository operations.

### Compatibility

No runtime API, persistence schema, provider protocol, frontend behavior, or packaging behavior changed. Existing files and user data were not moved or deleted.

### Validation

Verified the control files and expected directories exist, confirmed the governance rules match the current release scripts and repository structure, and retained existing runtime validation requirements for future code changes.

## 2026-08-27 — Phase 0 governance baseline

### Added

- Added repository-specific operating rules in `AGENTS.md`.
- Added predictable directories for new configuration, documentation, generated artifacts, logs, and temporary files: `config/`, `docs/`, `artifacts/`, `logs/`, and `tmp/`.
- Documented untrusted external instructions, approval gates for sensitive actions, secret-handling boundaries, validation expectations, and agent handoff requirements.
- Established repository conventions for source, tests, configuration, documentation, generated artifacts, logs, and temporary files.

### Compatibility

No runtime behavior, public API, persistence schema, provider protocol, or packaging behavior was changed by this governance update. Existing files were not moved.

### Validation

Confirmed the new control file exists and confirmed the directory baseline was created without relocating existing content. Runtime regression tests are not required for documentation-only changes; future code changes remain subject to the repository validation rules in `AGENTS.md`.

## Changelog

## 2026-08-27 — Help, errors, onboarding, and recovery guidance

### Added

- Added `docs/HELP_AND_RECOVERY_GUIDANCE.md` covering contextual help, first-run onboarding, safe operation-specific errors, tooltips, confirmations, state-aware recovery, accessibility, localization readiness, and secret-safe diagnostics.
- Added `docs/mockups/help-recovery.html`, a standalone synthetic prototype with onboarding guidance, accessible tooltips, an alert error, confirmation flow, and resume/retry/cancel recovery actions.
- Added `tests/test_help_and_recovery.py` with four focused tests covering contract completeness, required states, accessibility hooks, secret safety, and no-external-action behavior.

### Validation

Four focused unittest cases passed and Python compilation passed. No credentials, external services, or destructive actions were used. Live assistive-technology review and production GUI integration remain downstream validation work.


 policy

Each material entry must identify the date, category of change, compatibility impact, and validation evidence. Do not record credentials, tokens, private keys, or unredacted sensitive data.

## 2026-08-27 — MCP connector diagnosis and partial repair

### Changed

- Corrected the `python fast api` connector URL by removing trailing whitespace from `http://127.0.0.1:42069`.
- Updated the Fly connector note to identify `https://mcp.fly.dev` as unreachable and not the official Fly-documented transport.

### Validation

- Python MCP discovery advanced from an invalid-URL parse error to a connection-refused response, confirming the URL syntax repair. The local service is not listening on port `42069`.
- Fly MCP discovery timed out. Official Fly documentation describes `fly mcp server` as a local `flyctl` process with a default local port, so hosted repair is blocked until an official reachable transport and Fly CLI/auth configuration are provided.

### Status

The Python endpoint configuration repair is complete. The Fly connector remains an explicit external blocker rather than being represented as a working integration.

## 2026-08-27 — Fly MCP transport repaired

### Changed

- Installed the official `flyctl` v0.4.93 binary at `/home/ubuntu/.fly/bin/flyctl`.
- Replaced the stale hosted `https://mcp.fly.dev` connector transport with the official local stdio command `/home/ubuntu/.fly/bin/flyctl mcp server`.
- Removed the incompatible HTTP/SSE transport configuration that caused MCP initialization failures.

### Validation

- Fly MCP discovery now succeeds and reports 60 available tools.
- A read-only `fly-platform-regions` call reached the Fly CLI and returned the expected authentication requirement: `flyctl auth login`.

### Limitation

Fly account operations remain unavailable until the operator authenticates flyctl. Authentication was not performed because it requires user credentials or an interactive login session.

## 2026-08-27 — Python REST-to-MCP bridge implemented

### Added

- Added `orville_core/mcp_server.py`, a localhost-bound JSON-RPC MCP server on port `42069`.
- Added `tools/run_python_mcp.py` and the `orville-python-mcp` package entrypoint.
- Added `docs/PYTHON_MCP_BRIDGE.md` describing the architecture, route mapping, startup sequence, and security boundaries.
- Added `tests/test_mcp_server.py` covering initialization, tool discovery, REST forwarding, argument validation, unknown methods, and token requirements.

### Design

The bridge exposes 10 read-only tools mapped to authenticated Orville REST endpoints on port `8787`. It forwards the REST bearer token server-side, URL-encodes resource identifiers, enforces bounded request and response sizes, and does not expose mutation routes or connector credentials.

### Validation

Focused MCP tests passed: 5. Full regression suite passed: 241 tests, with one existing HTTP-client deprecation warning. Python compilation passed. A live desktop integration call successfully invoked `orville_health` through port `42069` and received the REST API health response from port `8787`.

## 2026-08-27 — MCP mutation controls and clean installation validation

### Added

- Added approval-gated mutation tools for project creation, task creation, project-memory writes, and personal-agent updates.
- Added dual mutation controls: `ORVILLE_MCP_MUTATIONS_ENABLED=1` at bridge startup plus `approved: true` on every mutation call.
- Updated bridge documentation and `.env.example` with the mutation feature flag and approval semantics.

### Safety

Mutation payloads are allowlisted per operation. The bridge does not expose arbitrary REST paths, connector invocation, terminal execution, schedule changes, secret operations, or destructive operations. Missing global enablement or per-call approval produces an MCP error without issuing a REST request.

### Validation

Clean wheel generation, isolated virtual-environment installation of `.[api]`, and imports of FastAPI, Uvicorn, the CLI, and MCP bridge succeeded. Focused MCP tests passed 8 tests, the full regression suite passed 246 tests with one existing HTTP-client deprecation warning, and Python compilation passed. A pre-existing corrupted `orville_core/cli.py` source file was repaired because it prevented full test collection.

## 2026-08-27 — M12.8 activation evidence and M13.8 policy contracts

### Added

- Added `ActivationAttestationEvidence` and `AttestationVerificationService` as the single application boundary for digest-bound attestation verification and secret-free activation evidence.
- Extended `LocalModelRecord` with persisted `activation_evidence`; activation now records the selected policy result after validation.
- Added `CanaryPolicy`, `CanaryCohort`, `HealthThresholds`, and `RollbackLimits` with bounded validation for M13.8.
- Added `config/canary-policy.example.json` and `docs/M13_SECURITY_BASELINE_PLATFORM_MATRIX.md`.

### Validation

The focused M12.8/M13.8 tests pass. The full regression suite passes 282 tests with one existing HTTP-client deprecation warning. Python compilation passes for all changed modules.

### Limitations

GUI attestation evidence presentation, Linux/GPU live isolation, production trust-root ceremony, and production canary deployment remain pending.


## 2026-08-27 — M14.3 sandbox validation checkpoint

Targeted security and sandbox tests passed 15 tests. Live Windows Sandbox/WSL and Linux bubblewrap execution could not run because the approved hosts lacked those runtimes; sanitized evidence is retained in artifacts/m14_3_sandbox_validation_2026-08-27.md. Full regression suite passed 295 tests with one existing Starlette/httpx deprecation warning.

## 2026-08-27 — Credential redaction security review

### Added

- Applied `SecretRedactor` to file-backed and SQLite checkpoint persistence.
- Added query-style secret and exception-message redaction helpers.
- Added `tools/security_review.py` for an independent local redaction review and clean-environment integration check using synthetic credentials only.

### Validation

Focused security tests passed: 11. Full regression suite passed 359 tests with one existing HTTP-client deprecation warning. Python compilation passed, and the independent review checker passed without credentials or external calls.


## 2026-08-27 — Phase 4 code-generation and delivery verification

### Added

- Added local-fake integration tests for provider HTTP and managed relay external boundaries.
- Added startup, authenticated main-workflow, disconnected-state, unauthorized, and invalid-input smoke coverage.
- Added `docs/DELIVERY_RUNBOOK.md` with standalone setup, run, test, configuration, deployment, rollback, and credential-safety instructions.
- Retained sanitized independent-review and validation evidence in `artifacts/phase4-independent-review.md` and `artifacts/phase4-validation-record.md`.

### Validation

The complete pytest suite passes 365 tests, unittest discovery passes 159 tests, Python compilation passes, the isolated clean-workspace main workflow persists a checkpoint, and Signal Room smoke/accessibility checks pass. Ruff, Black, mypy, isort, and flake8 are not configured in the supplied environment. Existing Starlette/httpx deprecation and unittest resource warnings remain non-blocking maintenance risks.

### Known limitations

Official third-party Blackbox OAuth remains blocked pending a documented provider flow. Live provider verification and production deployment evidence remain deployment-owned and were not attempted.


## 2026-08-27 — Progressive disclosure

### Added

- Added a default-collapsed `Show advanced options` control to the provider setup window.
- Kept provider type and model name in the primary path while moving endpoint, credential, timeout, capability, privacy, and provider-ID fields behind the reversible disclosure.
- Preserved entered values across collapse/expand operations and retained credential, approval, recovery, and accessibility boundaries.
- Added `docs/PROGRESSIVE_DISCLOSURE.md` and `tests/test_progressive_disclosure.py`.

### Validation

Three focused progressive-disclosure unittest cases and Python compilation for the modified GUI and test module passed. No credentials, external services, or destructive actions were used.


## 2026-08-27 — GUI accessibility

### Added

- Added native keyboard entry points for objective focus, workflow help, and shell focus, while retaining Tab traversal.
- Added visible focus borders for buttons and text controls and descriptive objective-workspace keyboard guidance.
- Added secret-safe, operation-specific error feedback with recovery instructions and focus return to the objective composer.
- Added `docs/GUI_ACCESSIBILITY.md` and `tests/test_gui_accessibility.py` covering keyboard access, focus, semantics, contrast, reduced motion, and error boundaries.

### Validation

Three focused GUI accessibility unittest cases and Python compilation for the modified GUI and test module passed. No credentials, external services, or destructive actions were used. Full screen-reader, platform-specific keyboard, rendered contrast, and web/mobile parity reviews remain follow-up gates.


## 2026-08-27 — Responsive layouts

### Added

- Added width-aware dashboard reflow in `windows_gui.py`: three columns at wide desktop widths, two columns at tablet widths, and one column at compact widths.
- Added bounded label wrapping and a refresh action that follows the final card row.
- Preserved the primary objective workspace while collapsing the context rail below 980 px and the sidebar below 790 px.
- Added `docs/RESPONSIVE_LAYOUTS.md` and `tests/test_responsive_layouts.py` covering breakpoints, shell collapse, wrapping, and refresh placement.

### Validation

Three focused responsive-layout unittest cases and Python compilation for the modified GUI and test module passed. No credentials, external services, or destructive actions were used. Pixel-level visual review, OS-specific font metrics, and web/mobile parity remain follow-up gates.


## 2026-08-27 — Consistent workflow states

### Added

- Added a shared desktop state vocabulary and classifier for loading, empty, offline, blocked, failed, partial, long-running, and ready outcomes.
- Applied the same state copy and recovery guidance to the execution monitor and verification view, including explicit loading and empty states before requests.
- Kept state feedback bounded and secret-safe by suppressing raw exceptions, credentials, payloads, and provider response bodies.
- Added `docs/WORKFLOW_STATE_HANDLING.md` and `tests/test_workflow_state_handling.py`.

### Validation

Three focused workflow-state unittest cases and Python compilation for the modified GUI and test module passed. No credentials, external services, or destructive actions were used. Live outage drills and cross-client visual review remain follow-up gates.


## 2026-08-27 — GUI architecture boundaries

### Added

- Selected a layered native-client architecture for the desktop GUI.
- Documented ownership and prohibited coupling across presentation, client adapter, API boundary, orchestration, model services, storage, and external integrations.
- Documented authenticated request/event flow, standalone operation, future-client reuse, credential handling, approval gates, failure projection, and lifecycle responsibilities.
- Added `docs/GUI_ARCHITECTURE_BOUNDARIES.md` and `tests/test_gui_architecture_boundaries.py`.

### Validation

Three focused GUI architecture documentation unittest cases and Python compilation for the test module passed. No credentials, external services, or destructive actions were used. Runtime dependency enforcement, multi-client contract testing, and production integration review remain follow-up gates.


## 2026-08-27 — GUI quality and major-journey test coverage

### Added

- Added `docs/GUI_TEST_STRATEGY.md` defining component, workflow, accessibility, responsive, and deterministic end-to-end test layers.
- Added `tests/test_gui_quality.py` with five focused tests covering shared controls, major GUI workflow surfaces, accessibility and secret-safety markers, responsive contracts, and the ordered objective-to-delivery journey.

### Validation

Five focused unittest cases passed and Python compilation passed. Tests use local repository artifacts and synthetic data only; no credentials, external services, browser sessions, or destructive actions were used. Live browser, screen-reader, visual-regression, performance, and backend-integrated e2e validation remain downstream release gates.


## 2026-08-27 — Visual regression checks

### Added

- Added `tools/visual_regression.py`, a deterministic fail-closed checker for reviewed design tokens and canonical critical-screen structure.
- Added `artifacts/visual_regression_baseline.json` as the reviewed baseline; baseline changes require explicit review rather than automatic regeneration.
- Added `docs/VISUAL_REGRESSION.md` and `tests/test_visual_regression.py` covering design-system markers, critical-screen structure, reproducibility, and drift detection.

### Validation

Three focused visual-regression unittest cases, the baseline comparison command, and Python compilation for the checker and test module passed. No credentials, external services, or destructive actions were used. Pixel-perfect cross-platform screenshot comparison and web/mobile baselines remain follow-up gates.

## 2026-08-27 — GUI performance measurement

Added `tools/measure_gui_performance.py`, `docs/GUI_PERFORMANCE_MEASUREMENT.md`, `docs/GUI_PERFORMANCE_BASELINE.json`, and `tests/test_gui_performance_measurement.py` for deterministic startup, interaction-latency, memory, and 1,000-task/500-artifact workload measurement. Four focused tests, Python compilation, and the Windows-target benchmark passed: 328.055 ms startup, 2.185 ms average interaction handling, and 100,235 peak traced bytes. No external credentials, services, GUI window, or destructive operation was used.


## 2026-08-27 — Worker concurrency limit increased to ten

### Changed

- Raised `tools/orville_manus_worker.py`'s bounded `--max-active` range from 1–3 to 1–10, with a default of 10.
- Corrected the designated worker-slot allowlist to include explicit `Worker Task 1` through `Worker Task 10` names.
- Updated `docs/ORVILLE_MANUS_WORKER.md` and `tests/test_orville_manus_worker.py` for the ten-task configuration.

### Validation

Nine worker tests passed, Python compilation passed, CLI help exposes values 1–10, and a credential-free `--dry-run --max-active 10` completed successfully. No external API call or credential value was used.


## 2026-08-27 — Standalone GUI operations documentation

### Added

- Added `docs/GUI_STANDALONE_OPERATIONS.md` covering source run, local API startup, build and release validation, PyInstaller packaging, portable and installed operation, safe updates, independent Compose deployment, rollback, recovery, data preservation, and Manus-independent security boundaries.
- Added `tests/test_gui_standalone_operations.py` with three focused documentation checks for run/build/package commands, update/deployment/rollback boundaries, and credential-safe standalone operation.

### Validation

Three focused unittest cases passed and Python compilation passed. No credentials, external services, or destructive actions were used. Code signing, live provider/browser verification, production deployment, and infrastructure-owned rollback evidence remain downstream responsibilities.


## 2026-08-27 — GUI sensitive-data exposure checks

### Added

- Added recursive safe display projection for provider, model, API, and operation output.
- Redacted credential-like values, prompts, local paths, runtime endpoint values, and protected authentication state before rendering.
- Removed raw manager exception display and objective echoing from GUI output/context widgets.
- Added `docs/GUI_SENSITIVE_DATA.md` and `tests/test_gui_sensitive_data.py` covering synthetic credentials, prompts, paths, raw errors, and required exposure categories.

### Validation

Three focused sensitive-data unittest cases and Python compilation for the modified GUI and test module passed. No live credentials, external services, or destructive actions were used. Live traffic, secret-store, crash/clipboard, and web/mobile exposure review remain separate release gates.


## 2026-08-27 — Workload classification contract

### Added

- Added `WorkloadClassification` and `classify_workload` to classify automation as `one_shot`, `recurring`, `event_triggered`, `webhook_driven`, or `persistent_service`.
- Added deterministic precedence, explicit-type conflict rejection, required-control metadata, public exports, `docs/WORKLOAD_CLASSIFICATION.md`, and `tests/test_workload_classification.py`.

### Validation

Five focused workload-classification tests passed and Python compilation passed for the implementation, package exports, and test module. The classifier is side-effect-free and uses no credentials or external services.


## 2026-08-27 — Schedule ownership and lifecycle

### Added

- Defined schedule ownership and delegated-operator responsibilities.
- Defined IANA timezone input, UTC normalization, DST behavior, expiration, pause/resume, and missed-run policy.
- Defined durable failure-before-notification ordering, approved non-secret notification targets, bounded notification retries, and deduplication.
- Added `docs/SCHEDULE_OWNERSHIP_LIFECYCLE.md` and `tests/test_schedule_ownership_lifecycle.py`.

### Validation

Three focused schedule-contract unittest cases and Python compilation for the test module passed. No credentials, external services, or destructive actions were used. Runtime schema migration, live scheduler execution, notification-provider delivery, and production timezone/DST drills remain follow-up gates.


## 2026-08-27 — Scheduled workflow idempotency and retry safety

### Changed

- Changed scheduled claims so `next_run_at` advances only after successful completion.
- Added deterministic occurrence execution IDs and durable reuse of execution records.
- Completed scheduled runs are deduplicated; failed runs remain retryable with the same workflow idempotency key.
- Added `ScheduleStore.advance_after_success` and focused coverage in `tests/test_scheduled_idempotency.py`.
- Added `docs/SCHEDULED_WORKFLOW_IDEMPOTENCY.md`.

### Validation

Six focused scheduler/automation tests passed and Python compilation passed. Tests use synthetic local handlers and do not contact external services or use credentials. Provider-side idempotency and compensation remain handler responsibilities.

## 2026-08-27 — Worker concurrency configuration

Updated `tools/install_orville_manus_worker.ps1` so scheduled-task registration, description, and dry-run guidance consistently use `--max-active 10`. The worker already validates and caps concurrency at ten existing task threads. No credentials or task records were changed.


## 2026-08-27 — Long-running job state and restart recovery

### Added

- Defined durable workflow, task checkpoint, event cursor, execution lease, artifact reference, and recovery records.
- Defined atomic state/event transitions, checkpoint sequencing, stale-lease protection, deterministic restart reconciliation, retention, and fail-closed recovery for unproven external side effects.
- Added `docs/LONG_RUNNING_JOB_STATE.md` and `tests/test_long_running_job_state.py`.

### Validation

Three focused long-running state unittest cases and Python compilation for the test module passed. No credentials, external services, or destructive actions were used. Runtime supervisor implementation, crash injection, multi-process lease testing, and production storage durability remain follow-up gates.


## 2026-08-27 — Execution target selection contract

### Added

- Added `docs/EXECUTION_TARGET_SELECTION.md`, defining when to use sandbox execution, managed web hosting, attached desktop execution, or persistent computing.
- Documented target selection by workload lifecycle, interface, operating-system capability, network identity, resource budget, and data residency.
- Documented secret boundaries, approval gates, resource limits, recovery and rollback expectations, escalation rules, and target-specific validation.
- Added `tests/test_execution_target_selection.py` with three focused decision-contract checks.

### Validation

Three focused tests passed and Python compilation passed. No credentials, external services, purchases, deployments, or destructive actions were used.


## 2026-08-27 — Health monitoring, structured logs, and operational runbooks

### Added

- Defined stable component health states and configurable availability, error-rate, latency, saturation, freshness, security, and release-quality signals.
- Defined bounded structured JSON operational events with correlation, severity, redaction, retention, access, and logging-failure rules.
- Added standalone operational runbooks for unavailable services, elevated failures, saturation, security/integrity findings, and release/canary failures.
- Added `docs/HEALTH_MONITORING_LOGGING_RUNBOOKS.md` and `tests/test_health_monitoring_logging_runbooks.py`.

### Validation

Three focused health/logging/runbook unittest cases and Python compilation for the test module passed. No credentials, external services, or destructive actions were used. Live alert delivery, hosted dashboards, production-calibrated thresholds, retention enforcement, and operator tabletop exercises remain deployment-owned gates.


## 2026-08-27 — Workflow dry-run mode

### Added

- Added `WorkflowExecutor.execute(..., dry_run=True)` for safe workflow previews.
- Mutating steps marked `mutates_external_state=True` are skipped and reported as `dry_run_actions`; safe local steps may execute; mutation success is never fabricated; and live approval rules remain active.
- Added `docs/WORKFLOW_DRY_RUN.md` and `tests/test_workflow_dry_run.py`.

### Validation

Three focused dry-run tests passed and Python compilation passed. Tests use synthetic local handlers only and do not contact external services or use credentials. Live provider, permission, quota, payload, and deployment behavior requires separate validation.


## 2026-08-27 — Approval checkpoints

### Added

- Added durable, deterministic `ApprovalCheckpoint` records for irreversible and high-impact workflow steps.
- Added idempotent checkpoint creation, single-use terminal resolution, bounded action/target summaries, approver references, and first-decision preservation in `orville_core/automation.py`.
- Added `docs/APPROVAL_CHECKPOINTS.md` and `tests/test_approval_checkpoints.py` covering fail-closed states, exact scope, dry-run separation, recovery, and safe evidence.

### Validation

Three focused approval-checkpoint unittest cases and Python compilation for the automation and test modules passed. No credentials, external services, or destructive actions were used. Live identity-provider authorization, external connector execution, and production destructive-action exercises remain deployment-owned gates.


## 2026-08-27 — Secret-handling rules

### Added

- Added `docs/SECRET_HANDLING_RULES.md`, defining protected handling for environment variables, configuration files, logs, artifacts, reports, screenshots, recordings, GUI fields, backups, and packaged outputs.
- Documented non-secret credential references, server-side consumption, pre-retention redaction, rotation and revocation, recovery, path containment, and secret-scan validation.
- Added `tests/test_secret_handling_rules.py` with focused contract and redaction checks.

### Validation

Three focused tests passed and Python compilation passed. Tests use synthetic values only and do not contact external services or use credentials. Provider secret-manager configuration and live incident response remain environment-owned controls.

## 2026-08-27 — Worker task-record assignment

At the user's request, created seven private Manus task records for Worker Task 3 through Worker Task 9 and assigned distinct unchecked TODO lines 727, 729, 731, 733, 735, 737, and 741. Persisted nine total unique worker records; Worker Task 10 remains available. A dry run validated the state with `max_active=10`. No credential value was written to the repository.


## 2026-08-27 — External-boundary validation and sanitization

### Added

- Added shared bounded text and identifier validation for untrusted inputs.
- Added HTTP(S) URL validation that rejects embedded credentials and requires explicit permission for local endpoints.
- Added recursive bounded output sanitization for sensitive keys, credential-like values, bearer tokens, and local filesystem paths.
- Added `docs/EXTERNAL_BOUNDARY_VALIDATION.md` and extended `tests/test_external_boundaries.py` with six focused boundary cases.

### Validation

Six focused external-boundary pytest cases and Python compilation for `orville_core/boundary.py` and the test module passed. No credentials, external services, or destructive actions were used. Live provider fuzzing, browser payload review, file-parser hardening, and production traffic inspection remain separate release gates.


## 2026-08-27 — Core unit-test coverage

### Added

- Added `tests/test_core_unit_contracts.py` covering task parsing round-trips, graph dependency and ownership validation, routing endpoint and request constraints, persisted engine state transitions, and artifact registration metadata.

### Validation

Five focused unit tests passed, and Python compilation passed for the covered core modules and test module. Tests use temporary local state and synthetic inputs only; no credentials or external services were used.


## 2026-08-27 — Regression fixtures

### Added

- Added `tests/fixtures/regressions/manifest.json` and three retained JSON fixtures for scheduled retry identity, workflow dry-run mutation suppression, and nested secret redaction.
- Added `tests/test_regression_fixtures.py` to load the manifest and exercise each corrected behavior with synthetic local inputs.

### Validation

Four focused regression-fixture tests passed and Python compilation passed. No external services, credentials, or destructive operations were used. External-provider, browser, connector, and deployment regression coverage remains separate integration work.


## 2026-08-27 — Boundary integration tests

### Added

- Added `tests/test_boundary_integrations.py` with local-fixture integration coverage for filesystem, model, GitHub/connector, browser, scheduling, provider, and webhook boundaries.
- Covered approval-gated connector invocation, workspace secret-file exclusion, model checksum verification, browser restart recovery, scheduled lease release, provider error redaction, and webhook signature validation without live credentials or external side effects.

### Validation

Six focused boundary integration pytest cases and Python compilation for the integration module passed. One pre-existing FastAPI/Starlette TestClient deprecation warning was emitted. Live service interoperability and platform-specific execution remain deployment-owned gates.


## 2026-08-27 — Deterministic test data and mock external service

### Added

- Added `tests/fixtures/deterministic_external_cases.json` with stable health, echo, unavailable, and credential-safety expectations.
- Added `tests/fixtures/mock_external_service.py`, a loopback-only HTTP fixture with deterministic JSON responses and bounded shutdown.
- Added `tests/test_deterministic_mocks.py` covering JSON client success/error behavior and fixture secret safety.

### Validation

Three focused mock-service tests passed and Python compilation passed. The service is local-only, uses synthetic inputs, and does not contact external providers or use credentials.


## 2026-08-27 — Performance boundary tests

### Added

- Added `tests/test_performance_boundaries.py` covering 100-task graph execution, bounded parallel fan-out, transient retries, and 100-artifact registration/listing.
- Added repeatable local timing gates with generous thresholds to detect severe regressions without claiming production capacity.

### Validation

Four focused performance pytest cases and Python compilation for the test module passed in 4.23 seconds. No credentials, external services, or destructive actions were used. Production load calibration and environment-specific benchmarking remain separate operational work.


## 2026-08-27 — Security attack-surface tests

### Added

- Added `tests/test_security_attack_surfaces.py` covering secret leakage, prompt-injection-as-data handling, path traversal, unauthorized filesystem writes, unsafe shell syntax, credential-like sandbox environments, and unauthorized tool actions.

### Validation

Five focused security tests passed and Python compilation passed for the covered policy modules and test module. Tests use synthetic values and temporary local paths only; no unsafe commands, credentials, external services, or side effects were used.


## 2026-08-27 — Failed-test triage before release

### Added

- Added `tools/test_triage.py` to validate secret-free failure dispositions with stable test IDs, owners, classifications, actions, and evidence.
- Added `config/test_triage_manifest.json` as the checked-in non-secret triage source and `docs/TEST_FAILURE_TRIAGE.md` for the required lifecycle and release procedure.
- Updated `tools/project_checks.py` so the test gate validates the triage manifest after the regression suite.
- Added `tests/test_test_triage.py` covering valid records, the empty baseline, missing fields, unsupported statuses, and duplicate identifiers.

### Validation

Three focused tests passed, the triage CLI validated the empty baseline, and Python compilation passed. No credentials, external services, or destructive actions were used.


## 2026-08-27 — Representative workflow acceptance tests

### Added

- Added `tests/test_acceptance_workflows.py` with credential-free acceptance coverage for representative coding and research workflows.
- Covered objective normalization, dependency-aware execution, independent verification, durable checkpoint persistence, artifact delivery, and research-source preservation.

### Validation

Two focused acceptance tests and Python compilation passed. Live provider, browser, connector, deployment, production, and GUI acceptance remain environment-specific and were not exercised.


## 2026-08-27 — Deployment commands by target

### Added

- Added `deploy.ps1` with explicit target selection for sandbox, web hosting, attached desktop, and persistent computing.
- Made deployment dry-run by default; live execution requires explicit `-Execute` after review and approval.
- Added `docs/DEPLOYMENT_TARGET_COMMANDS.md` with commands, target matrix, boundaries, validation, and rollback/recovery procedure.
- Added `tests/test_deployment_commands.py` for target coverage, dry-run safety, and existing command-boundary preservation.

### Validation

Three focused tests passed, PowerShell syntax parsing passed, and Python compilation passed. No live deployment, credential use, network upload, installation, or container start was performed.


## 2026-08-27 — Deployment targets and environment variables

### Added

- Added `docs/DEPLOYMENT_TARGETS_AND_ENVIRONMENT.md` defining local Python, installed Windows, portable Windows, Docker Compose small-team, and disposable-container targets.
- Documented required runtime configuration, optional integration variables, portable-release behavior, secret boundaries, production prerequisites, and unsupported managed-cloud/Kubernetes/serverless claims.
- Added `ORVILLE_PORTABLE=0` and `ORVILLE_REQUESTS_PER_MINUTE=120` to `.env.example` as safe non-secret defaults.
- Added `tests/test_deployment_targets.py` to verify target coverage, template synchronization, and secret/production boundaries.

### Validation

Three focused deployment-target tests and Python compilation passed. No credentials, network calls, infrastructure changes, or destructive actions were used. Live production promotion remains deployment-owned.

## 2026-08-27 — Worker orphan cleanup and temporary concurrency rollback

Removed the seven local Worker Task 3–9 records whose remote IDs repeatedly returned HTTP 404, preserving Worker Task 1–2 and a non-secret state backup under `artifacts/`. Temporarily changed `tools/install_orville_manus_worker.ps1` and the installed Scheduled Task to `--max-active 3` until the Manus task-routing visibility issue is resolved. Validation confirmed two persisted records, zero orphan slots, and the scheduled task using the three-task limit.


## 2026-08-27 — Versioning and release notes

### Added

- Added `docs/VERSIONING_AND_RELEASE_NOTES.md` defining Semantic Versioning 2.0.0, the `pyproject.toml` source of truth, release immutability, candidate handling, release-note structure, validation evidence, upgrade, and rollback rules.
- Added `RELEASE_NOTES.md` for the initial `0.1.0` standalone baseline, including user-facing changes, security boundaries, supported baseline, validation scope, upgrade guidance, and known limitations.
- Added `tests/test_versioning_release_notes.py` covering version consistency, required release-note sections, SemVer policy, and secret-safe wording.

### Validation

Three focused versioning/release-note tests and Python compilation passed. No credentials, external services, or destructive actions were used.


## 2026-08-27 — Deployment validation and smoke checks

### Added

- Added `tools/deployment_validation.py` with target-specific preflight validation for sandbox, web hosting, attached desktop, and persistent computing.
- Added bounded, credential-free HTTP smoke checks with loopback-by-default safety and explicit opt-in for remote hosts.
- Updated `deploy.ps1` to run preflight before deployment actions and `/docs` smoke checks after web-hosting and persistent-computing execution.
- Added `tests/test_deployment_validation.py` covering supported targets, local health checks, remote-host safety, and missing prerequisites.

### Validation

Seven focused deployment tests passed, including a deterministic local HTTP fixture. Python compilation and PowerShell parser validation passed. No credentials, external services, live deployments, or destructive actions were used.


## 2026-08-27 — Least-privilege permissions

### Added

- Added `LeastPrivilegePolicy` to `orville_core/security.py` with default-deny, task-scoped checks for connector IDs and scopes, repository IDs and write access, root-bound files, and normalized remote hosts and actions.
- Added `docs/LEAST_PRIVILEGE_PERMISSIONS.md` documenting resource boundaries, write/side-effect separation, approval requirements, and safe configuration examples.
- Added `tests/test_least_privilege_permissions.py` covering default denial, connector scope minimization, repository write separation, file containment, remote host/action allowlists, and explicit write grants.

### Validation

Four focused permission tests and Python compilation passed. No credentials, external systems, network calls, or destructive actions were used. Live connector, repository, remote-system, and deployment enforcement remains target-specific.


## 2026-08-27 — Explicit sensitive-operation confirmations

### Added

- Added `orville_core/confirmations.py` with fail-closed, single-use, expiring confirmation receipts for payments, purchases, publishing, deletion, account and permission changes, credential entry, external sends, connector mutations, and destructive file actions.
- Bound confirmations to the exact operation, target, scope, requester, and stable fingerprint without carrying secret payloads.
- Updated `docs/DESTRUCTIVE_ACTION_CONFIRMATIONS.md` with the executable gate contract and focused validation command.
- Added `tests/test_confirmations.py` for coverage, missing approval, scope mismatch, expiry, and receipt reuse.

### Validation

Seven focused confirmation and destructive-action tests passed, Python compilation passed, and a precise secret-pattern scan passed. No credentials, external services, or destructive actions were used. UI integration, provider authorization, and deployment-specific audit persistence remain caller-owned.


## 2026-08-27 — Sensitive-domain safe handling

### Added

- Added deterministic classification and safety metadata for medical, legal, tax, financial, insurance, real-estate, gambling, and major-life-decision objectives in `orville_core/workflow.py`.
- Added informational-only guidance, professional-review requirements, consequential-action approval gates, and a prohibited autonomous-behavior list without generating domain advice.
- Exported `classify_sensitive_domains` and `sensitive_domain_safety` through `orville_core.__init__`.
- Added `tests/test_sensitive_domain_safety.py` covering all requested domains, non-blocking informational requests, consequential-action gates, and advice-boundary wording.

### Validation

Four focused sensitive-domain tests and Python compilation for the modified modules passed. No credentials, external services, or user-specific advice were used. Professional review, emergency handling, jurisdiction-specific requirements, and live policy evaluation remain outside this local contract.


## 2026-08-27 — Untrusted-content execution boundary

### Added

- Added `orville_core/untrusted_content.py` with bounded deterministic detection of instruction-like external content.
- Added a fail-closed authorization boundary that prevents external pages, tool results, model outputs, and downloaded artifacts from authorizing tool execution based solely on their contents.
- Required separate explicit endorsement for trusted-origin execution and added `tests/test_untrusted_content.py`.

### Validation

Five focused untrusted-content tests and the existing external-boundary tests passed. Python compilation and a precise secret-pattern scan passed. No credentials, external services, or destructive actions were used. Provider-specific adapter integration and durable audit persistence remain follow-up work.


## 2026-08-27 — Incident response, credential rotation, and recovery procedures

### Added

- Added `docs/INCIDENT_RESPONSE_CREDENTIAL_ROTATION_RECOVERY.md` covering severity classification, incident intake, safe evidence preservation, fail-closed containment, credential rotation and revocation, backup/checkpoint restoration, staged recovery, failed-recovery handling, closure, and post-incident review.
- Added `tests/test_incident_response_procedures.py` to verify required operational stages, recovery validation, approval boundaries, standalone operation, and secret-safe wording.

### Validation

Four focused documentation tests passed, Python compilation passed, and a precise secret-pattern scan passed. No credentials, external services, or destructive actions were used. Live provider rotation, infrastructure recovery, and production incident exercises remain deployment-owned.


## 2026-08-27 — Dependency and supply-chain review

### Added

- Added `orville_core/supply_chain.py` with non-executing review primitives for downloaded packages, scripts, and artifacts.
- Added approved-root containment, SHA-256 verification, provenance requirements, script independent-review gating, and value-only review results without file execution or network access.
- Added `docs/SUPPLY_CHAIN_REVIEW.md` covering dependency, download, script, artifact, evidence, and retention procedures.
- Added `tests/test_supply_chain_review.py` covering default-deny path handling, integrity/provenance gates, script review, and safe review metadata.

### Validation

Four focused supply-chain tests and Python compilation for the modified modules passed. No packages were installed, scripts executed, artifacts downloaded, credentials used, or external calls made. Live vulnerability databases, package indexes, remote repositories, model hubs, and deployment scanners remain environment-specific follow-up checks.


## 2026-08-27 — Orchestration test matrix

### Added

- Added `docs/ORCHESTRATION_TEST_MATRIX.md` mapping orchestration, delegation, graph dependencies, retries, failures, approvals, integration, and safety integration to executable test modules, owners, acceptance gates, and deterministic execution profiles.
- Added `tests/test_orchestration_test_matrix.py` to verify matrix completeness, referenced test-module existence, safety gates, and explicit limits on live external validation.

### Validation

Four focused matrix-completeness tests passed, Python compilation passed, and a precise secret-pattern scan passed. No credentials, external services, or destructive actions were used. Full regression and live provider or infrastructure validation remain governed by the release gate.


## 2026-08-27 — Rollback and recovery verification

### Added

- Added `orville_core/recovery.py` with approval-requiring rollback-plan construction and non-destructive recovery-evidence verification.
- Added checks for backup existence, SHA-256 integrity, authenticated health, read-only state, and representative smoke workflow success.
- Added `docs/ROLLBACK_AND_RECOVERY_VERIFICATION.md` covering evidence preservation, credential response, storage safety, failed-recovery escalation, and closure requirements.
- Added `tests/test_rollback_recovery.py` covering explicit rollback approvals, matching backup checksums, complete evidence, failed checks, and missing-backup fail-closed behavior.

### Validation

Four focused rollback/recovery tests and Python compilation for the modified modules passed. No deployment commands, restores, external services, credentials, or destructive actions were used. Live rollback, database restoration, and target-specific recovery drills remain deployment-owned.


## 2026-08-27 — Structured correlation logging

### Added

- Added `orville_core/structured_logging.py` with structured JSON-lines events for multi-agent executions, execution-scoped correlation IDs, task and agent identifiers, bounded fields, UTC timestamps, severity, and secret-safe sanitization.
- Added `tests/test_structured_logging.py` covering correlation propagation, JSON shape, redaction, bounded messages, JSONL persistence, and resource-safe file handling.

### Validation

Four focused logging tests and the existing credential-redaction tests passed with `ResourceWarning` promoted to errors. Python compilation passed. No credentials or external services were used. Adapter-specific logger wiring and centralized log transport remain follow-up integration work.


## 2026-08-27 — Execution metrics

### Added

- Extended `orville_core.telemetry.MetricSeries` and `TelemetryRegistry.record` with task duration, success rate, retry count, bounded failure classes, and verification outcome aggregation.
- Preserved the existing telemetry API while adding validation for non-negative retry counts and bounded metric labels.
- Added `tests/test_telemetry_metrics.py` covering aggregate metrics, failure-only classification, bounded labels, and invalid retry counts.

### Validation

Three focused metrics tests and Python compilation passed. Metrics retain aggregate values only and no prompts, payloads, credentials, or raw errors. Adapter-specific instrumentation and production dashboard/report export remain environment-specific follow-up work.


## 2026-08-27 — Operational dashboards and reports

### Added

- Added `tools/operational_report.py`, a bounded standalone JSONL report generator for local, attached-desktop, sandbox, web-hosting, and persistent-computing targets.
- Added `docs/OPERATIONAL_DASHBOARDS_AND_REPORTS.md` documenting report fields, target support, interpretation, retention, privacy, and deployment-owned alerting limits.
- Added `tests/test_operational_report.py` covering aggregation, empty-log semantics, malformed input, and supported targets.

### Validation

Four focused operational-report tests passed, Python compilation passed, and a precise secret-pattern scan passed. No credentials, external services, or destructive actions were used. Hosted log collection, live dashboards, alert delivery, and infrastructure SLO collection remain deployment-owned.


## 2026-08-27 — Maintenance ownership and upgrade cadence

### Added

- Added `docs/MAINTENANCE_OWNERSHIP_AND_UPGRADE_CADENCE.md` assigning core, integration, security, GUI, release/deployment, documentation, and incident-recovery ownership boundaries.
- Defined every-change, weekly, monthly, quarterly, pre-release, and post-release maintenance activities with required evidence.
- Documented upgrade triggers, compatibility and migration requirements, rollback expectations, escalation paths, and ambiguity handling.
- Added `tests/test_maintenance_ownership.py` covering role ownership, cadence coverage, upgrade requirements, escalation, and secret-safe documentation.

### Validation

Three focused maintenance-contract tests and Python compilation passed. No credentials, external services, schedules, or infrastructure changes were used. Live ownership assignment, alerting, dependency scanners, and recovery exercises remain environment-specific.

## 2026-08-27 — Task replication-delay poller

Added `tools/poll_task_replication.py`, a bounded read-only CLI that polls `task.detail` for a 22-character task ID, retries 404 and other transient responses until visibility or timeout, stops on terminal errors, and never prints or persists credentials. Added `tests/test_poll_task_replication.py`; four focused tests, compilation, and invalid-ID CLI validation passed.


## 2026-08-27 — Standalone README

### Added

- Rewrote `README.md` as a standalone operating guide with prerequisites, isolated installation, configuration, local usage, examples, testing, deployment, troubleshooting, security boundaries, and explicit limitations.
- Added `tests/test_standalone_readme.py` to verify required sections, runnable local commands, referenced repository files, security guidance, and credential-safe wording.

### Validation

Four focused README tests passed, Python compilation passed, and a precise secret-pattern scan passed. No credentials, external services, or destructive actions were used.


## 2026-08-27 — Architecture document

### Added

- Added `docs/ARCHITECTURE.md` documenting the standalone component model, agent roles and handoffs, task-graph state, orchestration and checkpoints, tools and external boundaries, artifact and verification lifecycles, recovery, observability, and security controls.
- Added `tests/test_architecture_document.py` covering requested architecture sections, implemented component references, standalone/state contracts, and security boundaries.

### Validation

Three focused architecture-contract tests and Python compilation passed. No credentials, external services, or destructive actions were used. The document explicitly distinguishes implemented local contracts from live provider, browser, connector, infrastructure, and production validation.


## 2026-08-27 — Operator runbook

### Added

- Added `docs/OPERATOR_RUNBOOK.md` covering health checks, readiness, failure triage, connector diagnosis and fallback, credential exposure handling, checkpoint and backup recovery, staged restoration, escalation, and closure evidence.
- Added `tests/test_operator_runbook.py` to verify required procedures, commands, recovery boundaries, referenced documents, and secret-safe wording.

### Validation

Four focused operator-runbook tests passed, Python compilation passed, and a precise secret-pattern scan passed. No credentials, external services, or destructive actions were used. Live provider, connector, infrastructure, and production recovery actions remain deployment-owned.


## 2026-08-27 — Task template catalog

### Added

- Added `config/task-templates.json` with versioned templates for research, coding, automation, web development, media, documents, and deployments.
- Added `docs/TASK_TEMPLATES.md` describing template selection, refinement, safety, maintenance, and verification requirements.
- Added `tests/test_task_templates.py` covering requested template types, common fields, safety contracts, JSON integrity, and versioning.

### Validation

Four focused task-template tests passed, Python compilation passed, JSON parsing and seven-template count validation passed, and a precise secret-pattern scan passed. No credentials, external services, or destructive actions were used.


## 2026-08-27 — Contributor guide

### Added

- Added `docs/CONTRIBUTING.md` covering standalone prerequisites and setup, repository layout, development workflow, focused and full validation, review requirements, security and untrusted-content rules, release and deployment procedures, handoffs, completion criteria, and troubleshooting.
- Added `tests/test_contributor_guide.py` covering setup, test commands, review, release, security, and handoff guidance.

### Validation

Three focused contributor-guide tests and Python compilation passed. No credentials, external services, or destructive actions were used. Live ownership, hosted infrastructure, provider authorization, and production release actions remain environment-specific.


## 2026-08-27 — Standalone examples

### Added

- Added `examples/README.md` documenting no-Manus execution, local setup, and safe example expectations.
- Added `examples/local_operational_report.py` for deterministic local JSON report generation using temporary data.
- Retained `examples/basic_run.py` as a dependency-aware checkpointed workflow example and added focused execution tests.

### Validation

Three focused standalone-example tests passed, Python compilation passed, and a precise credential-pattern scan passed. No Manus-specific functionality, credentials, external services, or destructive actions were used.


## 2026-08-27 — Graceful degradation

### Added

- Added `docs/GRACEFUL_DEGRADATION.md` documenting stable unavailable-dependency states for connectors, websites, providers, partial dependencies, and offline operation.
- Defined preservation of objectives, task graphs, checkpoints, local artifacts, source identifiers, and transformation history during dependency failures.
- Documented bounded idempotent retries, explicit fallback and privacy constraints, partial-result labeling, sanitized diagnostics, recovery steps, and escalation boundaries.
- Added `tests/test_graceful_degradation.py` covering state vocabulary, safe recovery, fallback restrictions, retry rules, evidence preservation, and security boundaries.

### Validation

Three focused graceful-degradation documentation tests and Python compilation passed. No credentials, external services, browser sessions, or destructive actions were used. Live connector recovery, website availability, authentication, failover, alerting, and production network behavior remain environment-specific.


## 2026-08-27 — Canonical glossary

### Added

- Added `docs/GLOSSARY.md` defining task graph, agent role, artifact, verification gate, connector, execution state, and related orchestration terms.
- Added `tests/test_glossary.py` covering required definitions, concept distinctions, safety boundaries, maintenance rules, and secret-safe wording.

### Validation

Four focused glossary tests passed, Python compilation passed, and a precise secret-pattern scan passed. No credentials, external services, or destructive actions were used.


## 2026-08-27 — Repeated failure pattern review

### Added

- Added `orville_core/failure_patterns.py` with a bounded local analyzer for completed task-graph run events.
- Aggregated recognized task, verification, run, and block failures by sanitized class, with occurrence counts, distinct run/task counts, thresholds, and generic improvement guidance.
- Exported `FailurePattern` and `review_completed_task_graphs` through `orville_core.__init__`.
- Added `docs/REPEATED_FAILURE_REVIEW.md` describing review procedure, safe output, thresholds, improvement conversion, and security boundaries.
- Added `tests/test_failure_patterns.py` covering repeated detection, terminal-run filtering, nonfailure exclusion, secret-safe output, thresholds, and bounded reporting.

### Validation

Three focused failure-pattern tests and Python compilation of the analyzer, package exports, and tests passed. No credentials, external services, or automatic remediation were used. The analyzer does not infer causality or authorize changes to policy, retries, permissions, routing, or production systems.


## 2026-08-27 — Reusable fixes catalog

### Added

- Added `config/reusable-fixes.json` with named recurring-fix categories linking release validation, sensitive-operation safety, operator recovery, standalone delivery, and terminology/observability assets.
- Added `docs/REUSABLE_FIXES.md` defining the reuse workflow, maintenance rules, safety boundaries, and validation command.
- Added `tests/test_reusable_fixes.py` covering category coverage, referenced assets, schema versioning, safety boundaries, and secret-safe wording.

### Validation

Four focused reusable-fix tests passed, Python compilation passed, JSON validation and referenced-asset checks passed, and a precise secret-pattern scan passed. No credentials, external services, or destructive actions were used.


## 2026-08-27 — Lifecycle phase-duration metrics

### Added

- Extended `TelemetryRegistry` with bounded planning, execution, verification, and recovery duration aggregation through `record_phase_duration`.
- Added phase-name normalization and fail-closed rejection of unknown, negative, and non-finite durations while preserving the existing task-metrics snapshot/export shape.
- Added `tests/test_phase_duration_metrics.py` covering all four lifecycle phases, aggregation, invalid values, and coexistence with existing task metrics.

### Validation

Three focused phase-duration tests and Python compilation passed. Metrics retain aggregate values only and no prompts, payloads, credentials, or raw errors. Automatic instrumentation at every production lifecycle boundary and hosted time-series collection remain environment-specific.


## 2026-08-27 — Agent-assignment performance review

### Added

- Added `orville_core/assignment_review.py` with a bounded aggregate analyzer comparing safe assignment labels with terminal task outcomes, failure rates, verification failures, attempt means, and duration means.
- Exported `AssignmentStats` and `review_assignment_performance` through `orville_core.__init__`.
- Added `docs/AGENT_ASSIGNMENT_REVIEW.md` documenting review method, evidence boundaries, security and fairness limits, and improvement follow-up.
- Added `tests/test_assignment_review.py` covering aggregate outcomes, terminal-run filtering, secret-safe output, bounded labels, and input handling.

### Validation

Three focused assignment-review tests and Python compilation of the analyzer and tests passed. Public package export validation passed. The report does not rank individuals, infer causality, assign blame, or automatically reassign agents. No credentials, external services, or destructive actions were used.

## 2026-08-27 — Worker startup creation-readability gate

Added an opt-in `--validate-create-readability` gate for CLI runs above three concurrent tasks. The worker creates one harmless private diagnostic task, retries `task.detail` on HTTP 404 and transient failures with bounded `--validation-retries` and `--validation-interval` controls, and fails closed before polling existing tasks if the diagnostic task remains unreadable. Added `tests/test_worker_creation_validation.py`; 14 focused tests and Python compilation passed. The scheduled worker remains at `--max-active 3` until upstream task visibility is fixed.


## 2026-08-27 — Readiness report update

### Added

- Added `docs/READINESS_REPORT.md` reflecting current architecture, local validation, target readiness, security and observability controls, release gates, known blockers, and environment-owned limitations.
- Added `tests/test_readiness_report.py` covering report domains, target classifications, blocker disclosure, reproduction commands, and secret-safe wording.

### Validation

Four focused readiness-report tests passed, Python compilation passed, and a precise secret-pattern scan passed. The report explicitly records the full-suite collection blocker in `tools/orville_manus_worker.py` and the approval blocker on cleanup. No credentials, external services, or destructive actions were used.


## 2026-08-27 — Prioritized backlog

### Added

- Added `config/priority-backlog.json` with traceable existing TODO records and explicit status, priority, impact, effort, risk, dependencies, acceptance evidence, and blocker fields.
- Added `docs/PRIORITIZED_BACKLOG.md` defining scoring, dependency and blocker overrides, lifecycle states, review cadence, evidence retention, and security boundaries.
- Added `tests/test_prioritized_backlog.py` covering schema vocabulary, score bounds, TODO traceability, dependency metadata, blocker safeguards, and secret-safe catalog content.

### Validation

Three focused backlog tests, JSON parsing, and Python compilation passed. One initial traceability mismatch was corrected by aligning the integration-readiness record with the exact existing TODO wording. No tasks were created, credentials used, or destructive actions performed.


## 2026-08-27 — Milestone roadmap review

### Added

- Added `docs/MILESTONE_ROADMAP_REVIEW_2026-08-27.md` as an equivalent milestone review covering completed-local work, conditional target readiness, priorities, dependencies, risks, blockers, acceptance gates, and review cadence.
- Added `tests/test_milestone_roadmap_review.py` covering review sections, status areas, priorities, blockers, safety boundaries, and maintenance evidence.

### Validation

Four focused milestone-review tests passed, Python compilation passed, and a precise secret-pattern scan passed. The review preserves the full-suite collection blocker and cleanup approval blocker rather than treating either as resolved. No credentials, external services, or destructive actions were used.


## 2026-08-27 — GUI-to-engine API contract

### Added

- Added `docs/GUI_ENGINE_API_CONTRACT.md` defining versioned request/response envelopes and ownership boundaries for objectives, task graphs, runs, checkpoints, providers, local models, verification records, artifacts, approvals, and event streams.
- Documented engine-controlled state transitions, authentication and authorization, approval separation, redacted errors and audit records, idempotency, bounded event replay, degraded dependencies, and additive compatibility.
- Added `tests/test_gui_engine_api_contract.py` covering resource coverage, envelopes, state/security boundaries, event and error behavior, version compatibility, and secret exclusions.

### Validation

Three focused GUI-to-engine contract tests and Python compilation passed. Two initial wording mismatches were corrected in the tests without changing the contract. Authenticated backend bridging and GUI action wiring remain separate implementation items. No credentials, external services, or destructive actions were used.


## 2026-08-27 — Authenticated GUI backend bridge

### Added

- Documented the existing FastAPI GUI bridge in `docs/GUI_BACKEND_BRIDGE.md`, including authentication, authorization, request validation, CORS, rate limiting, redacted audit logging, safe errors, and deployment boundaries.
- Added `tests/test_gui_backend_bridge.py` covering bridge controls, synthetic audit redaction, documentation boundaries, and credential-safe contract content.

### Validation

Four focused bridge tests passed, API and audit modules compiled successfully, and the documentation secret-pattern scan passed. No external credentials, services, accounts, or destructive operations were used.

## 2026-08-27 — Autonomous TODO completion workflow

Strengthened the Manus worker continuation prompt to require one-item-at-a-time claims, focused branches when Git metadata exists, tests and compilation before completion, synchronized TODO/state/task-graph/changelog evidence, and explicit approval gates for external changes. Added `docs/AUTONOMOUS_TODO_WORKFLOW.md` and prompt-contract coverage. The attached directory has no `.git` metadata or remote, so branch, commit, and pull-request delivery remain unavailable there. Validation: 15 focused tests passed and Python compilation passed.


## 2026-08-27 — Real-time execution events

### Added

- Documented authenticated polling and resumable SSE delivery in `docs/REALTIME_EXECUTION_EVENTS.md`.
- Added `tests/test_realtime_execution_events.py` covering route exposure, sequence ordering, cursor resume, terminal behavior, safe reconciliation, and credential-safe contract content.

### Validation

Four focused event-contract tests passed, API and test Python compilation passed, and the documentation secret-pattern scan passed. No external credentials, providers, browser sessions, or live endpoints were used.


## 2026-08-27 — GUI model and provider controls

### Added

- Added `docs/GUI_MODEL_CONTROLS.md` documenting model catalog, local-model import and activation, provider health, privacy-aware routing, fallback, licensing, provenance, and GUI safety behavior.
- Added `tests/test_gui_model_controls.py` covering existing API route contracts, required control coverage, safety boundaries, and verification paths.

### Validation

Four focused GUI model-control tests passed. API, local-model, provider-feature, routing, and test modules compiled successfully. Forty-five related GUI/model/provider/routing/readiness regression tests passed, and the documentation secret-pattern scan passed. Git metadata and a remote were unavailable, so no branch, commit, or pull request was created.


## 2026-08-27 — GUI-to-engine action wiring

### Added

- Added `GUI_ENGINE_ACTIONS` and `build_engine_action_request` in `windows_gui.py` to centralize validated, URL-encoded route construction for objective creation, execution/resume/retry, cancellation, approvals, checkpoint reads, verification reads, and artifact listing.
- Connected execution-monitor controls to the shared action builder and retained the explicit local boundary that “Pause monitor” stops polling rather than pausing backend execution.
- Added `docs/GUI_ENGINE_ACTION_WIRING.md` documenting action mappings, engine-owned state, read projections, security boundaries, and current API limitations.
- Added `tests/test_gui_action_wiring.py` covering requested actions, routes, payloads, URL encoding, and fail-closed validation.

### Validation

Focused action-wiring, backend-bridge, and GUI-engine contract tests passed (11 total). Python compilation passed for `windows_gui.py` and `tests/test_gui_action_wiring.py`. No credentials, external services, or destructive actions were used. The repository copy is not a Git working tree, so Git diff/status validation is unavailable.

## 2026-08-27 — Explicit all-edits autopilot policy

### Added

- Added `--allow-all-edits` and `ORVILLE_ALLOW_ALL_EDITS=1` for explicit approval of agent edits across source, tests, configuration, documentation, and control files.
- Kept `TODO.md` worker-owned and preserved separate approval gates for credentials, external side effects, pushes, and pull requests.
- Added regression coverage for the expanded editing prompt.

### Validation

Five focused TODO-automation tests and Python compilation passed. No external actions were performed.

## 2026-08-27 — Automatic roadmap advancement

Updated the worker continuation prompt so each completed and validated one-item turn explicitly finishes for the next worker cycle to select the next eligible unchecked roadmap item. Duplicate-claim prevention, validation gates, state synchronization, and approval boundaries remain enforced. Validation: 15 focused worker tests passed and Python compilation passed.


## 2026-08-27 — Automatic TODO continuation activated

### Changed

- Enabled the existing Windows Scheduled Task `Orville Manus Todo Worker` with its one-minute cadence and absolute Orville repository path.
- Confirmed the worker is configured for up to three existing task threads and resumes the same thread with exactly one next unchecked TODO item after a stopped turn.
- Documented the completion gate requiring claim-before-work, focused code/tests validation, state/changelog synchronization, and TODO `[x]` only after validation evidence agrees.

### Boundaries

- No replacement Manus tasks were created during activation, and no live credential call was made by this setup action.
- The attached repository has no Git metadata, so branch, commit, push, and pull-request delivery remain unavailable locally; this is recorded rather than bypassed.


## 2026-08-27 — Artifact storage and lifecycle controls

### Added

- Extended `orville_core/artifacts.py` with root-bound metadata registration, digest-based durable version history, bounded text previews, metadata-only binary previews, manifest isolation, and non-destructive retention planning.
- Added authenticated API routes in `orville_core/api.py` for artifact preview, version history, retention planning, listing, creation, and download.
- Added `docs/ARTIFACT_STORAGE.md` and `tests/test_artifact_storage.py`.

### Validation

Four focused artifact tests passed and changed-module Python compilation passed. The broader suite reported 747 passed and 3 unrelated pre-existing connector/shell API failures; those remain release-triage blockers. No credentials, external services, deletion, or other destructive actions were used. Retention mutation remains approval-gated and plan-only.


## 2026-08-27 — Persistent observability and release evidence

### Added

- Added `orville_core/release_thresholds.py` with validated, deterministic release decisions over normalized health summaries.
- Added `config/release-thresholds.example.json` with non-secret defaults for sample sufficiency, error rate, P95 latency, saturation, security findings, business health, and release quality.
- Added `docs/OBSERVABILITY_EVALUATION_RELEASE_THRESHOLDS.md` describing persistent redacted traces, bounded metrics, retained evaluation fixtures, security regression coverage, release thresholds, and deployment-owned limitations.
- Added `tests/test_observability_release_evidence.py` covering JSONL trace persistence/redaction, retained evaluation and security fixtures, and threshold pass/fail behavior.

### Validation

Focused observability, evaluation, security, and threshold checks passed (23 tests). Python compilation passed for the affected modules and test module, and the threshold profile parsed as valid JSON. No credentials, external services, or deployment mutations were used.


## 2026-08-27 — Standalone release workflows

### Added

- Added `tools/standalone_release.py` with plan-first package, install, upgrade, migrate, rollback, and deployment workflows that run without Manus-specific services.
- Added deterministic forward-only configuration migration to version 1, versioned data backup and isolated restore primitives, explicit `--execute` mutation gating, and target delegation to the existing deployment preflight/smoke workflow.
- Added `docs/STANDALONE_RELEASE_WORKFLOWS.md` and `tests/test_standalone_release.py`.

### Validation

Four focused release-workflow tests passed, Python compilation passed, package plan JSON passed, and a local wheel build completed successfully. The broader suite completed with 747 passing tests and 3 unrelated pre-existing connector/shell API failures. No credentials, external deployment, deletion, account changes, or production mutations were used.


## 2026-08-27 — Clean-environment product validation

Validated the standalone product shape across three credential-free scenarios: configured cloud-shaped API behavior, local endpoint/provider routing behavior, and no-provider safe fallback behavior. The selected scenario suite passed 55 tests with one non-product test-client compatibility warning. Added `docs/CLEAN_ENVIRONMENT_VALIDATION.md` and retained sanitized evidence in `artifacts/clean-environment-validation-2026-08-27.json`. No live provider calls, credentials, deployments, or destructive actions were used; live provider availability, packaged installer execution, production networking, and multi-replica deployment remain environment-owned limitations.


## 2026-08-27 — Roadmap heading normalization

### Changed

- Renumbered the primary roadmap section sequence so Phase 5, Phase 6, Phase 6A, and Phase 7 use sections 10, 11, 11A, and 12 respectively, restoring a unique ordered sequence through Phase 12.
- Aligned GUI and document subsection prefixes with their normalized parent sections without changing task semantics, status markers, or historical backlog sections.
- Added `tests/test_todo_heading_normalization.py` to enforce primary phase ordering, subsection alignment, and completion-marker integrity.

### Validation

Three focused heading tests and six TODO-automation regression tests passed. Python compilation passed for the new test module. The repository is not a Git worktree, so no branch, commit, or pull request was created.


## 2026-08-27 — Roadmap phase and increment separation

Separated broad capability phases from implementation increments so provider work is tracked under Phase 2.7, environment reliability under Phase 3.1–3.3, and media work under Phase 6.2. Added `config/roadmap-phase-increments.json`, `docs/ROADMAP_PHASE_INCREMENT_MAP.md`, and `tests/test_roadmap_phase_increments.py`. Nine focused roadmap, heading-normalization, and backlog tests passed; Python compilation and JSON parsing passed. No runtime provider or media behavior changed.


## 2026-08-27 — Machine-readable roadmap task identifiers

### Added

- Added deterministic `TODO-xxxxxxxxxxxx` markers to every actionable checklist record in `TODO.md`.
- Added `tools/assign_todo_ids.py` for idempotent local regeneration while preserving status markers and task text.
- Added `docs/ROADMAP_TASK_IDENTIFIERS.md` and `tests/test_todo_identifiers.py` covering complete coverage, uniqueness, format, idempotence, and status preservation.

### Validation

Twelve focused tests covering identifiers, heading normalization, and TODO automation passed. Python compilation passed for the new utility and tests. No credentials, network calls, Git operations, or destructive actions were used.


## 2026-08-27 — Priority backlog metadata completeness

Normalized all four existing priority-backlog records with explicit status, owner, dependencies, reproducible acceptance tests, and artifact references. Advanced `config/priority-backlog.json` to schema version 1.1, updated `docs/PRIORITIZED_BACKLOG.md`, and strengthened `tests/test_prioritized_backlog.py`. Six focused tests passed, along with Python compilation, JSON validation, and artifact-reference existence checks. No new roadmap task or runtime behavior was introduced.


## 2026-08-27 — Deterministic workflow execution policy

### Added

- Added explicit `deterministic` and `agentic` workflow-step modes in `orville_core/automation.py`.
- Added fail-closed policy validation requiring deterministic implementations for `safety_critical`, `authorization`, `validation`, `persistence`, and `artifact_integrity` categories.
- Added a separate agentic-handler registry so agentic steps cannot silently fall back to deterministic handlers.
- Added `docs/WORKFLOW_EXECUTION_POLICY.md` and `tests/test_workflow_execution_policy.py`.

### Validation

Five focused policy tests and four existing automation/scheduled-workflow regression tests passed. Python compilation passed for the changed automation module and new tests. No external services, credentials, approvals, or destructive actions were used.


## 2026-08-27 — Durable operation checkpoints

### Added

- Added secret-safe `OperationCheckpoint` records to checkpoint schema version 2, preserving compatibility with schema version 1 files.
- Added durable before/after records for serial and parallel agent, tool, model, approval, artifact, and generic task operations; approval resolution records its after boundary before resumed execution.
- Added public export, focused tests, and `docs/OPERATION_CHECKPOINTS.md`.

### Validation

Five focused operation-checkpoint tests, four existing automation tests, and 18 discovered workflow/acceptance/core checkpoint regressions passed. Python compilation passed for the changed models, engine, package exports, and tests. One initial guessed test-path command was corrected after those filenames were not present; no product failure resulted. No credentials, external services, or destructive actions were used.


## 2026-08-27 — Execution-record known limitations

Added structured limitation categories to the reusable Standard Execution Record Template: scope, environment/provider, validation, and unresolved risks/follow-up dependencies. Added `tests/test_execution_record_template.py`; two focused tests and Python compilation passed. The checklist remains a template placeholder for future records and is not treated as a product milestone.
