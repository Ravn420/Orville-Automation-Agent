# Orville Test-Failure Diagnosis, Component Breakdown, and Optional-Component Setup

**Assessment date:** 2026-08-27  
**Repository revision assessed:** `4e94b3ad394f83140025637e368957ad011b082e` on `main`  
**Scope:** The 444-test `unittest` discovery execution that completed with **7 failures and 8 errors**, the project structure recorded in the assessment, and documented local setup for the optional API and Browser Operator extension.

## Executive summary

The final test result has three classes of issue. Five errors result from an unmet desktop-UI environment dependency (`tkinter`); two errors result from a missing, required visual-regression baseline artifact; and one error is a preview-server readiness race. Among the seven assertion failures, four have a common cross-platform path-normalization defect in their tests, while three concern stale or overly brittle assertions around UI copy and persistence behavior. None of the evidence indicates a provider-credential or external-service failure. [1] [2] [3]

The most efficient recovery sequence is to correct the portable test harness first, create and review the missing visual baseline, make preview startup wait for readiness, then update the stale/brittle unit-test expectations or the corresponding declared contract. That sequence should reduce environmental noise before changing orchestration behavior.

| Priority | Remediation workstream | Affected outcomes |
|---|---|---|
| P0 | Make GUI-dependent test collection portable and correct slash-path normalization | 5 errors and 4 failures |
| P1 | Add/review the required visual-regression baseline | 2 errors |
| P1 | Make preview startup report readiness before returning | 1 error |
| P2 | Reconcile checkpoint schema and monitor-copy contracts | 2 failures |
| P2 | Make timeout assertion target the failure event by type, not list position | 1 failure |

## Detailed test-failure diagnosis and recommended fixes

### Errors: environment and test-fixture prerequisites

| Count | Affected test(s) | Evidence and root cause | Recommended fix | Validation |
|---|---|---|---|---|
| 5 | `test_dashboard`, `test_gui_degraded_availability`, `test_gui_performance_measurement`, `test_gui_sensitive_data`, `test_workflow_state_handling` | These modules import `windows_gui`, which imports `tkinter` at module-import time. The Linux runner lacks the system `tkinter` package. Several tests exercise pure state or dashboard helper behavior rather than rendering a live window. [2] | For immediate CI unblocking, install the platform package in the GUI-test job (Ubuntu: `sudo apt-get install -y python3-tk`). For a durable portable design, move pure state/copy/dashboard transforms to a non-GUI module such as `orville_core/gui_state.py`, test that module without `tkinter`, and mark only true UI-rendering tests as skipped when the optional UI dependency is unavailable. Document desktop UI prerequisites in the development setup. | Run the five modules under the Linux test job with and without the GUI package. Pure helper tests should pass without `tkinter`; rendering tests should either run with it or be explicitly skipped. |
| 1 | `test_preview_runtime.PreviewRuntimeTests.test_start_status_http_and_stop` | `PreviewRuntime.start()` launches `python -m http.server` and returns immediately; the test immediately calls `urlopen()`. The observed connection refusal is consistent with a process-readiness race. The implementation also does not verify whether the child exited during startup. [4] | Add a bounded readiness loop to `start()`: poll `process.poll()` and attempt a TCP/HTTP connection until the selected port accepts requests or a short deadline expires. On failure, terminate the process and raise a diagnostic exception containing bounded child stderr. Keep the test’s immediate HTTP request; it then verifies the public `start()` contract. | Execute `python -m unittest tests.test_preview_runtime -v` repeatedly, including under loaded CI workers, and confirm it has no intermittent refusal. |
| 2 | `test_visual_regression.VisualRegressionTests.test_current_assets_match_committed_baseline`; `test_changed_baseline_fails_closed` | Both tests unconditionally read `artifacts/visual_regression_baseline.json`. The checker deliberately has no absent-baseline fallback, and that file is missing from the checkout. The baseline is a required reviewed artifact, not a disposable test by-product. [5] [6] | Generate a candidate baseline with `python tools/visual_regression.py snapshot > artifacts/visual_regression_baseline.json`. Inspect the JSON and review the sourced design-system and mockup changes. Once approved, force-add the ignored artifact to Git (`git add -f artifacts/visual_regression_baseline.json`) and commit it with the review evidence. Do **not** modify `check_baseline()` to silently create or accept a baseline. | Run `python tools/visual_regression.py check` and `python -m unittest tests.test_visual_regression -v`. The regular comparison should pass, while the test that mutates a temporary baseline should still fail closed. |

