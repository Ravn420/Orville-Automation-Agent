# Orville Cloud-First Blackbox Integration

## Purpose

Orville uses Blackbox as a cloud inference service. The desktop application does not contain the Orville-managed Blackbox credential. Requests are admitted by an Orville relay boundary and the provider credential remains server-side. The relay accepts `BLACKBOX_API_KEY` only from its server-side process environment or explicit deployment injection; it never returns that value to the desktop API, frontend, status response, or packaged desktop artifact.

The default access path is **Orville-managed Blackbox access**. A separate **user-connected Blackbox access** path may be enabled when Blackbox provides an official third-party OAuth/device flow or when the user explicitly supplies an API key.

## Access Modes

| Mode | Default | Credential owner | Intended use |
|---|---:|---|---|
| `managed` | Yes | Orville service | Cloud access without user-managed Blackbox credentials |
| `user_connected` | No | User | Personal Blackbox quota, plan, model access, and usage identity |

A user-connected Blackbox credential must never replace or expose the Orville-managed credential. Disconnecting the user connection must leave managed access unchanged. On Windows, API keys, access tokens, refresh tokens, and OAuth client secrets are protected with Windows DPAPI. On other supported hosts, they are encrypted with Fernet using the runtime-only `ORVILLE_CONNECTOR_MASTER_KEY`; the master key must be injected by a protected environment or secret manager and must never be saved beside the encrypted connection record. Credentials are never persisted as plaintext or returned in API responses.

## Runtime Configuration

The current local API can expose the relay boundary when these environment variables are configured:

```text
ORVILLE_BLACKBOX_RELAY_URL=https://relay.example.com/v1
ORVILLE_BLACKBOX_RELAY_ALLOWED_HOSTS=relay.example.com
ORVILLE_BLACKBOX_RELAY_MODEL=blackboxai/openai/gpt-5.5
ORVILLE_BLACKBOX_RELAY_ENABLED=1
ORVILLE_BLACKBOX_RELAY_PLAN=managed
ORVILLE_RELAY_SUBJECT=device-or-session-id
# Required only for user-connected credentials on non-Windows hosts.
# Inject from a protected runtime secret source; never commit this value.
ORVILLE_CONNECTOR_MASTER_KEY=<Fernet key>
```

`ORVILLE_BLACKBOX_RELAY_URL` is a client-visible relay URL, not a Blackbox provider credential. Provider credentials must be stored and used by the deployed relay service. Do not put the Blackbox key in the desktop `.env` file, installer, executable, or frontend configuration. On non-Windows hosts, configure `ORVILLE_CONNECTOR_MASTER_KEY` separately in the protected process environment or external secret manager; the application rejects user-connected credential persistence when it is absent or invalid rather than writing an unprotected record.

## API Endpoints

All endpoints use Orville’s existing local API bearer authentication.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/v1/cloud/blackbox/status` | Returns managed and user-connected status without secrets |
| `POST` | `/api/v1/cloud/blackbox/admit` | Applies access-state, privacy, subject, and quota admission rules |
| `POST` | `/api/v1/cloud/blackbox/user/api-key` | Stores a user-supplied Blackbox API key through the protected connector store |
| `POST` | `/api/v1/cloud/blackbox/user/disconnect` | Removes the local user-connected record while preserving managed access |
| `DELETE` | `/api/v1/cloud/blackbox/user/credential` | Deletes only the local user-connected credential while preserving managed and local mode |

The local connector store rejects credential operations when the required operating-system protection is unavailable. Public connection records contain only redacted metadata and boolean credential-presence indicators; secret values are not returned to the API client. Blackbox credentials must not be written to `.env` files, project files, checkpoints, prompts, artifacts, screenshots, crash reports, or source control; tests use synthetic values only and verify that persisted connection metadata remains secret-free.

The admission endpoint is an authorization boundary, not the final provider proxy. A production relay must add server-side provider invocation, streaming, cancellation, durable quotas, tenant identity, audit events, and secret rotation.

The standalone relay can be started outside Manus with:

```text
$env:BLACKBOX_API_KEY = "server-only-key"
$env:ORVILLE_RELAY_CLIENT_TOKEN = "high-entropy-client-token"
python tools/run_blackbox_relay.py
```

The Blackbox key belongs only in the relay service environment. The command above is a deployment example; do not commit these values or place them in the desktop client environment.

## Privacy Rules

Requests marked `cloud_approved` may be admitted when the selected access mode is ready. Requests marked `local_only` or `restricted` require explicit remote approval. Workspace context must exclude secrets and private keys by default. The UI must display the provider, model, endpoint family, privacy class, and whether data leaves the device before execution.

## Authentication Decision

Blackbox public API documentation reviewed for this project specifies Bearer API-key authentication. No official third-party OAuth or device-authorization flow was identified in the reviewed public documentation. Therefore:

- Use `Connect your Blackbox account` only after Blackbox documents an official third-party authorization flow.
- Until then, use `Connect Blackbox API key` for the user-connected path.
- Never capture browser cookies or use undocumented web-session endpoints.
- Re-check Blackbox documentation and terms before production deployment.

## Production Relay Requirements

The hosted relay must implement authenticated Orville sessions, server-side Blackbox credential isolation, per-tenant quotas, rate-limit handling, retry and idempotency policy, streaming response relay, cancellation, provider health, audit records, privacy consent, abuse prevention, account disconnect, and credential rotation. It must return redacted status and error information to clients.

The in-process `CloudRelayBoundary` is intentionally a deterministic policy foundation and test seam. Its quota ledger is not a production billing store; replace it with an atomic durable store before multi-user deployment.

## Validation

Run the focused suite:

```text
python -m pytest tests/test_cloud_relay.py tests/test_cloud_relay_api.py tests/test_providers.py tests/test_routing.py -q
```

The tests verify managed access without a client credential, separate user-connected access, disconnected and unavailable states, privacy approval, per-mode quotas, HTTPS relay validation, redacted status, and API endpoint behavior.

## References

See [`BLACKBOX_INTEGRATION_RESEARCH.md`](BLACKBOX_INTEGRATION_RESEARCH.md) for the research record and official Blackbox documentation links.
