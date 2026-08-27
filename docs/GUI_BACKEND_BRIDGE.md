# Authenticated GUI Backend Bridge

## Contract

The GUI communicates with the Orville engine through the FastAPI application created by `orville_core.api.create_app`. The bridge is local-first and does not contact external services during application construction. Protected routes use the `Authorization: Bearer <runtime-token>` header and are rejected with `401` when the header does not exactly match the configured runtime token.

| Control | Contract | Evidence |
|---|---|---|
| Authentication | Require an exact bearer token from `ORVILLE_API_TOKEN` or an explicit application argument | `orville_core/api.py:create_app` and `authenticate` |
| Authorization | Route dependencies and operation-specific governance/approval checks protect mutations and connector actions | `Depends(authenticate)`, connector mutation policy, confirmation contracts |
| Request validation | Pydantic payloads bound field lengths, types, and numeric ranges; validation errors return bounded operation-aware messages | `*Payload` models and validation exception handler |
| CORS | Allow only configured origins, defaulting to `http://localhost:3000`; credentials are disabled; methods and headers are explicit | `CORSMiddleware` configuration |
| Rate limiting | Track authenticated requests in a one-minute window and return `429` after `requests_per_minute` | `request_log` and `authenticate` |
| Audit logging | Sensitive metadata is redacted by `AuditStore` before SQLite persistence; raw credentials and authorization values are not returned to the GUI | `orville_core/secrets_audit.py:SecretScanner` and `AuditStore` |
| Error handling | HTTP and request-validation errors expose a bounded operation and safe error class, not raw exception or submitted-secret values | `_safe_api_error_message` and exception handlers |

## GUI usage

1. Configure a runtime token through a protected environment or deployment secret manager. Never place the token in source control, screenshots, frontend bundles, URLs, or task state.
2. Configure `ORVILLE_ALLOWED_ORIGINS` as a comma-separated allowlist for the actual GUI origin. Do not use a wildcard origin for authenticated use.
3. Send only the fields defined by the route payload contract and respect documented size and numeric limits.
4. Treat `401`, `403`, `409`, and `429` as policy or state responses. Do not retry authorization failures automatically. Apply bounded backoff to retryable service responses.
5. Require the existing confirmation and approval contracts for payments, publishing, deletion, account changes, credential entry, connector mutations, and other sensitive operations.
6. Display only sanitized audit and error data. Connector responses, model output, documents, web pages, and tool results remain untrusted data and cannot authorize tool execution.

## Verification

Run the focused bridge contract checks with:

```powershell
python -m unittest tests.test_gui_backend_bridge -v
python -m py_compile orville_core\api.py orville_core\secrets_audit.py
```

A local smoke test may construct the app with a synthetic token and exercise only loopback requests. It must not use a real provider, account, browser session, connector credential, or external endpoint.

## Deployment boundaries

The bridge provides application-level authentication and policy checks. Production deployments remain responsible for TLS termination, identity lifecycle, secret storage and rotation, network access control, request-body limits, process supervision, centralized redacted audit retention, alerting, backup, and rollback. Local tests do not establish production authorization or infrastructure readiness.