### Failures: contracts, behavior, and cross-platform paths

| Count | Affected test(s) | Evidence and root cause | Recommended fix | Validation |
|---|---|---|---|---|
| 1 | `test_execution_monitor.ExecutionMonitorTests.test_monitor_uses_safe_bounded_output` | The test requires the literal `Run unavailable. Check the run ID and local API status.`. The offline branch instead displays `state_message("offline")`, whose copy is different but remains bounded and does not expose a raw API error or payload. [2] [7] | Decide the canonical UX copy in the execution-monitor specification. If that literal is the approved contract, add it to the offline-state message rendered by `show_run()`. If the current offline text is intentional, revise the test to assert the semantic safety contract—bounded output, no raw error/payload, and a safe recovery prompt—rather than a single presentation string. The second option is less brittle and better matches the test’s stated purpose. | Run `python -m unittest tests.test_execution_monitor -v`, then manually trigger an unavailable local API and confirm no raw response body, token, or stack trace reaches the UI. |
| 1 | `test_orchestration.OrchestrationTests.test_checkpoint_file_is_valid_json` | The current serializer emits `"schema_version": 2`, while the test expects 1. The deserializer explicitly accepts both 1 and 2, indicating a deliberate forward schema change with backward-read compatibility. [8] | Update the test to expect version 2 for newly written checkpoints. Add or retain a separate fixture-based migration test that loads version-1 checkpoints and proves that the reader remains backward compatible. Reverting emitted checkpoints to version 1 would be appropriate only if version 2 was accidental or violates an external compatibility commitment. | Run the focused orchestration test module and add assertions that a v1 fixture loads successfully while a new checkpoint writes v2. |
| 1 | `test_orchestration.OrchestrationTests.test_task_timeout_is_persisted_as_failure` | The test reads `result.events[-2]`. The engine records `task_failed` with the timeout in its `error`, then appends an operation checkpoint and later a `run_failed` event. Therefore the second-to-last event can be a non-failure event with no `error` field even though timeout persistence occurred. [9] | Rewrite the test to select the `task_failed` event for task `slow`, then assert that its `details.error` contains `timeout`. Include sequential and parallel timeout cases. Only change engine event ordering if positional ordering is intentionally part of the public event contract and is documented as such. | Run `python -m unittest tests.test_orchestration -v` and assert the event stream contains one explicit timeout failure plus the expected run-finalization event. |
| 4 | `test_operator_runbook...referenced_procedures...`; `test_orchestration_test_matrix...references...`; `test_reusable_fixes...problem_assets...`; `test_standalone_readme...local_contracts...` | Each failing test replaces `/` with `\\` before using `pathlib.Path` to test repository files. The documents/configuration correctly use normal forward-slash repository paths; on Linux the replacement creates a filename containing backslashes, so existing files appear absent. [10] [11] [12] [13] | Remove every `reference.replace("/", "\\")` transformation. Use `ROOT / Path(reference)` or `ROOT.joinpath(*PurePosixPath(reference).parts)` so repository references resolve on Windows, macOS, and Linux. Put the common resolver in a small test helper to prevent recurrence, then add a POSIX CI job. | Re-run the four modules on Linux and Windows. Add a focused resolver test for `docs/SECRET_HANDLING_RULES.md`, `tests/test_core_unit_contracts.py`, and `tools/project_checks.py`. |

> **Recommended ownership boundary:** Treat `tkinter`, the visual baseline, and preview readiness as prerequisites/implementation work. Treat forward-slash transformation, the schema expectation, and positional event indexing as test-harness maintenance unless a documented public contract says otherwise. Do not silently weaken security, baseline-review, or timeout-persistence behavior merely to obtain a green test run.

## Detailed project structure and main components

The repository has **612 tracked files** at the assessed revision, including **103 core Python modules**, **205 Python test modules**, **23 Python operational tools**, and **2 Python examples**. The following inventory counts tracked files only, excluding untracked caches and transient test by-products. [14]

