# Orville Delivery Runbook

## Scope

This runbook describes how to install, configure, run, validate, deploy, and roll back Orville without requiring Manus. It applies to the current standalone Python backend and Signal Room fallback.

## Prerequisites

Use Python 3.10 or newer. API execution requires the dependencies declared by the `[api]` extra. Windows deployments require PowerShell and the repository's documented launcher scripts; container deployments require Docker.

## Setup

Linux:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[api]'
```

Windows PowerShell:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[api]"
```

Store runtime data under the configured AppData or portable data directory, not in the repository. Copy `.env.example` only as a template; replace placeholders through the process environment or the approved protected credential store. Never place provider credentials in source, frontend files, fixtures, or logs.

## Run

For the deterministic local demonstration:

```bash
python examples/basic_run.py
```

For the API bridge:

```bash
export ORVILLE_API_TOKEN='replace-with-a-long-random-secret'
python -m orville_core.api
```

On Windows PowerShell, set the token with `$env:ORVILLE_API_TOKEN = 'replace-with-a-long-random-secret'` before starting the API. Bind only to the intended local or deployment interface, and use the server-side relay for managed provider credentials.

## Test and validate

```bash
python -m compileall -q orville_core tests examples tools
python -m pytest -q
python -m unittest discover -s tests -q
python tools/signal_room_checks.py webui
```

A release candidate must also pass the clean-workspace example workflow and the independent review recorded in `artifacts/phase4-independent-review.md`. Review the latest sanitized validation results in `artifacts/phase4-validation-record.md`.

## Configuration

Use `.env.example` and `ENVIRONMENT_SETUP.md` for variable names and safe placeholders. The desktop client may use a credential reference or explicit user-supplied API-key fallback. Managed relay credentials remain server-side. Keep host allowlists, plan, subject, model, and privacy-routing settings explicit. Do not enable an external provider in tests unless a synthetic local boundary is being used.

## Deployment

The supported small-team production topology is Docker Compose with the `api` service on the private network, the `proxy` Caddy service on ports 80/443, and persistent `orville-data` and `caddy-data` volumes. For a disposable local container check, use:

```bash
docker build -t orville:local .
docker run --rm -p 8000:8000 --env-file .env.example orville:local
```

For an approved production promotion, use this sequence from a clean release checkout. Keep `.env.production` outside source control, inject secrets through the approved deployment secret manager, and never bake secrets into an image layer.

1. Record the release identifier, source revision, image digest, configuration schema version, and operator approval reference. Confirm that the target host, DNS, and ports 80/443 are correct.
2. Run the release checks before touching the live stack: `python -m compileall -q orville_core tests examples tools`, `python -m pytest -q`, the main workflow, and applicable UI checks. Retain sanitized results under the release evidence directory.
3. Create and verify a database backup before the upgrade. On a Windows operator host, run `powershell -ExecutionPolicy Bypass -File .\\deploy\\backup.ps1`; on other hosts, use an equivalent approved volume/database backup procedure. Store the copy outside the deployment host and record its checksum.
4. Review the effective non-secret Compose configuration with `docker compose --env-file .env.production config --quiet`. Confirm that the API is not publicly exposed, the intended domain is configured, and the persistent volume names are unchanged.
5. Build or pull the approved image, then start the stack with `docker compose --env-file .env.production up -d --build`. Do not scale the API beyond one replica while SQLite is the storage backend.
6. Verify `docker compose --env-file .env.production ps`, inspect startup logs for errors without printing secrets, and check the authenticated endpoint with `curl -fsS -H "Authorization: Bearer $ORVILLE_API_TOKEN" https://YOUR_DOMAIN/api/v1/health`. Complete a read-only checkpoint listing and the smoke workflow before declaring promotion successful.

Preserve the image digest, configuration schema version, backup checksum, test record, health result, smoke result, operator approval, and release notes as sanitized evidence. A failed preflight or post-deploy check stops promotion and enters the rollback procedure; it does not authorize an automatic destructive recovery.

## Rollback

Rollback is an approval-gated restoration to the last known-good release. Keep the current logs, database, backup, and release evidence; do not delete runtime databases, protected credential records, active logs, or release evidence.

1. Declare the rollback reason and scope, record the failed health or smoke check, and stop further promotion. If a credential may have been exposed, revoke or rotate it through the provider or protected credential manager before resuming service.
2. Preserve diagnostics with `docker compose --env-file .env.production logs --no-color --tail=500 api proxy`, after confirming the output contains no credentials.
3. Stop the new revision with `docker compose --env-file .env.production down` only after confirming that the command does not remove named volumes. Do not use `down --volumes`.
4. Restore the previously approved source checkout or image digest and the previously approved non-secret configuration. Start it with `docker compose --env-file .env.production up -d` (add `--build` only when the approved source must be rebuilt).
5. Verify the restored `/api/v1/health` endpoint, service status, read-only checkpoint listing, and smoke workflow. Compare each result with the retained validation record.
6. If the application data is inconsistent or the release requires a data restore, stop the stack, replace the database in `orville-data` with the verified backup, and start the stack again. Record the backup identifier and checksum; never overwrite a backup without retaining the original evidence.
7. Keep the failed release artifacts and rollback evidence for incident review. Mark the incident resolved only after the health, data-read, and smoke checks pass and the operator records the final release identifier.

For a container deployment without Compose, stop the new process or deployment revision, restore the previously approved image or source artifact, reapply the previously approved non-secret configuration through the deployment system, and perform the same health, read-only data, smoke, and evidence checks. Production deployment and provider-side rollback remain deployment-owned and require the target platform’s approval and audit controls.

## Known limitations

The official third-party Blackbox OAuth flow remains blocked until the provider publishes a documented flow. Managed relay and explicit API-key fallback are implemented, but live provider verification must be performed separately with authorized credentials and approval.
