# Orville AI Agent Platform Setup

## Requirements

Use Python 3.10 or newer. Install the package from the repository root with `python -m pip install -e .`. Install the optional API dependencies with `python -m pip install -e '.[api]'`.

## Existing orchestration API

Set a long random bearer token in `ORVILLE_API_TOKEN`, then start the API with `python -m orville_core.api`. The default bind address is `127.0.0.1:8787`; keep it local unless an authenticated reverse proxy and production identity adapter are configured.

## Milestone 1 control-plane flow

Create a project with `POST /api/v1/projects`, create a task with `POST /api/v1/projects/{project_id}/tasks`, create an editable plan with `POST /api/v1/tasks/{task_id}/plan`, and approve or reject it with `POST /api/v1/plans/{plan_id}/approve`. Retrieve sanitized activity events with `GET /api/v1/tasks/{task_id}/events?after=0`.

Plan rejection is non-mutating with respect to repository files. Plan approval moves the task to `workspace_ready`; actual repository execution requires a later workspace/task adapter.

## Validation

Run `python -m unittest discover -s tests -v` and `python -m compileall -q orville_core tests examples`. The test suite covers legacy orchestration behavior, API authentication and intake, control-plane lifecycle, secret redaction, event cursors, workspace path restrictions, checksum-guarded writes, allowlisted commands, revisions, and rollback.

## Environment and secrets

Keep provider credentials in environment variables or a future secret manager. Do not place credentials in source files, task requests, plans, event payloads, artifacts, screenshots, or downloaded archives. The current API is a development/local bridge and is not a substitute for production identity, encrypted secret storage, or hardened sandbox infrastructure.
