# Orville Repository Assessment

**Assessment date:** 2026-08-27  
**Repository:** `Ravn420/Orville-Automation-Agent`  
**Revision assessed:** `5825bcb3f936c573953c553dd493669d5963003c` on `main`

## Executive assessment

Orville is a Python 3.10+ standalone task-graph orchestration engine intended to coordinate provider-neutral workflows with durable checkpoints. The repository combines an orchestration core, REST and MCP entry points, desktop-oriented controls, browser-extension assets, operational tooling, deployment definitions, and an extensive test/contract suite. Its production container starts an API service backed by SQLite and can be placed behind Caddy via Docker Compose. [1] [2] [3]

The repository contains **609 tracked files**, including **342 Python source files** and **204 files matching test/spec naming patterns**. The documented full `unittest` discovery run was executed after installing the declared `pytest` test dependency. The suite does **not currently pass**: it executed 444 tests in 7.739 seconds and finished with 7 failures and 8 errors. Full output is preserved in the attached test log. [1] [4]

## Main components

| Component | Principal location | Role in the system |
|---|---|---|
| Core orchestration | `orville_core/` | Implements task graphs, workflow execution, engine behavior, persistence, checkpoints, validation, scheduling, workspace safety, and recovery. |
| API, command line, and MCP interfaces | `orville_core/api.py`, `orville_core/cli.py`, `orville_core/mcp_server.py` | Exposes the FastAPI service, local command-line interface, and Python MCP server, respectively. [3] |
| Provider and model integration | `orville_core/providers.py`, `routing.py`, `model_runtime.py`, `local_models.py`, `connector_*.py`, `browser*.py` | Supplies provider-neutral adapters, capability and policy controls, local-model support, connector governance, and browser-related boundaries. |
| Security and governance | `orville_core/security.py`, `protected_secrets.py`, `untrusted_content.py`, `supply_chain.py`, `attestations.py` | Provides secret handling, untrusted-content controls, authorization/confirmation boundaries, release evidence, and supply-chain checks. |
| User-interface assets | Desktop launcher scripts and `webui/` | Contains a desktop control-center implementation and built web UI assets. Browser-extension assets live in `browser_extension/`. |
| Operational and release tooling | `tools/`, `config/`, `deploy/`, Docker files | Provides project checks, release gates, test triage, operational reporting, deployment validation, configuration examples, and Caddy/Docker deployment definitions. [1] [3] |
| Documentation and examples | Root Markdown documents, `docs/`, `examples/` | Describes architecture, provider use, operating procedures, validation controls, deployment, and deterministic examples. [1] |
| Test and evidence corpus | `tests/`, `artifacts/` | Contains unit, integration/contract, documentation, GUI, security, and release-validation tests, with generated evidence under `artifacts/`. [1] |

## Declared dependencies and runtime

The base project deliberately declares no mandatory third-party runtime dependencies. Optional dependency groups separate API hosting, browser support, media support, security, and developer testing responsibilities. The repository requires Python 3.10 or newer; the production Docker image uses Python 3.12 slim. [2] [3]

| Dependency group | Declared packages | Purpose |
|---|---|---|
| Build | `setuptools>=68` | Builds the Python package. |
| Base runtime | None | Core package avoids mandatory external runtime dependencies. |
| `api` | `fastapi>=0.110`, `uvicorn>=0.29`, `cryptography>=42` | Runs the HTTP API and its cryptographic protections. |
| `browser` | `playwright>=1.62` | Provides browser automation support. |
| `media` | `huggingface-hub>=0.34` | Supports media/model-hub interactions. |
| `security` | `cryptography>=42`, `tuf>=6` | Supports cryptography and The Update Framework metadata. |
| `dev` | `pytest>=8.0`, `httpx2>=0.1` | Declares test/development tooling. The test run initially required installing `pytest`. |

The defined console scripts are `orville-api`, `orville`, and `orville-python-mcp`. Docker installs the API and security optional extras, runs as a non-root `orville` user, stores SQLite state at `/var/lib/orville/orville.db`, and exposes port 8787. Docker Compose deploys that API behind Caddy using an internal bridge network and persistent data volumes. [2] [3]

## Test execution and status

The README documents `python -m unittest discover -s tests -v` as the full configured test-suite command. The first execution could not fully collect the suite because the local environment lacked `pytest`, which project tests import. After installing `pytest 9.1.1`, the exact documented discovery command was re-run. [1] [4]

