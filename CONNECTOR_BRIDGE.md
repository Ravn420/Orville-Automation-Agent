# Orville Connector Access and Bridge

## Summary

The packaged Signal Room includes a dedicated **Connectors** menu for the 372-entry non-secret catalog. Users can select a service and connect it individually using a provider API key, bearer token, or OAuth2 authorization-code flow with PKCE. Orville records only redacted connection metadata in its API responses and protects stored credentials with Windows DPAPI.

The catalog is not an assertion that every service is enabled or that every provider shares one API protocol. Each service remains responsible for its official sign-in, scopes, endpoint, terms, and operation contract.

## User workflow

Open **Connectors** in the left Operations navigation or use the top-bar Connectors button. Search for a service, select it, and choose either **API key / bearer** or **OAuth2 sign-in**.

For a manual connection, enter the provider’s official connector endpoint, authentication type, credential header, credential, and scopes. The default header is `Authorization`; services such as `X-API-Key` can use their documented header. The local endpoint checkbox is required for loopback testing and is disabled by default.

For OAuth2, enter the provider’s official base URL, authorization URL, token URL, client ID, optional client secret, and scopes. Orville generates a state value and PKCE challenge, opens the provider sign-in page in a separate window, validates the callback state, and exchanges the authorization code locally. The access token is then protected with Windows DPAPI. OAuth client registration remains the user’s responsibility.

## Local API routes

| Route | Purpose |
|---|---|
| `GET /api/v1/connectors` | Returns the catalog count and redacted connection status. |
| `GET /api/v1/connector-connections` | Returns redacted signed-in connection records. |
| `POST /api/v1/connectors/{uid}/connect/manual` | Saves a manually configured API-key or bearer connection. |
| `POST /api/v1/connectors/{uid}/connect/oauth` | Starts an OAuth2 PKCE sign-in flow. |
| `GET /api/v1/connectors/{uid}/oauth/callback` | Validates state and completes the OAuth2 exchange. |
| `GET /api/v1/connectors/{uid}/operations` | Reads an operation catalog from the signed-in connector’s `/operations` endpoint. |
| `POST /api/v1/connectors/{uid}/invoke` | Invokes a signed-in connector after explicit approval. |
| `POST /api/v1/connectors/{uid}/disconnect` | Removes the local protected connection record. |

Every sensitive invocation requires `approved: true`. Connector IDs, operation names, request sizes, timeouts, response limits, and audit records are bounded. Secrets are not written to task state, API responses, UI state, or audit metadata.

## User-managed bridge compatibility

A separate bridge can still be configured when the user has an existing Manus-compatible connector service:

```env
ORVILLE_CONNECTOR_BRIDGE_URL=http://127.0.0.1:9999
ORVILLE_CONNECTOR_BRIDGE_TOKEN=<optional-bridge-token>
ORVILLE_CONNECTOR_BRIDGE_TIMEOUT=10
```

The external bridge exposes `GET /health` and `POST /invoke`. Its invocation body is:

```json
{
  "connector_uid": "github",
  "operation": "issues.list",
  "arguments": {"repo": "orville"},
  "run_id": "optional-run-id"
}
```

The standalone app prefers a locally signed-in connector when one exists and otherwise uses the configured external bridge. This permits per-connector sign-in for generic services while preserving compatibility with a bridge that already owns Manus OAuth sessions and provider-specific dispatch.

## Storage and security

Installed releases store `connector-connections.json` under `%LOCALAPPDATA%\Orville\data`. The file contains encrypted secret blobs and non-secret status metadata; it is not intended to be copied between Windows users. Portable releases store the same file beside the portable data directory. Use Windows account protection and normal filesystem permissions for the data directory.

Do not place provider credentials in task instructions, source repositories, screenshots, frontend local storage, or command-line arguments. Use the Connectors menu and rotate or disconnect credentials from the provider when access is no longer required.

## Validation

The regression suite covers manual sign-in, DPAPI-protected persistence, redaction, local endpoint approval, operation discovery, explicit invocation approval, local fixture invocation, and disconnect behavior. The frontend production build and packaged Windows executable must be rebuilt after source changes.


## Adapter registry and local Browser Operator relay

The release now exposes a provider-neutral adapter registry at `GET /api/v1/connector-adapters` and per-adapter operation discovery at `GET /api/v1/connector-adapters/{connector_id}/operations`. The initial manifests cover GitHub, Slack, Notion, Gmail, Google Calendar, Outlook Mail, Stripe, HubSpot, and n8n with explicit read/write/sensitive/critical risk classes. These manifests describe supported operation contracts; a provider-specific handler and successful user authorization are still required before a service is operational.

