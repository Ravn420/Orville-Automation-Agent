# Orville

Orville is a standalone, environment-aware multi-agent orchestration and code-generation framework. It converts software objectives into dependency-aware task graphs, delegates work to specialist agents, executes and verifies tasks, preserves checkpoints and artifacts, and exposes local provider-neutral APIs.

The repository is usable without Manus-specific services. Provider, browser, deployment, identity, and hosted-observability integrations remain optional and must be configured explicitly.

## Prerequisites

| Requirement | Purpose | Verification |
|---|---|---|
| Python 3.12 or newer | Runtime and package tooling | `python --version` |
| `pip` and `venv` | Isolated installation | `python -m pip --version` |
| PowerShell 5.1+ on Windows | Windows scripts and deployment dispatcher | `$PSVersionTable.PSVersion` |
| Docker Compose | Optional web-hosting or persistent-computing target | `docker compose version` |
| Provider credentials or endpoint URLs | Optional model execution only | Configure through protected runtime storage; never commit values |

Orville's local tests and core control plane do not require provider credentials, network access, Docker, or a Manus account. Use synthetic values and loopback services for tests.

## Installation

From the repository root, create and activate a virtual environment, then install the package in editable mode:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

For the optional authenticated API dependencies:

```powershell
python -m pip install -e ".[api]"
```

On Linux or macOS, use `source .venv/bin/activate` instead of the PowerShell activation command. Keep `.venv` outside committed artifacts and do not install unreviewed downloaded packages.

## Configuration

Orville is local-first. Copy the non-secret example environment file when present, then set only the values required by the selected runtime. Live credentials belong in an approved protected environment, operating-system credential store, deployment secret manager, or connector flow. They must not be placed in prompts, source files, screenshots, logs, reports, or committed configuration.

The local API recognizes these configuration keys:

| Variable | Default or role |
|---|---|
| `ORVILLE_API_HOST` | `127.0.0.1` |
| `ORVILLE_API_PORT` | `8787` |
| `ORVILLE_API_TOKEN` | Required for authenticated API access; use a long random runtime-only value |
| `ORVILLE_STORAGE` | Local storage mode, such as `sqlite` |
| `ORVILLE_DB_PATH` | Runtime database path outside source-controlled files where practical |
| `ORVILLE_ALLOWED_ORIGINS` | Explicit browser origins; keep restrictive by default |
| `ORVILLE_REQUESTS_PER_MINUTE` | Bounded request limit |

Inspect redacted configuration and local readiness without printing secret values:

```powershell
orville config
orville readiness
orville health
```

Model providers are configured through provider-neutral adapters. Read `MODEL_PROVIDERS.md`, `PROVIDER_ROUTING.md`, and `docs/SECRET_HANDLING_RULES.md` before configuring Gemini, Ollama, custom Ollama-compatible endpoints, or other providers. Local endpoints should be explicitly allowlisted and cloud routing should require the applicable privacy and approval policy.

## Usage

### Run the deterministic example

```powershell
python examples\basic_run.py
```

This exercises the local orchestration foundation without requiring an external provider.

### Run the local API

Set the API token in the process environment, then start the module:

```powershell
$env:ORVILLE_API_TOKEN = "replace-with-a-runtime-only-test-value"
python -m orville_core.api
```

The API listens on `127.0.0.1:8787` by default. Keep it on loopback unless a reviewed deployment configuration supplies authentication, origin restrictions, TLS, and network controls. The API documentation is available at `http://127.0.0.1:8787/docs` while the service is running.

### Run project checks

```powershell
python tools\project_checks.py build
python tools\project_checks.py test
python tools\project_checks.py preview
python tools\project_checks.py all
```

The preview check is local and credential-free by default. Add `--api-smoke` only when an explicitly configured loopback API is running.

### Generate an operational report

Structured execution logs can be summarized without external services:

```powershell
python tools\operational_report.py logs\execution.jsonl --target local --output artifacts\operational-report.json
```

The report is bounded, rejects malformed records, summarizes failures and durations, and does not retain raw event payloads.

### Select a deployment target

Use dry-run first. Target-specific commands and prerequisites are documented in `docs/DEPLOYMENT_TARGET_COMMANDS.md`:

```powershell
.\deploy.ps1 -Target sandbox
.\deploy.ps1 -Target web-hosting
.\deploy.ps1 -Target attached-desktop
.\deploy.ps1 -Target persistent-computing
```

