# Provider Discovery, Privacy Routing, and Redacted Export

**Status:** completed-local  
**Owner:** IDE Agent with Verification Agent review  
**Validation:** 261 tests passed; one pre-existing HTTP-client deprecation warning

## Provider model discovery

The authenticated endpoint `GET /api/v1/providers/{provider_id}/models` discovers model identifiers for supported provider families without returning credentials. Ollama uses `/api/tags`, OpenAI-compatible providers use `/models`, and Gemini uses `/v1beta/models` with the API key supplied through a request header rather than a URL query string. Providers without a safe discovery contract, such as Anthropic in the current implementation, return `manual_required` and retain manual model entry.

Discovery responses include provider identity, provider type, support status, model identifiers, and provider-safe metadata. Provider errors are normalized to bounded, credential-free HTTP error details.

## Persistent privacy-aware routing

Privacy policies are stored atomically in `orville-routing-policy.json` beside the configured Orville runtime data. The supported classes are `local_only`, `cloud_approved`, and `restricted`. `local_only` and `restricted` always force local-provider routing. A policy can additionally restrict routing to an explicit provider allowlist and control fallback behavior.

The API exposes:

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/routing/privacy` | List persisted privacy policies. |
| `POST /api/v1/routing/privacy` | Create or replace one privacy policy. |
| `POST /api/v1/objectives` with `privacy_class` | Propagate the selected class into task execution. |

Policy files contain provider IDs and routing flags only. They do not contain prompts, responses, API keys, headers, or tokens.

## Redacted configuration export

`GET /api/v1/config/export/redacted` returns a portable JSON template containing provider metadata, capability flags, endpoint URLs, timeout values, and privacy policies. Provider secrets are represented only by the existing `api_key_configured` boolean and are never included in the export. The desktop Provider setup window can save this response to a user-selected JSON file.

The export is intentionally not an import format for credentials. Reconnecting a provider requires the user to supply credentials through an approved secure configuration flow.

## Limitations

Provider discovery does not yet persist discovered model catalogs or automatically change the active model. Privacy policy persistence is local to the configured Orville runtime and does not replace remote relay admission or explicit user approval for external side effects. Endpoint reachability and provider authentication remain dependent on the configured provider.
