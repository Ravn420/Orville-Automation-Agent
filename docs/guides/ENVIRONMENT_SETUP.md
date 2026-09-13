# Orville Environment Setup

## Supported baseline

Orville targets Python 3.10 or newer. The core package uses the Python standard library. API execution additionally requires FastAPI and Uvicorn; browser automation and media integrations are optional extras.

## Linux

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[api]'
python -m compileall -q orville_core tests examples
python -m pytest -q
python -m orville_core.cli runtime-health
```

Use `python -m orville_core.cli` when the package entry point is not installed. Store runtime configuration outside the repository and never commit provider credentials.

## Windows PowerShell

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[api]"
python -m compileall -q orville_core tests examples
python -m pytest -q
python -m orville_core.cli runtime-health
```

If PowerShell execution policy prevents activation, invoke `.venv\Scripts\python.exe` directly. The Windows launchers may be used after the environment passes the same compile and test commands.

## Container

```bash
docker build -t orville:local .
docker run --rm -p 8000:8000 --env-file .env.example orville:local
```

Production containers must receive secrets through the deployment secret manager. Do not bake `.env.production` or provider credentials into an image layer.

## Validation policy

A clean-environment validation is complete only when dependency installation succeeds, `orville runtime-health` reports required commands, compilation succeeds, the full test suite passes, and the API health endpoint responds. Optional tools may be unavailable when the corresponding feature is not being used, but the report must record that state.

## M13.7 security release gate

The M13.7 gate validates the optional security runtime dependencies before accepting a security release. Install the security extras in the active Python environment before running the gate:

```powershell
python -m pip install -e ".[security]"
python tools/release_gate.py
```

The gate intentionally fails closed when `cryptography` is unavailable because Ed25519 attestation verification cannot be considered active without it. TUF integration requires the declared `tuf` security extra when `required_tuf` policy is used.

## Safe provider configuration examples

Use `.env.example` as the client configuration template. It contains placeholders and explicit variables for the API token, REST/MCP endpoints, local provider, and optional managed relay URL, model, host allowlist, plan, and subject. Do not add `BLACKBOX_API_KEY` or user-connected Blackbox credentials to this file; the managed provider credential belongs only in the relay server process environment, and user-connected credentials belong in the operating-system credential store.

For the Windows registration smoke test, provide `ORVILLE_API_TOKEN` through the process environment and optionally set `ORVILLE_API_BASE_URL`. The smoke test never reads a project credential file and never contacts Blackbox.