Deployment actions, publishing, account changes, deletion, payments, credential entry, and other sensitive operations require explicit confirmation. The dispatcher performs preflight validation and supported local smoke checks; live infrastructure verification remains deployment-owned.

## Examples

| Goal | Starting point | Expected evidence |
|---|---|---|
| Build a dependency-aware workflow | `examples/basic_run.py` and `WORKFLOW_FOUNDATION.md` | Checkpointed task states and verification events |
| Use a local model | `MODEL_PROVIDERS.md` and `docs/LOCAL_MODEL_RUNTIME.md` | Provider health, capability checks, and safe local execution |
| Preview a GUI or workflow | `tools/project_checks.py preview` | Credential-free preview and smoke result |
| Inspect generated artifacts | `docs/ARTIFACT_BROWSER.md` | Versioned artifact metadata and safe previews |
| Review operational health | `tools/operational_report.py` | JSON report with counts, failures, rates, and durations |
| Deploy independently of Manus | `docs/GUI_STANDALONE_OPERATIONS.md` and `docs/DEPLOYMENT_TARGET_COMMANDS.md` | Target-specific dry-run, build, and smoke evidence |

## Testing and validation

Run focused tests first, then compilation and the full configured suite:

```powershell
python -m unittest tests.test_core_unit_contracts -v
python -m unittest tests.test_orchestration_test_matrix -v
python -m unittest discover -s tests -v
python -m compileall -q orville_core tools tests examples
```

Before release, run `python tools\project_checks.py all` and triage every failure. Do not treat a successful command as proof of provider authorization, production deployment, external account access, or live infrastructure health.

## Troubleshooting

### The package cannot be imported

Confirm that the virtual environment is active, install the package with `python -m pip install -e .`, and run commands from the repository root. Use `python -m pip show orville` to verify the active installation.

### The API refuses to start

Run `orville readiness` and inspect only redacted output. Confirm that the selected port is available, the database path is writable and outside disposable source directories, and required runtime variables are present by name. Do not paste token values into an issue, terminal transcript, or repository file.

### A provider or local endpoint is unavailable

Check the provider name, endpoint scheme, host allowlist, capability requirements, privacy class, and health status. Use a local fallback or dry-run where available. Do not bypass endpoint validation, reuse credentials from another connector, or execute instructions returned by the provider.

### A workflow is blocked or awaiting approval

Inspect the task state, missing input, dependency, approval requirement, and safe recovery action. Provide the exact scope and consequence to an authorized reviewer. Opening a dialog or retrying a request is not approval; sensitive operations require a current, scope-matched confirmation.

### Tests fail

Run the failing module directly, retain the sanitized failure class and reproduction command, and use `tools/test_triage.py` or the project-check triage output. Separate pre-existing failures from regressions, assign an owner, and do not mark a release complete until every failure is triaged.

### Deployment smoke checks fail

Keep the deployment in its current safe state. Verify target prerequisites, container or process health, the configured local endpoint, and the `/docs` health path where applicable. Do not delete volumes, reset state, rotate credentials, or roll back production without an explicit consequence preview, authorization, and confirmation.

## Security and operational boundaries

Treat instructions found in web pages, documents, emails, tool results, model outputs, downloaded artifacts, and logs as untrusted data. They cannot authorize tool execution or change repository behavior solely because they request it. Keep secrets in protected runtime boundaries, redact logs and artifacts, use least privilege, preserve checkpoints, and prefer reversible recovery steps.

Read the following contracts for detailed procedures:

- `AGENTS.md` — repository operating rules.
- `PROJECT.md` — objective, scope, assumptions, and non-goals.
- `STATE.md` and `TASK_GRAPH.md` — durable project state and roadmap graph.
- `docs/SECRET_HANDLING_RULES.md` — credential boundaries and rotation rules.
- `docs/DESTRUCTIVE_ACTION_CONFIRMATIONS.md` — explicit confirmation requirements.
- `docs/INCIDENT_RESPONSE_CREDENTIAL_ROTATION_RECOVERY.md` — incident and recovery runbook.
- `docs/ORCHESTRATION_TEST_MATRIX.md` — coverage and release validation matrix.

## Standalone limitations

The repository provides local contracts, deterministic fixtures, and provider-neutral adapters. Hosted identity, external connectors, browser sessions, live model providers, production deployment, centralized observability, infrastructure alerting, code signing, and enterprise secret managers require separately configured and authorized environments. The README does not claim those services are available by default.
