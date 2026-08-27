# Orville API Bridge

## Purpose

The optional FastAPI bridge exposes the Python workflow foundation to an authorized GUI or other client. It keeps task intake, checkpoint storage, approval state, cancellation requests, and project-state access behind a bearer-token boundary.

## Install and run

```bash
python -m pip install -e '.[api]'
set ORVILLE_API_TOKEN=replace-with-a-long-random-secret
python -m orville_core.api
```

On POSIX shells, use `export ORVILLE_API_TOKEN=...` instead of `set`. The default bind address is `127.0.0.1:8787`; configure `ORVILLE_API_HOST`, `ORVILLE_API_PORT`, and `ORVILLE_API_TOKEN` through the environment.

## Routes

| Method | Route | Purpose |
|---|---|---|
| GET | `/api/v1/health` | Authenticated health check |
| POST | `/api/v1/objectives` | Normalize an objective into a task graph |
| POST | `/api/v1/objectives/{run_id}/execute` | Execute a normalized graph through injected handlers |
| GET | `/api/v1/runs/{run_id}` | Read a persisted checkpoint |
| GET | `/api/v1/runs/{run_id}/events` | Read persisted execution events for polling or later stream adaptation |
| POST | `/api/v1/runs/{run_id}/cancel` | Request run cancellation |
| POST | `/api/v1/runs/{run_id}/tasks/{task_id}/approval` | Approve or reject a task gate |
| GET | `/api/v1/state` | Read the current project-state schema |
| GET | `/api/v1/artifacts` | List root-bound artifact metadata |
| GET | `/api/v1/artifacts/{relative_path}` | Retrieve a root-bound artifact |

All routes require `Authorization: Bearer <token>`. The API does not return or log credential values. Production deployments must add TLS termination, a durable identity and authorization provider, rate limiting, CORS allowlists, CSRF protections where cookie auth is used, and a real run manager before exposing the bridge beyond localhost.

## Integration contract

The static GUI can be connected through a user-supplied API base URL and bearer token. The token should remain in memory only and should never be committed, placed in public frontend environment variables, or written to localStorage. The bridge is intentionally separate from model-provider credentials; provider secrets remain server-side.

## Limitations

Objective creation normalizes and stores the graph. Execution is available through `/api/v1/objectives/{run_id}/execute` when the application is created with a handler registry or an injected `OrchestrationEngine`; the bridge fails closed with HTTP 409 when no handlers are configured. Artifact storage, SSE/WebSocket push events, persistent user identities, authorization scopes, and database-backed state are subsequent integration requirements. The GUI client includes in-memory authentication and persisted-event retrieval primitives; it does not store bearer tokens in browser storage.
