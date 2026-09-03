# Orville — Remaining TODO Roadmap

This file intentionally contains only work that is unresolved, blocked, or not yet verified. Completed items remain preserved in the timestamped `TODO.backup-*.md` file in this directory. Do not mark an item complete without retained evidence, passing validation, and any required approval.

## Status markers

- `[ ]` — unresolved and actionable when prerequisites are available.
- `[!]` — blocked by a missing artifact, external service, deployment environment, approval, or other stated prerequisite.

## Current repository audit — 2026-08-27
- [!] Retain walkthrough-video source, validation evidence, and delivery metadata before closing its checklist. Reviewed and retained the explicit archival limitation in `docs/WALKTHROUGH_VIDEO_ARCHIVAL_COMPLIANCE_NOTE.md` and `docs/audits/WALKTHROUGH_VIDEO_REVIEW_2026-09-01.md`; the source, checksum, delivery metadata, or release-owner waiver is still unavailable, so closure remains blocked. <!-- task-id:TODO-f8a70d13fc97 -->
### 8.3A Optional Blackbox Integration
- [!] Obtain explicit Blackbox developer-support confirmation for third-party OAuth, device authorization, CLI token interoperability, scopes, redirect URIs, refresh-token behavior, rate limits, and redistribution requirements. Official support request submitted through `https://www.blackbox.ai/support`; remain blocked until the provider response is received and independently reconciled. Receipt: `artifacts/m12_18_external_submission_receipt_2026-08-27.md`. <!-- task-id:TODO-66fbf5bde1c2 -->
- [!] Add `blackbox.oauth` or device authorization only if Blackbox provides an official third-party flow with documented client registration and token semantics; otherwise do not label API-key entry as “Sign in with Blackbox.” <!-- task-id:TODO-a175285a1314 -->
- [!] If official OAuth/device authorization is confirmed, open the official authorization page, use state/PKCE protections where applicable, validate the callback, and store tokens securely. Blocked pending documented Blackbox third-party OAuth/device-authorization confirmation; no authorization page, callback, token, or external account was accessed. <!-- task-id:TODO-7146fe89cb35 -->
- [!] Complete the official Blackbox authentication decision for optional user-account connection and record evidence. Blocked: the existing public-source review found no documented official third-party OAuth/device flow, and external support confirmation cannot be obtained under the no-post/no-credential constraint. <!-- task-id:TODO-09dc84b7cc28 -->
- [!] Implement optional OAuth/device flow only if officially supported. Blocked: no officially supported Blackbox OAuth/device flow is documented or verified; API-key-only behavior remains enforced and the decision is recorded in the integration documentation and onboarding contract. <!-- task-id:TODO-419d48ee2bf1 -->
## 17. Phase 12 — Continuous Improvement
- [!] Remove obsolete dependencies, connectors, instructions, and artifacts. Blocked: repository rules require explicit confirmation before destructive deletion; candidate caches/tmp content require named-path review and retention checks. <!-- task-id:TODO-3f81d2a983e6 -->
## Verification
- [!] Requirements checked. Blocked: this checkbox is a reusable verification-template placeholder inside the Standard Execution Record Template, not an actionable roadmap task; it must remain unchecked for future execution records. <!-- task-id:TODO-1813c90c24df -->
- [!] Outputs inspected. Blocked: this checkbox is a reusable verification-template placeholder inside the Standard Execution Record Template, not an actionable roadmap task; it must remain unchecked for future execution records. <!-- task-id:TODO-42ada86910f9 -->
- [!] Tests or validation commands executed. Blocked: this checkbox is a reusable verification-template placeholder inside the Standard Execution Record Template, not an actionable roadmap task; it must remain unchecked for future execution records. <!-- task-id:TODO-9e65a63bd1d3 -->
- [!] Independent review completed. Blocked: this checkbox is a reusable verification-template placeholder inside the Standard Execution Record Template, not an actionable roadmap task; it must remain unchecked for future execution records. <!-- task-id:TODO-f7bf278e300e -->
### Known limitations
- [!] Final artifacts integrated and delivered. Blocked: this checkbox is a reusable verification-template placeholder inside the Standard Execution Record Template, not an actionable roadmap task; it must remain unchecked for future execution records. <!-- task-id:TODO-abc4b239dd1b -->
### 21.5 GUI quality gates
- [!] Test the GUI with keyboard-only navigation, screen readers, high zoom, reduced motion, high contrast, small screens, slow connections, and long-running operations. The executable `windows_gui.py` source has now been restored from the pre-refactor Git revision and GUI contract tests pass; live assistive-technology, browser/device, slow-connection, and long-operation validation remains blocked until a configured target environment is available. <!-- task-id:TODO-2db4ae3a211f -->
- [!] Add usability testing with first-time users for task creation, model setup, local model import, execution review, verification review, and artifact export. The GUI source has been restored and the protocol remains in `docs/USABILITY_TEST_PROTOCOL_2026-09-01.md`; participant sessions and device-based testing remain blocked pending an approved participant/device environment. <!-- task-id:TODO-49e3f6d26ee8 -->
## Current Integration Status — Finalization Pass
- [!] Production GUI bridge remains pending: durable identity and authorization scopes, CORS and rate-limit enforcement, backend run manager injection, artifact APIs, SSE/WebSocket push, and database-backed state. Local durable state, artifact APIs, event streaming, and in-memory safeguards are verified; production identity, deployed run-manager binding, external audit sink, and deployment topology remain unavailable. <!-- task-id:TODO-e365c91ee53b -->
- [!] Final operational pass remains pending: OpenTelemetry export, evaluation harness, security regression suite, packaging and migration workflows, deployment configuration, rollback procedures, and clean-environment acceptance testing. Local compatibility, evaluation, security, packaging-policy, and migration contracts are verified, but external export, deployment, rollback-target, and clean-environment evidence remain unavailable. <!-- task-id:TODO-32baa69a5473 -->
## Finalization Pass Status
- [!] Provide a production identity provider, scoped authorization, TLS, deployment secrets, CORS allowlist, and audit-log sink. Added fail-closed `orville_core/production_config.py` and `tests/test_production_config.py` for the required boundary checks; 77 focused persistence, API, evaluation, GUI, visual, tracing, metadata, and configuration tests passed with one non-blocking Starlette/httpx warning. Production completion remains blocked pending a real identity provider, deployment secret reference, TLS endpoint, explicit CORS origins, and audit sink. <!-- task-id:TODO-23b12a217ff3 -->
- [!] Inject real model-backed handlers and run manager into the deployed API; no fake generation handlers are permitted. Local provider routing, capability negotiation, model lifecycle, and runtime-control contracts are present and covered by the verified test suite, but deployment completion remains blocked until a real provider credential/configuration and deployed run-manager binding are supplied; no fake generation path was enabled. <!-- task-id:TODO-41dfe16627d4 -->
- [!] Implement SSE/WebSocket event push, full local-model runtime activation, sandboxed process execution, and hardware-aware resource checks. Verified the local SSE/event, SQLite persistence, local-model, runtime-control, capability, provider, security, and health contracts with 58 passing tests; production completion remains blocked because no approved live sandbox adapter, GUI/device target, GPU isolation environment, or deployed runtime is available. <!-- task-id:TODO-e4e9152d3c61 -->
- [!] Complete production acceptance, security, accessibility, performance, repository-level code-generation evaluation, packaging, deployment, rollback, and disaster-recovery tests. Added `docs/FINAL_ACCEPTANCE_REPORT_2026-09-02.md`; full local suite recorded 838 passing tests, 4 failures, 27 setup errors, 6 passing subtests, and one non-blocking warning. Remaining failures/errors are concentrated in missing recovered-checkout GUI files, while production identity, TLS, provider credentials, live sandbox, device testing, deployment topology, and rollback targets remain unavailable. <!-- task-id:TODO-9d23783f4060 -->
## Roadmap Completion Pass — Verified Update
- [ ] Connect deployed GUI to a configured backend URL and authenticated token through a server-side secret mechanism. <!-- task-id:TODO-c4ddd8a16896 -->
- [ ] Complete external identity, scoped authorization, TLS, distributed rate limiting, and durable audit logging. <!-- task-id:TODO-2d2b1715895f -->
- [ ] Complete real model runtime injection, sandboxed local process execution, resource validation, and provider capability negotiation. <!-- task-id:TODO-007a1807f0ec -->
- [ ] Run clean-environment acceptance and deployment validation after choosing the target hosting topology. <!-- task-id:TODO-494d5e4a3c5c -->
## Instruction-First Agentic Code Completion
- [x] Audit the current opening screen and objective composer flow. Reviewed the restored `windows_gui.py` opening screen, composer, API readiness state, accessibility entry points, and workflow help; the composer now presents agentic instructions before task creation. <!-- task-id:TODO-06b14744f832 -->
- [x] Make the initial view request agentic code-completion instructions before showing the workspace. The restored Signal Room composer now leads with `Instructions`, explains the plan/work/check flow, and sends `workflow_mode=agentic_code_completion` on run creation; focused GUI validation passed 36 tests. <!-- task-id:TODO-30c6c3b3d12b -->
- [x] Add clear fields for task instructions, repository or project context, expected changes, and acceptance criteria. Added labeled `Instructions`, `Repository or project context`, and `Acceptance criteria` controls to `windows_gui.py`; values are included in the structured create-run request without exposing credentials. Compilation and 36 focused GUI tests passed. <!-- task-id:TODO-a272ae63acef -->
- [x] Launch the created agentic run directly into the live code-generation viewer. Updated `windows_gui.py` so a successful create-run response with a `run_id` opens the existing bounded execution monitor in live code-generation mode, preselects the run, immediately refreshes status/events, and continues 1.5-second polling with pause/recovery controls; compilation passed and 23 focused GUI/workflow tests passed. <!-- task-id:TODO-8064ebccb62c -->
- [ ] Preserve access to the Signal Room workspace, Integrations, runs, artifacts, state, events, and API docs. <!-- task-id:TODO-b1e88a5c21d9 -->
- [ ] Verify empty, validation, success, error, and reconnect states. <!-- task-id:TODO-ab4e74aeb309 -->
- [ ] Save a verified preview checkpoint. <!-- task-id:TODO-0b58db0f4139 -->
## Repository-Aware Code Completion
- [ ] Save a repository-aware checkpoint. <!-- task-id:TODO-ac234124eb89 -->
## Restored Orville Shell Status
- [ ] Save a verified restored-shell checkpoint. <!-- task-id:TODO-9746b1729935 -->
## Runs Walkthrough Video
- [ ] Define the complete run lifecycle narrative and scene order. <!-- task-id:TODO-582e0f5dec5a -->
- [ ] Prepare Signal Room visual references and instructional overlays. <!-- task-id:TODO-92c9029c2bf1 -->
- [ ] Generate a walkthrough covering intake, planning, provider generation, live code, verification, approvals, artifacts, failure, and repair. <!-- task-id:TODO-c5944ab8d2c5 -->
- [ ] Review the video for readable labels, sequence completeness, and factual alignment with the current Orville implementation. <!-- task-id:TODO-cc4006312df6 -->
- [ ] Deliver the final video artifact. <!-- task-id:TODO-130df39163f5 -->
## Broad Manus-Like Capability Expansion
- [ ] Audit existing Orville capabilities against research, browser, coding, workspace, memory, artifact, automation, connector, scheduling, notification, deployment, and observability categories. <!-- task-id:TODO-d22666b3ed35 -->
- [ ] Define standalone Windows equivalents and explicitly document proprietary Manus capabilities that cannot be reproduced literally. <!-- task-id:TODO-3ca9e5661f74 -->
- [ ] Implement the highest-value missing agent runtime, browser/research, workspace, memory, approval, and automation foundations. <!-- task-id:TODO-ef21104055e5 -->
- [ ] Implement document, spreadsheet, presentation, data, media, and code artifact workflows. <!-- task-id:TODO-6f0f192e0f8d -->
- [ ] Implement connectors, schedules, notifications, deployment helpers, and observability equivalents. <!-- task-id:TODO-e54e5165107f -->
- [ ] Integrate new capabilities into Signal Room without removing existing menus or workflows. <!-- task-id:TODO-6c093406ae52 -->
- [ ] Verify security, compatibility, end-to-end behavior, clean-host operation, and executable packaging. <!-- task-id:TODO-e4d256e35cd9 -->
- [ ] Save a broad-capability checkpoint and deliver a parity report. <!-- task-id:TODO-7d86fda66f3f -->
## Safe Browser Session Adapter
- [ ] Audit current browser adapter, security policy, API initialization, and GUI capability status. <!-- task-id:TODO-14b1a51a18bc -->
- [x] Define browser session lifecycle, domain allowlist, takeover, approval, and audit contracts. Verified the existing `orville_core/browser.py` lifecycle, normalized domain allowlist, takeover approval, persistence/recovery, and audit behavior with `tests/test_browser.py`, `tests/test_browser_persistence.py`, `tests/test_browser_relay.py`, `tests/test_connector_policy.py`, and `tests/test_security.py`; 14 tests passed. <!-- task-id:TODO-effd7a331bf6 -->
- [x] Implement a local browser-session adapter with read-only defaults and fail-closed navigation. Verified `orville_core/browser.py` read-only navigation defaults, domain allowlist enforcement, explicit approval for takeover/form/download actions, bounded excerpts, and safe shutdown/recovery behavior with the browser contract suite. <!-- task-id:TODO-fe9759a5f934 -->
- [x] Add authenticated session, allowlist, navigation, takeover, approval, and audit routes. Verified authenticated browser-relay pairing, session listing, action queueing, navigation validation, polling, and revocation routes in `orville_core/api.py` and `orville_core/browser_relay.py`; browser and relay regression tests passed. <!-- task-id:TODO-8aea5ebfd639 -->
- [ ] Integrate browser controls and takeover prompts into Signal Room. <!-- task-id:TODO-0f6019a14705 -->
- [!] Verify blocked domains, allowed navigation, sensitive-action approval, takeover state, audit records, and responsive UI behavior. Browser policy, allowlist, approval, takeover, and audit behavior passed the 14-test contract suite; responsive UI and live browser/device validation remain blocked by the missing complete GUI source and configured browser/device environment. <!-- task-id:TODO-c4d9d0ccf9c9 -->
- [x] Save a browser-session adapter checkpoint. Added `docs/BROWSER_SESSION_ADAPTER_CHECKPOINT.md` with verified behavior, security boundaries, test evidence, and remaining environment-owned limitations. <!-- task-id:TODO-a8cd1e62d28c -->
## Browser Actions, Recovery, and Run Citations
- [x] Audit browser sessions, action state, run events, artifact storage, and shutdown lifecycle. Added `orville_core/browser_evidence.py` to link run/session/artifact identifiers and project bounded redacted audit events; added `tests/test_browser_evidence.py`. Focused validation: 20 browser, artifact, and security tests passed and Python compilation passed. <!-- task-id:TODO-2f13d5e2c921 -->
- [x] Define approval records for form submissions and file downloads with redaction rules. Added `orville_core/browser_approvals.py` with scoped action records, field-name-only capture, TTL expiry, explicit decisions, and scope digests; added `tests/test_browser_approvals.py`. <!-- task-id:TODO-8dd98903dd3a -->
- [x] Record browser actions and implement approval-gated form submission and download operations. Verified the existing browser adapter records approval-required and approved action events, requires explicit approval for form/download side effects, and preserves bounded audit detail; browser, approval, relay, artifact, and security tests passed. <!-- task-id:TODO-aa8e3d054349 -->
- [x] Persist browser sessions and recover interrupted sessions safely after restart or shutdown. Verified `BrowserSessionManager` atomic metadata persistence, shutdown handling, recovered status, takeover requirement, and explicit browser-handle restart boundary with the browser persistence tests. <!-- task-id:TODO-641133423429 -->
- [x] Extract page titles, readable text, metadata, and downloaded-source references. Added bounded `BrowserSession.extract_page_metadata()` for title, canonical URL, selected metadata, visible text, and source reference; added `tests/test_browser_metadata.py`. Focused browser validation: 25 tests passed and Python compilation passed. <!-- task-id:TODO-b213e9e47c35 -->
- [x] Attach source records and citations to agent runs and generated artifacts. Added `orville_core/source_citations.py` with absolute HTTP(S) validation, bounded quotes/values, verification states, deterministic source hashes, and run/artifact attachment; added `tests/test_source_citations.py`. Focused validation: 27 browser, citation, artifact, and security tests passed and Python compilation passed. <!-- task-id:TODO-1bfd83e7a066 -->
- [ ] Integrate action approvals, recovery state, and citations into Signal Room. The missing `windows_gui.py` and GUI packaging specifications have been restored from the pre-refactor Git revision; the UI-safe browser projection and 30 contract tests pass, but wiring these controls into the actual Signal Room window remains the next implementation task. <!-- task-id:TODO-f210cb47fc7a -->
- [ ] Verify security, persistence, clean shutdown, run linkage, and frontend behavior. <!-- task-id:TODO-e1bada1fe5df -->
- [ ] Save a verified browser workflow expansion checkpoint. <!-- task-id:TODO-5c65799963ea -->
## Current execution — Windows release validation
- [ ] Save a final project checkpoint and deliver the executable path and validation results. <!-- task-id:TODO-36f54f90723f -->
## Current execution — Stable Horde multimodality upgrade
- [ ] Save a checkpoint and document supported capabilities and limitations. <!-- task-id:TODO-96de5d667406 -->
## Current Task — Hub Transfer Retry and Backoff Telemetry
- [ ] Rebuild and validate the Windows executable. <!-- task-id:TODO-c5c4c75ae716 -->
## Current Task — Use the Manus Connector Catalog
- [ ] Rebuild and validate the Windows executable and connector execution smoke flow. <!-- task-id:TODO-2ff572f86602 -->
- [ ] Save a final checkpoint and deliver the connector usage status. <!-- task-id:TODO-ff539eb1ab4c -->
## Current Task — Connector Operation Discovery Demo Video
- [ ] Define the product-demo sequence for selecting a connector and discovering operations. <!-- task-id:TODO-be0242b177cf -->
- [ ] Generate a concise Signal Room demo video. <!-- task-id:TODO-c01fa63cf902 -->
- [ ] Review the generated video for sequence clarity and deliver it. <!-- task-id:TODO-1ee7698d3d1b -->
## Current Task — Animated Connector Discovery Prototype
- [ ] Define prototype states for connector selection, operation discovery, permissions, request preview, and approval. <!-- task-id:TODO-ab0a0c8e9170 -->
- [ ] Implement the animated HTML prototype in the existing Signal Room preview. <!-- task-id:TODO-4c01ab00ce15 -->
- [ ] Verify interactions, animation timing, accessibility, and mobile layout. <!-- task-id:TODO-852c793f898d -->
- [ ] Save a checkpoint and deliver the prototype. <!-- task-id:TODO-fd7cee87a475 -->
## Current Task — Connector Discovery Storyboard Images
- [ ] Define a coherent set of frames for connector selection, operation discovery, permissions, request preview, and approval. <!-- task-id:TODO-15d1f27d18d1 -->
- [ ] Generate the storyboard images with consistent Signal Room styling. <!-- task-id:TODO-757490a3dd86 -->
- [ ] Review image readability and deliver the set. <!-- task-id:TODO-3a932b25f7d8 -->
## Current Task — Windows Release Hardening
- [ ] Inspect launcher, PyInstaller spec, storage paths, and available Windows packaging tools. <!-- task-id:TODO-4288173a3678 -->
- [ ] Define user-data, portable-mode, migration, and recovery boundaries without changing the GUI. <!-- task-id:TODO-04d8c2bbc381 -->
- [ ] Add native application-window support using the existing web bundle. <!-- task-id:TODO-503692865ae2 -->
- [ ] Add dynamic local-port selection and communicate selected ports to the unchanged GUI. <!-- task-id:TODO-08a4ac853630 -->
- [ ] Add single-instance protection and orphan-process cleanup. <!-- task-id:TODO-f3332d113251 -->
- [ ] Add crash recovery diagnostics and repair-safe startup behavior. <!-- task-id:TODO-176b67390b6f -->
- [ ] Add installer and portable ZIP build scripts. <!-- task-id:TODO-2a9ad3f40990 -->
- [ ] Add update-safe data migrations and release documentation. <!-- task-id:TODO-4ff4a3d9ed9c -->
- [ ] Add optional code-signing configuration without embedding credentials. <!-- task-id:TODO-d7c301ab61bb -->
- [ ] Run backend, packaged, installer, portable, and recovery validation. <!-- task-id:TODO-177c92c6bc76 -->
- [ ] Save a final checkpoint and deliver the hardened release artifacts. <!-- task-id:TODO-44bf404991ca -->
## 18.1 Roadmap rules and non-goals
- [ ] Preserve the existing Signal Room visual system and native Windows shell; new capabilities must extend existing surfaces rather than replace the GUI. <!-- task-id:TODO-3b7209f9a1b2 -->
- [ ] Preserve local-first operation. Every cloud-dependent feature must have a documented local mode, an explicit optional hosted mode, or a clear unsupported state. <!-- task-id:TODO-9168feae91d7 -->
- [ ] Exclude Cloud Browser infrastructure from this roadmap. Implement only local browser access, local extension relay, takeover, allowlists, approvals, audit, and recovery. <!-- task-id:TODO-137d52d0e669 -->
- [ ] Never represent a catalogued connector as operational until its authentication, capability discovery, operation schema, and invocation tests pass. <!-- task-id:TODO-12699b27c498 -->
- [ ] Treat credentials, OAuth tokens, cookies, files, prompts, browser content, connector responses, and generated code as separate trust domains. <!-- task-id:TODO-9a8a0493d529 -->
- [ ] Require independent verification for every material feature, including security tests, restart tests, failure-path tests, and user-visible acceptance tests. <!-- task-id:TODO-4a9a6027b02b -->
- [ ] Keep all new services runnable outside Manus through documented Python/Node commands, configuration files, migration steps, and test fixtures. <!-- task-id:TODO-df7659765e90 -->
- [ ] Document cost boundaries before enabling any hosted provider, external API, persistent relay, notification channel, or paid model. <!-- task-id:TODO-485c46140552 -->
### A1. Task and message model
- [ ] Add a durable `TaskThread` model with stable task ID, project ID, agent ID, parent task ID, status, stop reason, active model, connector set, skill set, structured-output state, timestamps, and recovery metadata. <!-- task-id:TODO-6fa537929800 -->
- [ ] Add an append-only `TaskMessage` model for user messages, assistant messages, tool calls, tool results, status updates, questions, approvals, errors, artifacts, and citations. <!-- task-id:TODO-3cbf6cb3907b -->
- [ ] Add explicit statuses: `planned`, `ready`, `running`, `waiting`, `stopped`, `failed`, `cancel_requested`, `cancelled`, and `recovering`. <!-- task-id:TODO-498262667bdc -->
- [ ] Add explicit stop reasons: `finish`, `ask`, `approval_required`, `cancelled`, `error`, `timeout`, and `policy_blocked`. <!-- task-id:TODO-74491cf31575 -->
- [ ] Implement `send_message`, `list_messages`, `task_detail`, `stop`, `resume`, and `retry` operations. <!-- task-id:TODO-2f7fd076f533 -->
- [ ] Preserve full event history across process restart and migration. <!-- task-id:TODO-91309b9bf064 -->
- [ ] Add optimistic concurrency/version numbers so duplicate user actions cannot advance a task twice. <!-- task-id:TODO-d436adee1bc5 -->
### A2. Waiting and confirmation protocol
- [ ] Define a typed `WaitingRequest` with event ID, event type, description, JSON Schema, risk classification, requested permissions, expiry, and originating tool. <!-- task-id:TODO-73f758acca12 -->
- [ ] Implement `ask_user` for normal questions and `confirm_action` for every other approval-gated event. <!-- task-id:TODO-b2e161153474 -->
- [ ] Validate confirmation payloads against the stored JSON Schema before execution. <!-- task-id:TODO-ff1fa14edbd6 -->
- [ ] Add confirmation types for terminal execution, file writes, repository changes, browser takeover, form submission, download, connector invocation, account changes, payments, deployment, secret entry, and model installation. <!-- task-id:TODO-98304c36573b -->
- [ ] Add “allow once”, “allow for task”, and “always allow for this safe scope” policies with explicit expiry and revocation. <!-- task-id:TODO-28556f5c48d6 -->
- [ ] Prevent a rejected or expired confirmation from silently advancing the task. <!-- task-id:TODO-daab8b14d76c -->
- [ ] Add UI rendering for schema-driven confirmation forms with safe defaults and irreversible-action warnings. <!-- task-id:TODO-22426565b67e -->
### A3. Acceptance criteria
- [ ] A task can receive at least three follow-up messages without losing context. <!-- task-id:TODO-96d7d017bd3d -->
- [ ] A task paused for a question remains paused until a user response is received. <!-- task-id:TODO-9e32da9c5eed -->
- [ ] A task paused for an approval resumes only after a valid schema-conforming approval. <!-- task-id:TODO-4c43d670ea10 -->
- [ ] Restarting the executable during `running` or `waiting` restores the correct state without duplicate tool execution. <!-- task-id:TODO-025ff0a48fdc -->
- [ ] Every state transition is visible in the activity timeline and persisted in the audit log. <!-- task-id:TODO-0adcc6eccc27 -->
## 18.3 Phase B — Agent registry and subtask runtime [P0]
- [ ] Create an `AgentProfile` model with stable ID, name, description, system instructions, model policy, memory scope, skill set, connector set, tool permissions, risk ceiling, and enabled state. <!-- task-id:TODO-9d7d09e856b2 -->
- [ ] Convert the existing Personal Agent into a real registry-backed agent with a persistent main thread. <!-- task-id:TODO-17c5d57b0079 -->
- [ ] Add agent creation, update, clone, disable, delete, and inspect operations. <!-- task-id:TODO-1fb8710876d3 -->
- [ ] Add child-task creation with parent/child relationships, bounded depth, budgets, deadlines, and cancellation propagation. <!-- task-id:TODO-c19df709f36f -->
- [ ] Add subtask result contracts containing status, artifacts, citations, errors, metrics, and verification record. <!-- task-id:TODO-31c84b45fd9a -->
- [ ] Add parallel subtask execution with queue limits and explicit owned-path/resource claims. <!-- task-id:TODO-10ab06aacdd6 -->
- [ ] Add synthesis stages that cannot complete until required child tasks meet their verification policy. <!-- task-id:TODO-04f3cddca503 -->
- [ ] Add failure policies: retry child, skip optional child, pause for user, or fail parent. <!-- task-id:TODO-7a8257b4df0f -->
- [ ] Add per-agent tool and connector permission policies. <!-- task-id:TODO-a8cb2eca6214 -->
- [ ] Add tests for nested subtasks, cancellation, timeouts, retries, partial completion, and restart recovery. <!-- task-id:TODO-c9a6b437ef05 -->
## 18.4 Phase C — Skills system [P0]
- [ ] Define a skill package format containing metadata, `SKILL.md`, version, author, license, permissions, dependencies, entry points, and optional resources. <!-- task-id:TODO-ab0e7a72373f -->
- [ ] Implement local folder, ZIP, official package, and GitHub repository import. <!-- task-id:TODO-25cca32d5754 -->
- [ ] Validate package paths, archive traversal, symlinks, executable content, dependency declarations, and unsafe commands. <!-- task-id:TODO-64ca9d666974 -->
- [ ] Add static inspection and risk report before installation or first execution. <!-- task-id:TODO-b99c9c0d5ada -->
- [ ] Add skill registry with installed, disabled, update-available, incompatible, and quarantined states. <!-- task-id:TODO-2ec6a4e9dbe7 -->
- [ ] Implement version pinning, update checks, rollback, and uninstall. <!-- task-id:TODO-0bbfb331ac75 -->
- [ ] Implement progressive disclosure: metadata at startup, instructions on activation, resources on demand. <!-- task-id:TODO-50f760fa0f08 -->
- [ ] Add slash-command skill activation and task-level skill selection. <!-- task-id:TODO-5c876bdd8edf -->
- [ ] Add automatic skill recommendation only after user approval or explicit project policy. <!-- task-id:TODO-842abbc3266e -->
- [ ] Run skills inside the same sandbox, approval, timeout, network, and audit boundary as tools. <!-- task-id:TODO-a88bec283fe2 -->
- [ ] Add a skill authoring wizard that converts a verified workflow into a package. <!-- task-id:TODO-acf02b5c5603 -->
- [ ] Add malicious-skill fixtures and regression tests. <!-- task-id:TODO-5ba519c1f3a1 -->
### D1. Adapter contract
- [ ] Define a versioned `ConnectorAdapter` interface for metadata, authentication, refresh, revoke, health, capability discovery, operation schemas, invocation, pagination, uploads, downloads, error normalization, and rate limits. <!-- task-id:TODO-9584124bc31d -->
- [ ] Add connector states: `catalogued`, `supported`, `authorization_required`, `connected`, `expired`, `reauthorization_required`, `disabled`, `rate_limited`, `degraded`, and `unsupported`. <!-- task-id:TODO-c517cb4e86ad -->
- [ ] Store connector manifests separately from credentials. <!-- task-id:TODO-6f1fc4030571 -->
- [ ] Add official provider URLs, scopes, redirect URIs, API versions, and documentation references to each supported manifest. <!-- task-id:TODO-228958bdcebf -->
- [ ] Add per-operation risk class and approval policy. <!-- task-id:TODO-f8e8d7623a7a -->
- [ ] Add request/response schema validation and redaction rules. <!-- task-id:TODO-aad616397c9d -->
### D2. Initial provider set
- [ ] Implement and test Gmail. <!-- task-id:TODO-3a0a53cb11b0 -->
- [ ] Implement and test Google Calendar. <!-- task-id:TODO-2fce927e5d27 -->
- [ ] Implement and test Slack. <!-- task-id:TODO-6e1427fa5fcb -->
- [ ] Implement and test Notion. <!-- task-id:TODO-a1fd1d3696bb -->
- [ ] Implement and test GitHub. <!-- task-id:TODO-038b200edc38 -->
- [ ] Implement and test Microsoft Outlook Mail. <!-- task-id:TODO-63c490fdffb0 -->
- [ ] Implement and test Stripe in read-only mode first, then approved write actions. <!-- task-id:TODO-c09eb7147a17 -->
- [ ] Implement and test HubSpot or another CRM provider. <!-- task-id:TODO-619c76c15c70 -->
- [ ] Implement and test Zapier or n8n as an automation provider. <!-- task-id:TODO-c75af322e0a8 -->
- [ ] Add a generic OpenAPI/HTTP adapter for user-owned services with explicit allowlists. <!-- task-id:TODO-6f5b98ff5c09 -->
- [ ] Maintain the remaining catalog entries as catalogued or unsupported until real adapters exist. <!-- task-id:TODO-e9d3ad18bb16 -->
### D3. Auth and operations
- [ ] Support provider-specific OAuth2 authorization-code + PKCE. <!-- task-id:TODO-384b252565ab -->
- [ ] Support API-key, bearer, signed-request, and local endpoint authentication where appropriate. <!-- task-id:TODO-9336bd7b1aeb -->
- [ ] Add token refresh, expiry detection, revocation, reauthorization, and account labeling. <!-- task-id:TODO-0aaad601e8cb -->
- [ ] Add per-provider redirect/callback tests using local fixtures. <!-- task-id:TODO-2c4988fc1a18 -->
- [ ] Add provider-specific pagination, retry, rate-limit, and error handling. <!-- task-id:TODO-15b85b494a95 -->
- [ ] Add connector defaults at user, project, and task levels. <!-- task-id:TODO-0b0ca06cdd55 -->
- [ ] Implement explicit connector override, clear, and reuse semantics for follow-up task messages. <!-- task-id:TODO-d4a07f6a230f -->
- [ ] Add operation discovery and schema-driven invocation UI. <!-- task-id:TODO-23fc3fa9f479 -->
- [ ] Add audit records that never store raw credentials or authorization headers. <!-- task-id:TODO-2f153d906a94 -->
- [ ] Add connector health checks and “test connection” actions that do not perform mutations. <!-- task-id:TODO-c7232ee513b7 -->
## 18.6 Phase E — Durable scheduler [P0]
- [ ] Define schedule model with task template, project, agent, connector set, skill set, timezone, recurrence, next run, state, retry policy, concurrency policy, and missed-run policy. <!-- task-id:TODO-a925a97a87a0 -->
- [ ] Support one-time, interval, daily, weekday, weekly, monthly, and cron schedules. <!-- task-id:TODO-55304b438898 -->
- [ ] Add pause, resume, edit, clone, run-now, and delete actions. <!-- task-id:TODO-7f5ed0860a69 -->
- [ ] Persist schedules independently of the GUI process. <!-- task-id:TODO-b64eafcc5f8c -->
- [ ] Add worker leasing so only one process executes a scheduled run. <!-- task-id:TODO-958ea8edb0e5 -->
- [ ] Add catch-up, skip, and coalesce policies for missed runs. <!-- task-id:TODO-08d640ba2025 -->
- [ ] Add notifications for success, failure, waiting, approval, connector expiry, and repeated retries. <!-- task-id:TODO-19616374b701 -->
- [ ] Add schedule import/export and backup coverage. <!-- task-id:TODO-4d5dac1f67bf -->
- [ ] Test daylight-saving changes, clock skew, restart, sleep/wake, duplicate execution, and long-running tasks. <!-- task-id:TODO-c100593b6738 -->
## 18.7 Phase F — Webhooks and event delivery [P0]
- [ ] Add webhook endpoint registration, update, disable, rotate-secret, test, and delete operations. <!-- task-id:TODO-b7580c1bcccb -->
- [ ] Support local loopback callbacks and documented secure relay configuration. <!-- task-id:TODO-c6b0553d23f8 -->
- [ ] Validate webhook payloads and enforce maximum body size. <!-- task-id:TODO-a7906966f5d4 -->
- [ ] Add HMAC or asymmetric signature verification and timestamp/replay protection. <!-- task-id:TODO-b926f78466a3 -->
- [ ] Add idempotency keys and a deduplication store. <!-- task-id:TODO-13c9a3e6f8f1 -->
- [ ] Add exponential backoff with jitter, retry caps, dead-letter state, and manual replay. <!-- task-id:TODO-c68bcd54efd9 -->
- [ ] Add delivery history with status, latency, response code, retry count, and redacted error. <!-- task-id:TODO-da5fcb74b85d -->
- [ ] Add task-created, task-status-changed, task-waiting, task-stopped, artifact-created, connector-expired, and schedule-failed events. <!-- task-id:TODO-ce27bbaca694 -->
- [ ] Add webhook policy controls so external events cannot bypass approval gates. <!-- task-id:TODO-b3772650c637 -->
- [ ] Add fixture tests for duplicate, delayed, malformed, unsigned, and replayed events. <!-- task-id:TODO-793a72ec8797 -->
## 18.8 Phase G — Structured output [P0]
- [ ] Add JSON Schema input to task creation and follow-up messages. <!-- task-id:TODO-f9cae5b47aa8 -->
- [ ] Implement supported-subset validation before execution. <!-- task-id:TODO-77ec11f6ccc6 -->
- [ ] Enforce object root, `additionalProperties: false`, required fields, nesting depth, and supported types/keywords. <!-- task-id:TODO-e94cae43c25f -->
- [ ] Persist schema state as `armed`, `paused`, `consumed`, `failed`, or `rearmed`. <!-- task-id:TODO-ec188d72727c -->
- [ ] Extract only after a successful terminal completion. <!-- task-id:TODO-ea4e4f62a463 -->
- [ ] Preserve schema when a task pauses for user input. <!-- task-id:TODO-70a9d6eaf111 -->
- [ ] Return `{success, value, error}` with a schema-conforming zero-value fallback on extraction failure. <!-- task-id:TODO-53b5966018be -->
- [ ] Display structured results as JSON, table, downloadable artifact, and task event. <!-- task-id:TODO-42b5e4da8e01 -->
- [ ] Add schema fixtures for research extraction, code manifests, connector results, and data analysis. <!-- task-id:TODO-4a1ffb531500 -->
## 18.9 Phase H — Files and project knowledge bases [P1]
- [ ] Add managed file records with ID, filename, MIME type, size, hash, status, owner, project, task, created time, expiry, and deletion state. <!-- task-id:TODO-18b3944462f9 -->
- [ ] Implement safe local upload staging and optional S3-compatible storage abstraction. <!-- task-id:TODO-fbad5d40691b -->
- [ ] Add file type, size, archive, executable, and script policies. <!-- task-id:TODO-9bc20d365c65 -->
- [ ] Add resumable uploads, checksum verification, cleanup, and quota reporting. <!-- task-id:TODO-f85099e6d05b -->
- [ ] Add file previews for text, images, PDFs, CSV, JSON, and code. <!-- task-id:TODO-6fae629bee18 -->
- [ ] Add project knowledge-base ingestion, chunking, indexing, retrieval, citations, and deletion propagation. <!-- task-id:TODO-24637d64142e -->
- [ ] Add project-scoped permissions and inherited instruction/version semantics. <!-- task-id:TODO-fffb495963b8 -->
- [ ] Add project pinning, ordering, filters, favorite tasks, and task-to-project movement. <!-- task-id:TODO-9e9fd72f6fe8 -->
- [ ] Add local-only and hosted-storage modes with explicit data-location indicators. <!-- task-id:TODO-a69059cca4b8 -->
- [ ] Add backup/restore coverage for metadata and content. <!-- task-id:TODO-fc8785fba2ea -->
## 18.10 Phase I — Local Browser Operator extension [P1; Cloud Browser excluded]
- [ ] Define a Chrome/Edge extension protocol for authorized tabs, sessions, screenshots, navigation, DOM extraction, and action requests. <!-- task-id:TODO-f726762cda92 -->
- [ ] Implement authenticated local relay bound to loopback with origin validation and rotating session keys. <!-- task-id:TODO-3503d0594da6 -->
- [ ] Require explicit per-session browser authorization. <!-- task-id:TODO-adf1858ed563 -->
- [ ] Preserve “no password storage” and allow takeover for passwords, MFA, CAPTCHA, and sensitive pages. <!-- task-id:TODO-b3424fb5708e -->
- [ ] Add tab selection and browser-profile selection. <!-- task-id:TODO-39af57932323 -->
- [ ] Enforce domain allowlists and operation-level approvals. <!-- task-id:TODO-0e14227fb51a -->
- [ ] Add download path containment and file-type policies. <!-- task-id:TODO-08a5c545b916 -->
- [ ] Add visible stop/release control that immediately ends agent control. <!-- task-id:TODO-169d89e78224 -->
- [ ] Add action timeline, screenshots, URL history, and redacted audit events. <!-- task-id:TODO-fb449c0200f4 -->
- [ ] Add extension disconnect and browser restart recovery. <!-- task-id:TODO-011a82bb6745 -->
- [ ] Test Chrome and Edge, multiple tabs, stale sessions, MFA handoff, downloads, form submission, and emergency stop. <!-- task-id:TODO-305c61ffa73c -->
## 18.11 Phase J — Wide Research [P1]
- [ ] Add explicit Wide Research task mode with item source, item identity, requested fields, output format, concurrency, and evidence policy. <!-- task-id:TODO-a6d8c4f2e7a6 -->
- [ ] Implement bounded map workers with isolated context per item. <!-- task-id:TODO-a2b1525fe2c1 -->
- [ ] Add work queue, leases, progress counters, retries, partial completion, and resume. <!-- task-id:TODO-c1a0ded27134 -->
- [ ] Store per-item source URLs, quotes, extracted values, uncertainty, and verification status. <!-- task-id:TODO-2e087a355c06 -->
- [ ] Add synthesis worker that waits for required items or produces a clearly marked partial result. <!-- task-id:TODO-50d540e4bcff -->
- [ ] Add table, CSV, JSON, Markdown report, and chart artifacts. <!-- task-id:TODO-f47202dabe6f -->
- [ ] Add rate-limit-aware concurrency and provider budget controls. <!-- task-id:TODO-e217008c6b6f -->
- [ ] Add cancellation that stops new items and allows active items to finish or terminate safely. <!-- task-id:TODO-0218ee9d605a -->
- [ ] Add tests for 10, 50, and 100-item fixtures with injected failures and duplicate sources. <!-- task-id:TODO-1c8676da3dfb -->
## 18.12 Phase K — Website build, publish, and artifact lifecycle [P1]
- [ ] Add website entity linked to project/task with title, visibility, URL, status, and current checkpoint. <!-- task-id:TODO-0b918d50520f -->
- [ ] Add checkpoint records with version ID, commit/hash, status, timestamp, message, files, tests, and preview URL. <!-- task-id:TODO-8f80fadbfd51 -->
- [ ] Add local preview and optional user-selected hosting adapter. <!-- task-id:TODO-ba3ba5978a74 -->
- [ ] Add publish, republish-latest, update metadata, visibility, and rollback controls. <!-- task-id:TODO-36ce70dfbfb6 -->
- [ ] Add deployment logs, health checks, failure state, and retry. <!-- task-id:TODO-3a043a2ffeb9 -->
- [ ] Add custom-domain configuration documentation without storing provider secrets in project files. <!-- task-id:TODO-8b263592765e -->
- [ ] Add explicit deployment approvals and public-visibility confirmation. <!-- task-id:TODO-ba8e2760bdac -->
- [ ] Add website artifact links from task history and contextual rail. <!-- task-id:TODO-968f7b91d98b -->
### L1. Slides
- [ ] Add presentation artifact model with deck metadata, slide objects, notes, theme, assets, and source citations. <!-- task-id:TODO-a772599ed072 -->
- [ ] Add outline → content → visual → review → export pipeline. <!-- task-id:TODO-15e3d87d2f12 -->
- [ ] Support editable PPTX, PDF, web slides, and speaker-notes export. <!-- task-id:TODO-7ff2cb12a898 -->
- [ ] Support imported templates with font, color, layout, and asset validation. <!-- task-id:TODO-7b86e829b08a -->
- [ ] Add chart generation from CSV/XLSX/JSON data. <!-- task-id:TODO-21b1b5a9cc7d -->
- [ ] Add slide-level approval, revision, and visual verification. <!-- task-id:TODO-c815cb6ddba3 -->
- [ ] Add tests for deck generation, export, notes, and template preservation. <!-- task-id:TODO-7b4a54bd55e3 -->
### L2. Multimedia
- [ ] Add unified media artifact model for image, audio, video, transcript, caption, and derived metadata. <!-- task-id:TODO-6f736f5ec43c -->
- [ ] Add image understanding and OCR task stages. <!-- task-id:TODO-f8d54eda2a37 -->
- [ ] Add video ingestion, frame extraction, audio extraction, transcript alignment, and evidence timestamps. <!-- task-id:TODO-baa89d6903ea -->
- [ ] Add speech-to-text provider/local runtime integration. <!-- task-id:TODO-1f2c6cfbc243 -->
- [ ] Add text-to-speech provider/local runtime integration. <!-- task-id:TODO-69f4b8f48caf -->
- [ ] Add media generation job polling, cancellation, retries, quota, and asset cleanup. <!-- task-id:TODO-a9d75eb02ef7 -->
- [ ] Add content-type capability negotiation before provider calls. <!-- task-id:TODO-dc3b561063c9 -->
- [ ] Add approval and policy checks for generated media and external publishing. <!-- task-id:TODO-cfa675dc7769 -->
## 18.14 Phase M — Usage, budgets, and provider health [P1]
- [ ] Record model calls, tokens, latency, retries, local compute time, connector calls, downloads, storage, and bandwidth. <!-- task-id:TODO-f54849faf951 -->
- [ ] Add provider and connector rate-limit state with reset timestamps. <!-- task-id:TODO-e8d4e0cc065f -->
- [ ] Add per-task, per-project, per-agent, and global budgets. <!-- task-id:TODO-2544d68a87ea -->
- [ ] Add warning thresholds, hard stops, and approval escalation. <!-- task-id:TODO-650db53a54e6 -->
- [ ] Add usage dashboard with filters, pagination, export, and redacted diagnostics. <!-- task-id:TODO-492de74d9866 -->
- [ ] Add health dashboard for models, runtimes, connectors, browser relay, scheduler, and webhooks. <!-- task-id:TODO-67b1a84e509f -->
- [ ] Add exponential backoff with jitter and circuit breakers for external services. <!-- task-id:TODO-d5dca5d50e5b -->
- [ ] Add cost-estimation disclaimers and provider-specific pricing configuration without hardcoding unstable prices. <!-- task-id:TODO-036d1caf08ba -->
## 18.15 Phase N — Collaboration and remote local-host access [P2]
- [ ] Define hosted collaboration mode separately from local-only mode. <!-- task-id:TODO-523f738fbbd0 -->
- [ ] Add identity, invitations, roles, permissions, task sharing, project sharing, and revocation. <!-- task-id:TODO-a1c28c1e28d9 -->
- [ ] Add real-time event synchronization with ordered prompts and conflict handling. <!-- task-id:TODO-160aa2733887 -->
- [ ] Add owner-controlled approval and connector permissions. <!-- task-id:TODO-ddb917bb9dfe -->
- [ ] Add secure remote gateway for submitting tasks to an online Windows host. <!-- task-id:TODO-46cdff75adfd -->
- [ ] Add device registration, revocation, session expiry, and notification controls. <!-- task-id:TODO-fbc4355a5616 -->
- [ ] Add privacy indicators showing which files, connectors, and browser sessions are shared. <!-- task-id:TODO-a11197947914 -->
- [ ] Add collaboration audit history and export. <!-- task-id:TODO-553c6f053e0d -->
## 18.16 Phase O — Security, recovery, and release operations [P0/P1]
- [ ] Add per-task working-directory isolation and safe path containment. <!-- task-id:TODO-83c70b0a8aa9 -->
- [ ] Add subprocess CPU, RAM, wall-clock, output-size, and process-count limits. <!-- task-id:TODO-637eefb817d8 -->
- [ ] Add network egress policy by provider, connector, domain, and task. <!-- task-id:TODO-b77dff3f1c58 -->
- [ ] Add executable/script scanning and quarantine before execution. <!-- task-id:TODO-af780e47f4cc -->
- [ ] Add tamper-evident audit export with redaction verification. <!-- task-id:TODO-d9c695c01887 -->
- [ ] Add encrypted backup and restore for SQLite, catalogs, projects, task history, and protected connection metadata. <!-- task-id:TODO-55c59644866f -->
- [ ] Add migration dry-run, rollback-safe migration, and restore validation. <!-- task-id:TODO-070e8f94bb8b -->
- [ ] Add signed update manifest, integrity validation, release channels, and rollback package. <!-- task-id:TODO-86b4e5dd4cdf -->
- [ ] Add opt-in crash reporting with local redaction preview. <!-- task-id:TODO-9c3f8ab35b95 -->
- [ ] Add clean-machine tests for first launch, missing runtime, blocked port, firewall, WebView2 absence, no network, corrupted state, interrupted migration, and duplicate launch. <!-- task-id:TODO-c54222337cb2 -->
- [ ] Add release SBOM, dependency audit, license inventory, and reproducible build record. <!-- task-id:TODO-d2fab7607fbf -->
## 18.17 Verification matrix
- [ ] Unit-test every new model, migration, schema, policy, and state transition. <!-- task-id:TODO-9cfe498f52ea -->
- [ ] Add fixture servers for OAuth, connector APIs, webhook delivery, file storage, provider rate limits, and browser relay. <!-- task-id:TODO-976bde708f85 -->
- [ ] Add property tests for path containment, credential redaction, idempotency, retry bounds, and schema validation. <!-- task-id:TODO-9d9b3e2d85e0 -->
- [ ] Add integration tests for task → subtask → connector → approval → artifact → webhook flows. <!-- task-id:TODO-f42cf5448cba -->
- [ ] Add restart tests during every durable state transition. <!-- task-id:TODO-fe195ae06ee8 -->
- [ ] Add Windows executable smoke tests after each P0 phase. <!-- task-id:TODO-9dc32583ec19 -->
- [ ] Add accessibility checks for keyboard navigation, focus order, labels, contrast, and reduced motion. <!-- task-id:TODO-b9c64144eb2e -->
- [ ] Add performance tests for 100 concurrent local subtasks, large repositories, large files, and long event streams. <!-- task-id:TODO-e6161bb7f1f7 -->
- [ ] Add a second-agent verification record for each completed roadmap phase. <!-- task-id:TODO-e8675fe3aeec -->
## 18.18 Recommended execution order
- [ ] Release 1: Durable task threads, typed waiting/confirmations, structured output, and restart recovery. <!-- task-id:TODO-7585089c2cb1 -->
- [ ] Release 2: Agent registry, bounded subtasks, skills registry, and sandbox permissions. <!-- task-id:TODO-506c6dce1518 -->
- [ ] Release 3: Connector adapter framework and first eight provider adapters. <!-- task-id:TODO-4575f645378b -->
- [ ] Release 4: Durable scheduler, webhooks, usage budgets, and provider health. <!-- task-id:TODO-6e6ab934c516 -->
- [ ] Release 5: Managed files, project knowledge bases, and local Browser Operator extension. <!-- task-id:TODO-752844bfaa74 -->
- [ ] Release 6: Wide Research, website lifecycle, Slides, and unified multimedia artifacts. <!-- task-id:TODO-1bfe5b3f9e3b -->
- [ ] Release 7: Collaboration, secure remote access, backup/restore, signed updates, and operations hardening. <!-- task-id:TODO-ca8887eb16a8 -->
## 18.19 Definition of parity for this roadmap
- [ ] Orville can run a persistent multi-turn task with typed questions and approvals. <!-- task-id:TODO-5858b001714e -->
- [ ] Agents can create bounded child tasks and synthesize verified results. <!-- task-id:TODO-740372a530f6 -->
- [ ] Skills can be imported, audited, permissioned, activated, disabled, and rolled back. <!-- task-id:TODO-fd633e8b611a -->
- [ ] Supported connectors can be signed into, refreshed, discovered, invoked, revoked, and audited. <!-- task-id:TODO-79dd991288e1 -->
- [ ] Scheduled tasks and webhooks operate safely while the GUI is closed. <!-- task-id:TODO-3c3861145384 -->
- [ ] Structured output, files, projects, and citations have durable lifecycle semantics. <!-- task-id:TODO-9cf20a06eecf -->
- [ ] Local browser access supports extension-based control and user takeover without storing passwords. <!-- task-id:TODO-dc5b24db38cf -->
- [ ] Wide Research supports bounded parallel work with item-level evidence. <!-- task-id:TODO-8cb75052a5de -->
- [ ] Websites, presentations, media, and other artifacts have versioned preview/export/publish workflows. <!-- task-id:TODO-a8d58ceea699 -->
- [ ] Usage, budgets, provider health, backups, updates, and recovery are visible and testable. <!-- task-id:TODO-8a576d7be329 -->
- [ ] Collaboration and remote access are either implemented with a secure hosted layer or explicitly marked unavailable in local-only mode. <!-- task-id:TODO-95ebb027daf1 -->
## 18.20 Research references
- [ ] Read and implement against Manus API v2 task lifecycle: [https://open.manus.im/docs/v2/task-lifecycle](https://open.manus.im/docs/v2/task-lifecycle) <!-- task-id:TODO-d1a404e4d918 -->
- [ ] Read and implement against Manus API v2 agents: [https://open.manus.im/docs/v2/agents-overview](https://open.manus.im/docs/v2/agents-overview) <!-- task-id:TODO-5099b7523010 -->
- [ ] Read and implement against Manus API v2 connectors: [https://open.manus.im/docs/v2/connectors](https://open.manus.im/docs/v2/connectors) <!-- task-id:TODO-2e34d8bcef8a -->
- [ ] Read and implement against Manus API v2 structured output: [https://open.manus.im/docs/v2/structured-output](https://open.manus.im/docs/v2/structured-output) <!-- task-id:TODO-90eeb65f853c -->
- [ ] Read and implement against Manus API v2 webhooks: [https://open.manus.im/docs/v2/webhooks-overview](https://open.manus.im/docs/v2/webhooks-overview) <!-- task-id:TODO-d7161cf0b5b3 -->
- [ ] Read and implement against Manus API v2 files: [https://open.manus.im/docs/v2/file.upload](https://open.manus.im/docs/v2/file.upload) <!-- task-id:TODO-57552c85cb04 -->
- [ ] Read and implement against Manus API v2 websites: [https://open.manus.im/docs/v2/website](https://open.manus.im/docs/v2/website) <!-- task-id:TODO-bcffb465f97d -->
- [ ] Read and implement against Manus API v2 rate limits: [https://open.manus.im/docs/v2/rate-limits](https://open.manus.im/docs/v2/rate-limits) <!-- task-id:TODO-ac34c90b96b0 -->
- [ ] Review Manus Skills: [https://manus.im/docs/features/skills](https://manus.im/docs/features/skills) <!-- task-id:TODO-51bea3079e35 -->
- [ ] Review Manus Projects: [https://manus.im/docs/features/projects](https://manus.im/docs/features/projects) <!-- task-id:TODO-39fb74533715 -->
- [ ] Review Manus Desktop/My Computer: [https://manus.im/docs/features/desktop](https://manus.im/docs/features/desktop) <!-- task-id:TODO-f630fcf1acdc -->
- [ ] Review Manus Browser Operator: [https://manus.im/docs/features/browser-operator](https://manus.im/docs/features/browser-operator) <!-- task-id:TODO-2982c7a589ea -->
- [ ] Review Manus Wide Research: [https://manus.im/docs/features/wide-research](https://manus.im/docs/features/wide-research) <!-- task-id:TODO-81bdec2f2260 -->
- [ ] Review Manus Scheduled Tasks: [https://manus.im/docs/features/scheduled-tasks](https://manus.im/docs/features/scheduled-tasks) <!-- task-id:TODO-903b307d21d4 -->
- [ ] Review Manus Collab: [https://manus.im/docs/features/collab](https://manus.im/docs/features/collab) <!-- task-id:TODO-c4825d5e10c0 -->
- [ ] Review Manus Slides: [https://manus.im/docs/features/slides](https://manus.im/docs/features/slides) <!-- task-id:TODO-327dc76e2416 -->
- [ ] Review Manus Multimedia: [https://manus.im/docs/features/multi-modal](https://manus.im/docs/features/multi-modal) <!-- task-id:TODO-3d8918341092 -->
## 18.21 Research limitation
- [ ] Video demonstrations were identified for additional first-hand evidence, but automated video analysis was unavailable during this run because the analysis service reported insufficient credits. Official documentation was used as the authoritative implementation basis; video evidence should be added during a later research pass if available. <!-- task-id:TODO-27b0645872ac -->
# 19. Active Execution Batch — Manus-Parity Implementation
- [ ] Audit the current Windows repository, test baseline, packaging configuration, and existing roadmap state. <!-- task-id:TODO-94503e6f242b -->
- [ ] Complete agent registry and bounded subtask execution. <!-- task-id:TODO-efaa0108c4a8 -->
- [ ] Complete provider-specific connector adapter framework and priority adapters. <!-- task-id:TODO-8f272d72b592 -->
- [ ] Complete connector defaults, refresh, revoke, discovery, rate limits, and operation schemas. <!-- task-id:TODO-f4260cac08a8 -->
- [ ] Complete durable scheduling and signed webhook delivery. <!-- task-id:TODO-c9a4edddb56e -->
- [ ] Complete usage, budget, quota, provider-health, and notification controls. <!-- task-id:TODO-102b27748183 -->
- [ ] Complete managed file lifecycle and project knowledge-base indexing. <!-- task-id:TODO-b2fe8a186a50 -->
- [ ] Complete local Browser Operator extension and secure relay; Cloud Browser remains excluded. <!-- task-id:TODO-10a98d16bd88 -->
- [ ] Complete Wide Research map/reduce execution and evidence synthesis. <!-- task-id:TODO-0446f6b8779d -->
- [ ] Complete website lifecycle, publishing adapter, and checkpoint management. <!-- task-id:TODO-40b0d0efcc90 -->
- [ ] Complete Slides artifact generation and export. <!-- task-id:TODO-1f8b2e6253b4 -->
- [ ] Complete unified multimedia artifacts, speech-to-text, text-to-speech, and video understanding. <!-- task-id:TODO-ec1aa8dcb33b -->
- [ ] Complete collaboration and secure remote-local access boundaries where feasible without claiming hosted parity. <!-- task-id:TODO-46d9f594d458 -->
- [ ] Complete sandboxing, backups, restore tests, signed updates, observability, and release hardening. <!-- task-id:TODO-a71eaa592243 -->
- [ ] Run full regression, clean-machine startup, security, recovery, and Windows packaging validation. <!-- task-id:TODO-7c88988f44f2 -->
- [ ] Create final checkpoint and deliver the completed artifacts with documented limitations. <!-- task-id:TODO-15e9426eb73f -->
## 19.1 Execution progress — 2026-08-26
- [ ] Provider-specific connector network handlers, OAuth refresh/revocation for each provider, and production credential test coverage remain incomplete. <!-- task-id:TODO-d695aa6a8050 -->
- [ ] Signal Room UI still needs dedicated surfaces for agent profiles, Skills, task-thread state, budgets, provider health, and adapter support status. <!-- task-id:TODO-b1216a68949f -->
## 19.2 Execution progress — continuation
- [ ] Provider-specific network handlers and real credentialed integration tests remain required before claiming operational support for each connector. <!-- task-id:TODO-575a52352d24 -->
- [ ] GUI surfaces and packaged-release rebuild remain required for this execution batch. <!-- task-id:TODO-57fb54e87070 -->
# 20. Full Connector Adapter Execution
- [ ] Inventory and normalize every connector catalog entry. <!-- task-id:TODO-5f8611ca4828 -->
- [ ] Classify each connector as native-provider, generic-HTTP, OpenAPI-discoverable, local-endpoint, or configuration-required. <!-- task-id:TODO-361fa3f1fbc5 -->
- [ ] Add a universal adapter manifest with authentication, base URL, scopes, operations, schemas, risk classes, limits, and documentation links. <!-- task-id:TODO-928123bf51b3 -->
- [ ] Add OpenAPI discovery with schema sanitization, operation caps, host allowlists, and user approval. <!-- task-id:TODO-dbc795387932 -->
- [ ] Add provider-specific auth refresh, revoke, pagination, retry, and error normalization contracts. <!-- task-id:TODO-0e8a359a23f4 -->
- [ ] Generate a manifest for every catalog connector without falsely marking unsupported services operational. <!-- task-id:TODO-f12e61555796 -->
- [ ] Connect manifests to per-connector sign-in, defaults, operation discovery, approval, audit, usage, and provider-health state. <!-- task-id:TODO-7888020be11c -->
- [ ] Add adapter support-state visibility to the Connectors menu. <!-- task-id:TODO-34e1f4ad28d2 -->
- [ ] Add fixture and contract tests for every adapter class and priority provider group. <!-- task-id:TODO-6cac0015117b -->
- [ ] Rebuild and validate the Windows executable and portable release. <!-- task-id:TODO-d27ea90cef5c -->
- [ ] Document configuration-required connectors and the user steps for provider OAuth/API registration. <!-- task-id:TODO-6a028bf461aa -->
## 20.1 Full-catalog adapter milestone — 2026-08-26
- [ ] Provider-specific handlers, OAuth presets, real provider operation contracts, and credentialed integration tests remain required for each external service. <!-- task-id:TODO-f91997ffda10 -->
# 21. Four-Layer Connector Architecture Execution
- [ ] Audit catalog/manifest registry coverage, authentication lifecycle, operation adapters, and approval/audit gateway. <!-- task-id:TODO-160c8c1f94af -->
- [ ] Add manifest versioning, capability metadata, scopes, limits, risk classifications, documentation, and support-state transitions. <!-- task-id:TODO-4ca557b3c3f4 -->
- [ ] Add OAuth2 PKCE refresh, revocation, expiry recovery, and provider preset lifecycle. <!-- task-id:TODO-7c61769eb124 -->
- [ ] Add API-key/bearer validation, rotation, account labels, and connection health checks. <!-- task-id:TODO-c1f53b116bb4 -->
- [ ] Add generic OpenAPI operation discovery with sanitization and approval. <!-- task-id:TODO-df9186721089 -->
- [ ] Add adapter pagination, upload/download contracts, bounded retries, rate-limit handling, and normalized errors/results. <!-- task-id:TODO-fbd05e7e7f51 -->
- [ ] Integrate operation schemas with approval, redaction, egress policy, usage, and audit records. <!-- task-id:TODO-f6361a1631d1 -->
- [ ] Add Connectors UI support-state, health, defaults, operation, and approval controls. <!-- task-id:TODO-4f4b00da1461 -->
- [ ] Add fixture and contract tests for all four layers and rebuild the Windows release. <!-- task-id:TODO-fd294435b323 -->
## 21.1 Four-layer architecture progress
- [ ] Connectors UI still needs dedicated controls for refresh, revoke, defaults, and OpenAPI discovery results. <!-- task-id:TODO-b8f5aac9c941 -->
- [ ] Provider-specific handlers and credentialed contract tests remain required for each external service. <!-- task-id:TODO-bf1c2a2376b4 -->
## 21.2 Verified four-layer connector milestone
- [ ] Provider-specific handlers and credentialed contract tests are still required for each third-party service; configuration-required fallback is intentional for services without a verified handler. <!-- task-id:TODO-ca2439065edd -->
# 22. Connector Roadmap Continuation
- [ ] Implement user/project/task connector defaults with explicit override and clear semantics. <!-- task-id:TODO-9f0ee5882c51 -->
- [ ] Add provider OAuth presets, scopes, token endpoints, revocation endpoints, and refresh policy metadata. <!-- task-id:TODO-9c3cde3783c8 -->
- [ ] Add connector health, expiry, refresh, and reauthorization status controls to the Connectors UI. <!-- task-id:TODO-6282db5e033a -->
- [ ] Add bounded adapter pagination and normalized page/cursor results. <!-- task-id:TODO-06adb74b1d29 -->
- [ ] Add adapter retries, rate-limit parsing, circuit integration, and normalized error envelopes. <!-- task-id:TODO-d0dae1765b35 -->
- [ ] Integrate connector operation schemas with approval, usage, and audit records. <!-- task-id:TODO-49e00bb85e58 -->
- [ ] Add credential-free provider fixtures and contract tests for all adapter classes. <!-- task-id:TODO-7805fb19cce2 -->
### Automated canary deployments
- [!] M13.15 Integrate a reviewed production deployment provider only after dry-run, non-production canary, and rollback-drill gates pass; requires an explicitly selected deployment provider, credentials, environment, and operator approval. <!-- task-id:TODO-bf8cc4ae2753 -->
### M13 acceptance gates
- [ ] Required attestation policies fail closed for missing, malformed, expired, revoked, wrong-digest, wrong-key, and unverifiable artifacts. <!-- task-id:TODO-089e9e7452e3 -->
- [ ] Canary advancement requires fresh health evidence, minimum samples, bounded hold time, and no critical security event. <!-- task-id:TODO-c4b2c016125f -->
- [ ] Non-production canary and recovery drill pass before any production adapter is enabled; no production provider or traffic has been used. <!-- task-id:TODO-2d6448742192 -->
## Current security milestone — M12.8 continuation
- [ ] Complete a production trust-root ceremony using operator-reviewed signed root metadata and an out-of-band pinned root digest. <!-- task-id:TODO-814f902bf980 -->
- [!] Execute live Linux bubblewrap worker IPC/GPU tests on a Linux host with bubblewrap and an exposed GPU device; the current host capability is not sufficient. <!-- task-id:TODO-66fdeb90e288 -->
## 8.6 Next milestone — M14 Enterprise Production Readiness
- [ ] M14.9 Establish encrypted off-host backups, retention, restore verification, RTO/RPO evidence, access review, and a disaster-recovery runbook. <!-- task-id:TODO-97bdd2fb0076 -->
- [ ] M14.10 Run production-readiness security, load, soak, dependency, observability, quota, cost, and rollback gates with sanitized evidence. <!-- task-id:TODO-20c9e32dc7de -->
- [!] M14.11 Execute a controlled production canary only after M14.1–M14.10 pass and explicit operator approval is recorded. <!-- task-id:TODO-1f50da4a9ba5 -->
