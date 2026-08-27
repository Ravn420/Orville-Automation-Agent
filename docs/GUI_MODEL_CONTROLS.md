# GUI model and provider controls

The GUI uses the authenticated API bridge to discover, import, activate, health-check, and route models without exposing provider credentials. The controls are capability-aware and preserve local-only and privacy-routing policies.

## Control surface

| GUI control | API surface | Behavior |
|---|---|---|
| Model catalog | `GET /api/v1/models/catalog`, `GET /api/v1/models/local`, and provider/model discovery routes | Shows supported models, capabilities, runtime compatibility, provenance, and availability using public metadata only. |
| Local-model import | `POST /api/v1/models/local/import` | Registers a local model from a contained source path or approved reference with bounded metadata, provenance, license, and storage options. |
| Local-model activation | `POST /api/v1/models/local/{model_id}/activate` | Activates a compatible runtime and endpoint only after validation, license acceptance where required, and explicit approval for sensitive actions. |
| Provider health | `GET /api/v1/providers/health` and adapter-health routes | Displays provider and adapter status, capability health, and safe error classes without returning credentials. |
| Routing controls | Privacy-routing policy and provider route APIs | Selects providers by capability, privacy class, local-only flag, preference, fallback policy, and rate-limit state. |

All controls require the GUI backend bridge authentication contract. Payloads are bounded by typed request models and invalid values are rejected without echoing submitted secrets.

## GUI behavior

The catalog should distinguish available, local, compatible, unavailable, degraded, and blocked states. A provider health failure must not silently fall back across a privacy boundary. Local-only requests must remain local, and a fallback must satisfy the same required capabilities and privacy class.

Import and activation are separate operations. Import records metadata and provenance; activation changes runtime state and therefore requires compatibility checks, license restrictions, endpoint validation, and applicable approval. The GUI must display a review summary before activation and must never render API keys, client secrets, authorization headers, or protected connector values.

## Routing display

For each route decision, display only the provider identifier, model identifier, capability match, privacy class, local-only status, fallback status, and safe attempt outcome. Do not expose raw provider responses or secret-bearing headers. If no provider satisfies the request, show a bounded actionable error and preserve the user’s objective for retry or reconfiguration.

## Verification

Run the focused contract checks with:

```powershell
python -m unittest tests.test_gui_model_controls -v
python -m py_compile tests\test_gui_model_controls.py
```

Local checks may use synthetic model metadata and loopback endpoints only. They must not load real credentials, contact a provider, activate a production runtime, or mutate an external account.

## Environment boundaries

Hosted provider discovery, live health probes, model downloads, runtime processes, TLS, identity, secret storage, license verification, and deployment rollback remain environment-owned. The GUI control contract provides presentation and request boundaries; it does not authorize sensitive operations or convert external model metadata into trusted instructions.