| Area | Tracked files | Primary responsibility | Principal contents |
|---|---:|---|---|
| `orville_core/` | 104 | Application core | 103 Python modules plus packaged JSON data. Implements orchestration, persistence, APIs, policy, adapters, security, provider/model routing, and runtime health. |
| `tests/` | 210 | Automated validation | 205 Python modules spanning unit behavior, acceptance, API/CLI, GUI contract, security, release, provider, connector, deployment, and documentation checks. |
| `docs/` | 145 | Technical and operational contract | Architecture, deployment, security, connector, testing, runbook, feature, mockup, and recovery documentation. |
| `tools/` | 24 | Operational and release automation | Project checks, test triage, release gates, visual regression, operational reports, local worker/relay checks, and deployment validation. |
| `config/` | 16 | Versioned non-secret configuration examples | Design system, deployment and release thresholds, test triage, task templates, connector/roadmap examples, and reusable fix catalog. |
| `webui/` | 6 | Prebuilt web UI assets | Static HTML, JavaScript, CSS, and debug/version metadata. |
| `browser_extension/` | 2 | Local browser control channel | Manifest V3 declaration and background service worker for the Browser Operator extension. [15] |
| `examples/` | 3 | Deterministic onboarding | Local workflow example(s) that do not require a model provider. [16] |
| `deploy/` plus Docker files | 1 directory file plus root Docker/Compose files | Container deployment | Caddy proxy configuration, Python API container, SQLite volume, and private Compose network. [17] |
| `data/` and `artifacts/` | 8 | Project data and reviewed evidence | Versioned project inputs and test/review artifacts. Artifacts are ignored by default, so reviewed evidence must be explicitly force-added when project policy requires synchronization. |

### Core subsystem map

| Subsystem | Representative modules | Responsibilities and boundaries |
|---|---|---|
| Workflow and orchestration | `engine.py`, `workflow.py`, `models.py`, `checkpoint.py`, `persistence.py`, `task_threads.py`, `workspace*.py` | Turns objectives into dependency-aware task graphs; schedules, verifies, pauses, cancels, retries, checkpoints, and recovers task execution while enforcing workspace containment. [9] |
| Agent and worker coordination | `agent_runtime.py`, `agent_modes.py`, `agent_contracts.py`, `worker_protocol.py`, `model_worker.py`, `assignment_review.py` | Defines specialist-agent modes, contracts, assignment/review boundaries, and worker communication. |
| API, CLI, and MCP interfaces | `api.py`, `cli.py`, `mcp_server.py`, `openapi_discovery.py`, `relay_server.py` | Offers local authenticated HTTP, command-line operations, MCP integration, and bounded OpenAPI/relay entry points. The declared scripts are `orville-api`, `orville`, and `orville-python-mcp`. [18] |
| Providers and model execution | `providers.py`, `routing.py`, `provider_features.py`, `provider_presets.py`, `model_runtime.py`, `model_safety.py`, `local_models.py`, `hub_models.py` | Provides provider-neutral capability selection, local-model integration, routing/fallback policy, privacy/safety controls, and runtime health. |
| Connectors and browser integration | `connector_*.py`, `browser.py`, `browser_relay.py`, `catalog_adapters.py`, `connector_bridge.py` | Manages connector metadata, configuration, health, authorization, operation policy, audit boundaries, and the explicit local browser relay. [19] |
| Security, trust, and governance | `security.py`, `protected_secrets.py`, `secrets_audit.py`, `untrusted_content.py`, `confirmations.py`, `supply_chain.py`, `tuf_metadata.py`, `trust_root_ceremony.py` | Redacts sensitive data, constrains untrusted inputs, requires approvals, protects secrets, maintains trust/update evidence, and supports auditable release gates. |
| Observability and operations | `observability.py`, `structured_logging.py`, `telemetry.py`, `production_metrics.py`, `readiness.py`, `runtime_health.py`, `recovery.py` | Captures bounded telemetry, reports readiness/health, records operation outcomes, and supports controlled recovery. |
| UI and user experience | `windows_gui.py`, `webui/`, `browser_extension/` | Provides a Tkinter-based desktop control center, prebuilt web assets, and an explicit-pairing browser extension. The GUI requires the operating system’s Tk bindings. [2] [15] |

## Optional authenticated API: setup and local execution

The optional API is a FastAPI bridge for authorized local GUI or other clients. It exposes task intake, persisted checkpoints, approval/cancellation state, project state, and artifact access behind a bearer-token boundary. It is not a public-production deployment by itself. [18]