| Command | Result | Details |
|---|---|---|
| `python3 -m unittest discover -s tests -v` before test dependency installation | Incomplete execution | 487 tests in 8.331 seconds; 7 failures and 51 errors, including 48 import errors caused by missing `pytest`. |
| `python3 -m unittest discover -s tests -v` after installing `pytest>=8.0` | **Failed** | 444 tests in 7.739 seconds; **7 failures, 8 errors**, exit code 1. |

### Remaining errors after dependency installation

| Affected test(s) | Observed cause |
|---|---|
| `test_dashboard`, `test_gui_degraded_availability`, `test_gui_performance_measurement`, `test_gui_sensitive_data`, `test_workflow_state_handling` | `ModuleNotFoundError: No module named 'tkinter'` in the current Linux test environment. |
| `test_preview_runtime.PreviewRuntimeTests.test_start_status_http_and_stop` | Connection refused while attempting the preview runtime HTTP check. |
| `test_visual_regression.VisualRegressionTests.test_changed_baseline_fails_closed`; `test_current_assets_match_committed_baseline` | Required file `artifacts/visual_regression_baseline.json` is absent. |

### Remaining assertion failures after dependency installation

| Affected test | Observed mismatch |
|---|---|
| `test_execution_monitor.ExecutionMonitorTests.test_monitor_uses_safe_bounded_output` | An expected safe-message string was not present in the inspected UI source. |
| `test_operator_runbook.OperatorRunbookTests.test_referenced_procedures_exist_and_no_secrets_are_embedded` | A referenced procedure could not be resolved under the test's current path handling. |
| `test_orchestration.OrchestrationTests.test_checkpoint_file_is_valid_json` | The test expects checkpoint `schema_version` 1, while produced data reports 2. |
| `test_orchestration.OrchestrationTests.test_task_timeout_is_persisted_as_failure` | The test expected a timeout indication in a persisted failure-event field, but that field was empty. |
| `test_orchestration_test_matrix.OrchestrationTestMatrixTests.test_each_matrix_row_references_existing_test_modules` | A test-matrix file reference could not be resolved. |
| `test_reusable_fixes.ReusableFixesTests.test_each_fix_has_problem_assets_and_reuse_rule` | A configured reusable-fix asset reference could not be resolved. |
| `test_standalone_readme.StandaloneReadmeTests.test_referenced_local_contracts_exist` | A README-referenced local contract could not be resolved. |

The three reference-resolution failures visibly transform forward slashes to backslashes before evaluating local paths. On this Linux checkout, that behavior produces a path different from the actual forward-slash file path. That is an observed cross-platform test-path issue; correcting it requires a code/test change and was not performed during this assessment.

## README purpose and usage

The README identifies the project as **Orville**, describes prerequisites, editable installation, configuration through environment variables, local API operation, project checks, operational reports, deployment targeting, test commands, troubleshooting, security boundaries, and standalone limitations. The complete, unmodified `README.md` is supplied as a separate attachment for direct reading. [1]

> The repository provides local contracts, deterministic fixtures, and provider-neutral adapters. Hosted identity, external connectors, browser sessions, live model providers, production deployment, centralized observability, infrastructure alerting, code signing, and enterprise secret managers require separately configured and authorized environments. [1]

## Reproducibility artifacts

| Artifact | Content |
|---|---|
| `artifacts/test_runs/unittest_discover_2026-08-27.log` | Initial discovery execution, before `pytest` was available. |
| `artifacts/test_runs/unittest_discover_with_pytest_2026-08-27.log` | Final documented full-suite test log used for this assessment. |
| `artifacts/project_assessment_2026-08-27.md` | This report. |

## References

[1]: https://github.com/Ravn420/Orville-Automation-Agent/blob/5825bcb3f936c573953c553dd493669d5963003c/README.md "Orville README at the assessed revision"
[2]: https://github.com/Ravn420/Orville-Automation-Agent/blob/5825bcb3f936c573953c553dd493669d5963003c/pyproject.toml "Project metadata and dependency declarations"
[3]: https://github.com/Ravn420/Orville-Automation-Agent/blob/5825bcb3f936c573953c553dd493669d5963003c/Dockerfile "Orville Docker runtime"
[4]: https://github.com/Ravn420/Orville-Automation-Agent/tree/5825bcb3f936c573953c553dd493669d5963003c/tests "Orville test suite at the assessed revision"
