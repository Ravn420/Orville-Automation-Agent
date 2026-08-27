# Provider Operations and Enterprise Policy Storage

## Discovery catalogs and active models

Provider discovery results are stored atomically in `orville-provider-catalogs.json` beside the configured runtime data. Each provider entry contains the discovered model metadata, discovery status, timestamp, and active model identifier. `GET /api/v1/providers/{provider_id}/catalog` reads the persisted catalog.

When discovery finds models and the configured model is not present, Orville automatically activates the first discovered model and rebuilds the provider adapter. Users can explicitly select a discovered model through `POST /api/v1/providers/{provider_id}/models/select` with `{ "model": "model-id" }`. Selection is accepted only for a model present in the persisted catalog.

## Rate limits and usage metrics

Provider call and token windows are stored in the configured SQLite database. Limits are configured through `POST /api/v1/provider-rate-limits` and inspected through `GET /api/v1/provider-rate-limits/{provider_id}`. Generation routing admits calls against the provider window before execution and records provider-scoped usage, token counts, latency, and success/failure status.

Provider metrics are available through `GET /api/v1/provider-usage/{provider_id}`. Existing budget and provider-health routes remain compatible and continue to expose aggregate usage and circuit state.

## Enterprise remote policy storage

Set the following runtime variables for an enterprise policy service:

```text
ORVILLE_POLICY_STORE_URL=https://policy.example.com
ORVILLE_POLICY_STORE_TOKEN=<secret supplied through the deployment secret manager>
```

The adapter reads from `GET /v1/policies/privacy` during API startup and writes individual policies to `PUT /v1/policies/privacy/{privacy_class}`. The token is never returned in status, exports, logs, or error details. If the remote service is not configured or unavailable, Orville continues using the atomic local JSON policy store and reports `remote_synced: false`; this fallback is explicit and observable through `GET /api/v1/policy-store/status`.

The remote service must provide tenant authentication, authorization, TLS, concurrency-safe writes, audit retention, backup, and disaster recovery. The local fallback is appropriate for standalone operation but is not a substitute for a highly available enterprise control plane.

## Validation

```powershell
python -m py_compile orville_core\provider_features.py orville_core\routing.py orville_core\api.py
python -m pytest -q
```

No live enterprise endpoint or production credential is required for local validation. Tests use synthetic credentials and mocked transport only.

## Tenant catalog federation

Set `ORVILLE_CATALOG_STORE_URL`, `ORVILLE_CATALOG_STORE_TOKEN`, and `ORVILLE_TENANT_ID` to enable tenant-scoped catalog synchronization. Orville reads from `GET /v1/tenants/{tenant_id}/catalogs/providers` at startup and publishes provider updates to `PUT /v1/tenants/{tenant_id}/catalogs/providers/{provider_id}`. Missing or unavailable remote configuration leaves the local catalog authoritative and reports `remote_synced: false`.

The local API exposes `GET /api/v1/catalog-store/status` and `POST /api/v1/catalog-store/sync`. Tenant identifiers are included in audit metadata but credentials are never included in responses or logs.

## Audit and disaster recovery

Policy changes, catalog discovery, model selection, catalog synchronization, and backup creation append sanitized events to the existing audit store. Backup snapshots are written atomically under `policy-backups/` and contain policies and catalogs only. Each backup filename includes a truncated SHA-256 identifier, while the API returns the complete checksum for external retention verification.

Use `POST /api/v1/policy-store/backup` to create a snapshot and `GET /api/v1/policy-store/backups` to enumerate retained snapshots. Enterprise operations should copy snapshots to encrypted, access-controlled off-host storage and periodically test restoration. The local backup is not itself a complete enterprise disaster-recovery system.

## Concurrency load testing

Run the local synthetic load test with:

```powershell
python tools\load_test_provider_controls.py --workers 16 --operations 200
```

The test verifies that SQLite `IMMEDIATE` transactions admit no more calls than the configured provider limit and that concurrent catalog updates complete with a valid final active model. It uses synthetic state and does not contact external services.