### Local development procedure

From the repository root, create an isolated environment, install the API optional dependency group, set a non-committed runtime token, and start the module. The command below is for Linux/macOS; on Windows, use the PowerShell activation and `$env:ORVILLE_API_TOKEN` syntax documented in the README. [16] [18]

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[api]'

# Use a long random value generated and stored only in the runtime environment.
export ORVILLE_API_TOKEN='replace-with-a-long-random-runtime-only-value'
export ORVILLE_API_HOST='127.0.0.1'
export ORVILLE_API_PORT='8787'
python -m orville_core.api
```

The default listener is `127.0.0.1:8787`. Verify documentation and the authenticated health route from another terminal; do not print the actual token in issue logs, screenshots, or committed files. [16] [18]

```bash
curl -I http://127.0.0.1:8787/docs
curl -H "Authorization: Bearer $ORVILLE_API_TOKEN" \
  http://127.0.0.1:8787/api/v1/health
```

| API endpoint group | Local purpose |
|---|---|
| `GET /api/v1/health` | Authenticated health check. |
| `POST /api/v1/objectives` and `POST /api/v1/objectives/{run_id}/execute` | Normalize an objective and, when handlers are injected, execute its graph. |
| `GET /api/v1/runs/{run_id}` and `/events` | Read persisted checkpoints and bounded execution events. |
| Cancellation and approval routes | Request cancellation or approve/reject a guarded task. |
| State and artifact routes | Read project state and root-bound artifacts. [18] |

The API fails closed with HTTP 409 for execution when no handler registry or injected orchestration engine exists. Keep it on loopback for local development. Any exposure beyond localhost requires independent, reviewed TLS, identity/authorization, restrictive origins, rate limiting, and other production controls; those services are explicitly outside the default standalone API. [18]

## Optional Browser Operator extension: setup and operation

The Browser Operator is an unpacked **Manifest V3** extension rather than a hosted browser service. It uses only `activeTab`, `scripting`, and `storage` permissions; its background worker posts approved, allowlisted actions to the local relay at `http://127.0.0.1:8787`. It does not store passwords, cookies, or cloud browser sessions. [15] [19]

### Prerequisites

The local Orville API/relay must be running on its default loopback endpoint. The user must be able to load an unpacked extension in Chrome or Edge and must explicitly pair an approved HTTP(S) browser tab through the local Signal Room workflow. The extension will return `extension-not-paired` until an authorized pairing creates its relay session and secret. [15] [19]

### Chrome or Edge procedure

1. Start the local API using the preceding section and keep it running during browser operations.
2. Open `chrome://extensions` in Chrome or `edge://extensions` in Edge. Enable **Developer mode**.
3. Select **Load unpacked** and choose the repository’s `browser_extension/` directory. Confirm the installed extension is named **Orville Browser Operator**.
4. In Orville’s Signal Room, initiate the documented local pairing flow. Then open the intended HTTP or HTTPS tab and click the extension action, **Pair with Orville**, to record the selected tab and origin.
5. Approve any requested takeover or sensitive action within Orville. Keep the API and extension active only for the duration needed, then use the relay’s release/revocation controls.

The background worker allows only `navigate`, `extract`, `screenshot`, `takeover_request`, and `release`. It sends the stored pairing secret and session identifier to the relay action route; it does not grant broad arbitrary browser automation. [15]

| Operational control | Expected behavior |
|---|---|
| Unpaired extension | Rejects relayed messages with `extension-not-paired`. |
| Disallowed action | Rejects the action with `action-not-allowlisted`. |
| Non-web page | The toolbar click refuses to pair tabs outside the `http:` or `https:` schemes. |
| Sensitive or critical connector operation | Requires explicit approval through the connector/relay policy gateway. [19] |
| Local service stopped | The extension cannot exchange actions; restart the loopback Orville service rather than exposing its local relay publicly. |

## Suggested verification order after remediation

Run the corrected environment and focused tests first, then the whole suite. The following sequence narrows failure sources and retains the project’s fail-closed behavior. [5] [16]

