# Frontend–Backend Contracts and Environment Configuration

## Summary

This document defines the stable contract between an Orville frontend client and the optional FastAPI bridge. It is usable by the existing static GUI, future web clients, and native clients without coupling the frontend to provider credentials or a deployment-specific host.

## Contract ownership and compatibility

The backend owns authentication, authorization, task normalization, execution state, approval state, checkpoint persistence, provider configuration, and secret handling. The frontend owns presentation, local input validation, request cancellation, accessible status messaging, and in-memory session state. The frontend must treat all backend values as untrusted data and must not infer authorization from a successful HTTP response alone.

The API base URL is supplied at runtime. A client must not hard-code a production URL, embed provider credentials, or expose server-only environment variables through a public build. Backward-compatible additions may add response fields, error details, or routes. Existing fields and meanings must not be removed or changed without a versioned contract update.

## Transport and common headers

The current API prefix is `/api/v1`. Requests use JSON unless a route says otherwise. Clients send `Accept: application/json` and `Content-Type: application/json` for JSON bodies. Authorized requests send `Authorization: Bearer <runtime token>`; the token is held in memory only and is never written to localStorage, sessionStorage, URLs, telemetry, or frontend build output. The backend must never return the token or provider credentials.

The backend may include a correlation identifier in `X-Request-Id`. Clients should preserve it in diagnostic context without displaying it as a secret. CORS, TLS termination, rate limiting, and durable identity enforcement are deployment responsibilities and must be configured before a non-local exposure.

## Response envelopes

Successful responses return the route-specific JSON object. Collection responses use a stable `items` array and may include pagination metadata. A client must ignore unknown fields.

Errors use the following envelope for all authenticated API routes:

```json
{
  "error": {
    "code": "run_not_found",
    "message": "Unable to load the requested run.",
    "operation": "get_run",
    "retryable": false,
    "request_id": "safe-request-id"
  }
}
```

`code` is a stable machine-readable identifier. `message` is safe for end-user display and identifies the failed operation without including bearer tokens, API keys, cookies, authorization headers, environment-variable values, full exception strings, filesystem secrets, or raw provider responses. `operation` is a short allowlisted operation name such as `health_check`, `create_objective`, `execute_run`, `load_run`, `list_events`, `cancel_run`, `update_approval`, `read_state`, `list_artifacts`, or `get_artifact`. `retryable` tells the client whether bounded retry may be appropriate; clients must not retry authentication, authorization, validation, or approval failures automatically. `request_id` is optional and contains only a safe diagnostic identifier.

The backend maps internal exceptions to stable codes and logs the detailed exception only through the repository's secret-redaction boundary. The frontend displays `message`, not raw exception text or response bodies from upstream providers.

| HTTP status | Error code family | Client behavior |
|---|---|---|
| 400 | `invalid_request`, `invalid_json` | Correct the request and do not retry unchanged input. |
| 401 | `authentication_required`, `authentication_failed` | Clear in-memory session state and request re-authentication. |
| 403 | `forbidden`, `approval_required` | Stop the operation and show the required authorization or approval state. |
| 404 | `run_not_found`, `artifact_not_found`, `route_not_found` | Treat the resource as unavailable; do not retry unchanged input. |
| 409 | `execution_unavailable`, `state_conflict`, `idempotency_conflict` | Refresh state and show the operation-specific conflict. |
| 413 | `payload_too_large` | Reduce input size; do not retry unchanged input. |
| 429 | `rate_limited` | Retry only when bounded backoff is permitted and the server provides a safe retry hint. |
| 500 | `internal_error` | Show a generic operation-specific message and record only the request ID. |
| 502/503/504 | `upstream_unavailable`, `service_unavailable`, `request_timeout` | Retry at most within the client retry budget; preserve the operation name. |

## Route contracts

The following routes are the current minimum integration surface. Request and response bodies may gain additive fields, but route purpose and authentication requirements remain stable.

