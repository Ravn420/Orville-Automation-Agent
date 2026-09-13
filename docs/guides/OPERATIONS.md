# Orville Operations Guide

## Summary

Orville can run independently of Manus as a Python package and API service. The API uses SQLite checkpoint persistence by default, supports JSON checkpoints as a compatibility mode, exposes authenticated run and artifact endpoints, and provides a reconnectable Server-Sent Events stream for execution events.

## Installation

Create a virtual environment with Python 3.10 or newer, install the package, and install API dependencies when the HTTP bridge is required:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .[api]
```

On Windows PowerShell, activate with `.venv\\Scripts\\Activate.ps1`.

## API configuration

Set `ORVILLE_API_TOKEN` to a high-entropy secret before starting the service. Set `ORVILLE_DB_PATH` to the durable SQLite database location. `ORVILLE_STORAGE=sqlite` is the default; use `ORVILLE_STORAGE=json` only when compatibility with the legacy checkpoint directory is required. `ORVILLE_API_HOST` and `ORVILLE_API_PORT` control the bind address and port. Configure the GUI origin explicitly with `create_app(allowed_origins=[...])` in deployments rather than relying on the localhost default.

Start the service with:

```bash
orville-api
```

Every API route requires `Authorization: Bearer <token>`. The service supports objective creation, restart-compatible run retrieval, cancellation requests, approval mutations, artifact listing/retrieval, and event history. Live monitoring is available at `/api/v1/runs/{run_id}/events/stream?last_event_id=N` with `text/event-stream` responses and stable event IDs.

## CLI inspection

The standalone CLI does not require FastAPI:

```bash
orville --database .orville/orville.db health
orville --database .orville/orville.db runs
orville --database .orville/orville.db show <run-id>
```

## Security requirements

Keep the database and artifact root outside public static directories. Do not place provider keys in prompts, task context, browser storage, or logs. Use the existing filesystem, network, tool, and secret-redaction policies for task handlers. Local model activation must be explicitly validated for runtime availability, resource capacity, file readability, checksum, and license/provenance metadata before execution.

The current API token validator is appropriate for a single-process deployment or local control plane. Production multi-user deployments still require an external identity provider, scoped authorization, TLS termination, durable audit logging, and distributed rate limiting.

## Recovery procedure

SQLite checkpoints are updated after each material engine transition. If a process stops, construct a new `SQLiteCheckpointStore` against the same database and resume the run using the checkpoint's `run_id` and graph. Runs that were waiting for approval can be approved through the API before resuming. Cancellation is persisted as a context flag and is honored at the next engine boundary.

## Validation

Run the complete backend suite with `python -m unittest discover -s tests -v`, compile with `python -m compileall -q orville_core tests examples`, and build the GUI with `pnpm run check && pnpm run build`. A clean-environment acceptance run must also verify installation from `pyproject.toml`, database creation, token rejection, objective persistence across API process recreation, artifact traversal rejection, and SSE event replay.