```bash
# GUI environment/portable-helper tests
python -m unittest tests.test_dashboard tests.test_workflow_state_handling \
  tests.test_gui_degraded_availability tests.test_gui_performance_measurement \
  tests.test_gui_sensitive_data -v

# Cross-platform documentation and configuration reference tests
python -m unittest tests.test_operator_runbook tests.test_orchestration_test_matrix \
  tests.test_reusable_fixes tests.test_standalone_readme -v

# Runtime and persistence behavior
python -m unittest tests.test_preview_runtime tests.test_orchestration \
  tests.test_execution_monitor -v

# Reviewed visual baseline
python tools/visual_regression.py check
python -m unittest tests.test_visual_regression -v

# Final configured suite
python -m unittest discover -s tests -v
```

## References

[1]: https://github.com/Ravn420/Orville-Automation-Agent/blob/4e94b3ad394f83140025637e368957ad011b082e/artifacts/test_runs/unittest_discover_with_pytest_2026-08-27.log "Final full unittest log"
[2]: https://github.com/Ravn420/Orville-Automation-Agent/blob/4e94b3ad394f83140025637e368957ad011b082e/windows_gui.py "Tkinter desktop GUI and execution monitor"
[3]: https://github.com/Ravn420/Orville-Automation-Agent/blob/4e94b3ad394f83140025637e368957ad011b082e/pyproject.toml "Project dependency declarations"
[4]: https://github.com/Ravn420/Orville-Automation-Agent/blob/4e94b3ad394f83140025637e368957ad011b082e/orville_core/preview_runtime.py "Preview runtime implementation"
[5]: https://github.com/Ravn420/Orville-Automation-Agent/blob/4e94b3ad394f83140025637e368957ad011b082e/tools/visual_regression.py "Visual regression baseline checker"
[6]: https://github.com/Ravn420/Orville-Automation-Agent/blob/4e94b3ad394f83140025637e368957ad011b082e/docs/VISUAL_REGRESSION.md "Visual regression policy"
[7]: https://github.com/Ravn420/Orville-Automation-Agent/blob/4e94b3ad394f83140025637e368957ad011b082e/tests/test_execution_monitor.py "Execution monitor test"
[8]: https://github.com/Ravn420/Orville-Automation-Agent/blob/4e94b3ad394f83140025637e368957ad011b082e/orville_core/models.py "Checkpoint serialization model"
[9]: https://github.com/Ravn420/Orville-Automation-Agent/blob/4e94b3ad394f83140025637e368957ad011b082e/orville_core/engine.py "Orchestration engine"
[10]: https://github.com/Ravn420/Orville-Automation-Agent/blob/4e94b3ad394f83140025637e368957ad011b082e/tests/test_operator_runbook.py "Operator runbook path test"
[11]: https://github.com/Ravn420/Orville-Automation-Agent/blob/4e94b3ad394f83140025637e368957ad011b082e/tests/test_orchestration_test_matrix.py "Orchestration test-matrix path test"
[12]: https://github.com/Ravn420/Orville-Automation-Agent/blob/4e94b3ad394f83140025637e368957ad011b082e/tests/test_reusable_fixes.py "Reusable-fixes path test"
[13]: https://github.com/Ravn420/Orville-Automation-Agent/blob/4e94b3ad394f83140025637e368957ad011b082e/tests/test_standalone_readme.py "Standalone README path test"
[14]: https://github.com/Ravn420/Orville-Automation-Agent/tree/4e94b3ad394f83140025637e368957ad011b082e "Repository tree"
[15]: https://github.com/Ravn420/Orville-Automation-Agent/tree/4e94b3ad394f83140025637e368957ad011b082e/browser_extension "Browser Operator extension"
[16]: https://github.com/Ravn420/Orville-Automation-Agent/blob/4e94b3ad394f83140025637e368957ad011b082e/README.md "README installation, configuration, and usage"
[17]: https://github.com/Ravn420/Orville-Automation-Agent/blob/4e94b3ad394f83140025637e368957ad011b082e/docker-compose.yml "Docker Compose deployment definition"
[18]: https://github.com/Ravn420/Orville-Automation-Agent/blob/4e94b3ad394f83140025637e368957ad011b082e/API_BRIDGE.md "API bridge setup and contract"
[19]: https://github.com/Ravn420/Orville-Automation-Agent/blob/4e94b3ad394f83140025637e368957ad011b082e/CONNECTOR_BRIDGE.md "Connector bridge and Browser Operator relay"