The local Browser Operator extension bundle is under `browser_extension/`. It uses Manifest V3 with `activeTab`, `scripting`, and `storage` permissions rather than broad host permissions. The local relay supports pairing, session expiry, domain validation, allowlisted action queues, explicit takeover approval, polling, and revocation through `/api/v1/browser-relay/*`. It does not store passwords, cookies, or cloud browser sessions.

The extension is intentionally a local control channel, not a hosted browser service. Users must load it as an unpacked extension in Chrome or Edge, pair it from the Signal Room, approve the selected browser tab, and keep Orville running while actions are being exchanged. Cloud Browser remains outside the product scope.


## Four-layer connector architecture

The local connector system is organized into four explicit layers:

1. **Catalog and manifest registry.** Every catalog entry receives a versioned manifest record with connector identity, capabilities, scopes, limits, risk-classified operations, documentation metadata, and a transparent support state. Catalogued entries remain `configuration_required` until a provider endpoint and credentials are configured; only tested handlers are marked `operational`.
2. **Authentication service.** Manual API-key and bearer credentials are protected with Windows DPAPI. OAuth2 uses authorization-code PKCE, local callbacks, protected access and refresh tokens, optional provider revocation endpoints, expiry state, refresh, reauthorization, and local disconnect. Secrets and authorization headers are never returned in public records or audit metadata.
3. **Operation adapter service.** Priority manifests expose reviewed operation schemas. User-owned providers can expose operations through the bounded `/openapi.json` discovery route, which enforces host policy, size limits, operation caps, safe paths, normalized risk classes, pagination metadata, and explicit user configuration. Generic HTTP invocation applies timeouts, response-size limits, network egress rules, and result redaction.
4. **Approval and audit gateway.** Sensitive and critical operations require explicit approval. Request payloads are validated against operation schemas, connector calls are rate-limited and metered, results are redacted, provider health is tracked, and every sign-in, refresh, revoke, discovery, approval, invocation, failure, and policy block is audited.

### Provider configuration status

The full 372-entry catalog is available for search and configuration. A catalog entry is not an assertion that Orville contains that provider's proprietary API implementation. For services without a native handler, use the Connectors menu to configure the official endpoint and credential, then review discovered operations before enabling them for agent tasks. Provider-specific OAuth client IDs, scopes, redirect URIs, refresh behavior, and service terms remain user-owned configuration.

### OpenAPI discovery

After connecting a service, Orville can request a reviewed JSON OpenAPI document from the configured base URL through `POST /api/v1/connectors/{uid}/openapi/discover`. The discovery endpoint ignores YAML by default, limits document size and operation count, rejects unsafe paths and duplicate operation IDs, classifies `GET` as read, `POST`/`PUT`/`PATCH` as write, `DELETE` as critical, and honors `x-orville-sensitive` for provider-declared sensitive operations. Discovered operations must still pass approval and network policy before execution.

OAuth connections may optionally provide a provider revocation endpoint. When configured, the Revoke action calls the provider first and retains the local record if remote revocation fails; local Disconnect removes only the local protected record.

## Durable triggers and provider adapters

The local bridge exposes authenticated durable trigger controls. Clients can list schedules with `GET /api/v1/schedules`, claim and release worker leases, recover stale leases, and dispatch enabled workflows through `POST /api/v1/schedules/{schedule_id}/dispatch`. Signed inbound deliveries can be inspected through `GET /api/v1/events/inbound/recent` and can dispatch an enabled workflow through `POST /api/v1/events/inbound/dispatch`. Event acceptance requires a bounded non-empty event identifier. When `ORVILLE_WEBHOOK_SIGNING_SECRET` is configured, `X-Orville-Signature` must contain either an HMAC-SHA256 digest or a timestamped `t=<unix>,v1=<digest>` value inside the configured replay window. Duplicate event IDs are rejected durably in SQLite.

Priority connector adapters can be invoked through `POST /api/v1/connector-adapters/{connector_id}/invoke`. The route requires an existing local connection, rejects sensitive and critical operations without explicit approval, applies provider-specific non-secret protocol headers, enforces the registered host policy, redacts returned values, records attempts in the audit store, and increments the connection operation counter. File-transfer operations use `FileTransferPolicy`: uploads remain inside Orville's approved `connector-files` directory and respect configured size and MIME limits; downloads are written to a contained `.part` file before atomic replacement. Credentials remain DPAPI-protected and are never returned to clients.

The completed roadmap slice was validated with 204 backend tests, Python compilation, a successful production frontend build, a rebuilt portable Windows release, and executable startup checks returning docs `200`, OpenAPI `200`, unauthenticated health `401`, and authenticated health `200`. Provider credentials and external provider availability remain environment-dependent and require credentialed fixture or live integration tests before any provider is classified as universally operational.