| Method | Route | Request | Response purpose |
|---|---|---|---|
| GET | `/api/v1/health` | None | Authenticated readiness and service status. |
| POST | `/api/v1/objectives` | Normalized objective input | Creates a run/task graph and returns its identifier and state. |
| POST | `/api/v1/objectives/{run_id}/execute` | Optional execution controls | Starts or resumes execution; returns run state and event cursor. |
| GET | `/api/v1/runs/{run_id}` | None | Returns persisted run/checkpoint state. |
| GET | `/api/v1/runs/{run_id}/events` | Optional cursor/limit | Returns bounded execution events for polling or stream adaptation. |
| POST | `/api/v1/runs/{run_id}/cancel` | Cancellation reason | Records a cancellation request and returns the resulting state. |
| POST | `/api/v1/runs/{run_id}/tasks/{task_id}/approval` | Approval decision and safe reference | Records an approval or rejection without accepting secret material. |
| GET | `/api/v1/state` | None | Returns the current project-state schema and safe metadata. |
| GET | `/api/v1/artifacts` | None | Lists root-bound artifact metadata only. |
| GET | `/api/v1/artifacts/{relative_path}` | None | Retrieves an approved root-bound artifact. |

Clients must treat run execution, cancellation, approval, and artifact retrieval as state-changing or sensitive operations even when the HTTP method is read-like. UI controls must show the current state, disable duplicate submissions while a request is pending, and use an idempotency key when the backend contract requires one.

## Environment-specific configuration

Configuration is selected by the process environment, not by frontend source edits. The checked-in example at `config/frontend-backend.example.json` is non-secret documentation input; deployment systems may translate it into environment variables or a protected runtime configuration store.

| Variable | Local default | Staging/production rule | Exposure |
|---|---|---|---|
| `ORVILLE_API_HOST` | `127.0.0.1` | Bind to the approved interface or service mesh address. | Backend only |
| `ORVILLE_API_PORT` | `8787` | Use the assigned service port. | Backend only |
| `ORVILLE_API_TOKEN` | Unset; required for authenticated startup | Inject from an approved secret store or protected OS environment. | Backend only |
| `ORVILLE_API_BASE_URL` | `http://127.0.0.1:8787` | Use the TLS-terminated public/service URL. | Frontend runtime configuration; never a secret |
| `ORVILLE_API_TIMEOUT_SECONDS` | `10` | Use a bounded value appropriate to the deployment. | Frontend/backend as applicable |
| `ORVILLE_API_RETRY_ATTEMPTS` | `2` | Keep within the client and gateway retry budget. | Frontend runtime configuration |
| `ORVILLE_ALLOWED_ORIGINS` | `http://127.0.0.1:3000` | Explicitly allowlist deployed frontend origins; never use `*` with credentials. | Backend only |
| `ORVILLE_ENVIRONMENT` | `local` | Set to `staging` or `production` through deployment configuration. | Non-secret metadata |

For a static frontend, `ORVILLE_API_BASE_URL`, timeout, retry budget, and environment label may be generated into a runtime `config.json` served beside the application. `ORVILLE_API_TOKEN` and all provider credentials must remain server-side; a frontend must use an approved session mechanism or in-memory token supplied through an explicit user-authentication flow. Never place secrets in `VITE_*`, `NEXT_PUBLIC_*`, static HTML, source maps, query parameters, or committed `.env` files.

## Environment validation

Startup validation must reject missing or malformed backend authentication configuration, invalid ports, negative timeouts, invalid retry counts, and non-allowlisted origins. Local development may use loopback HTTP. Staging and production require TLS at the ingress boundary, explicit origin allowlists, durable identity and authorization, rate limiting, redacted logs, and an operator-owned secret injection path. The example configuration is not production-ready until these deployment-owned controls are supplied.

## Client behavior and testing

A conforming client validates JSON shape before rendering, handles every listed status family, preserves request IDs for safe diagnostics, and does not display raw response bodies on unexpected failures. Focused tests should cover successful health and objective flows, malformed requests, authentication and authorization rejection, missing runs or artifacts, unavailable execution, bounded rate-limit retry, and assertions that representative error text does not contain synthetic tokens or provider credentials.

## Related files

- `API_BRIDGE.md` — existing route and authentication overview.
- `config/frontend-backend.example.json` — non-secret environment contract example.
- `tests/test_frontend_backend_contract.py` — contract fixture and redaction checks.
