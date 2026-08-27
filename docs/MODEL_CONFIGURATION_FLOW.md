# Secret-Safe Model Configuration Flow

## Scope

The model configuration flow accepts a provider type, model name, endpoint URL, optional user-supplied credential, timeout, privacy class, and declared capabilities. It presents configuration metadata for review without exposing the credential value and delegates persistence, secret storage, endpoint validation, and health checks to an approved local service.

## Workflow

1. **Select provider type.** Offer documented presets for `ollama`, `gemini`, `openai_compatible`, and `anthropic`. Presets are editable defaults, not credentials or authorization.
2. **Enter endpoint and model.** Require a syntactically valid `http` or `https` URL and a non-empty model name. Local endpoints are preferred for local-only privacy classes.
3. **Enter credential if required.** Use a masked password control with autocomplete disabled for credential reuse. Never echo the value into labels, previews, errors, screenshots, logs, checkpoints, artifacts, or browser storage.
4. **Declare constraints.** Capture timeout, privacy class, capabilities, and any user-approved routing or rate-limit constraints. Do not infer permission to send prompts or generated content from configuration alone.
5. **Review redacted configuration.** Show provider, model, endpoint, timeout, privacy class, and a boolean credential-present state. Do not show the credential, a reversible mask, or an authorization header.
6. **Save through the approved local boundary.** Send only the structured configuration to the authenticated local API or configured standalone adapter. The UI must clear the credential field after submission and render only a safe result.
7. **Run health explicitly.** A health check is a separate, user-visible action. Its result is structured and redacted; it does not silently send a prompt or generated content.

## Secret and endpoint boundaries

Credentials are accepted only in protected input controls and approved secret stores or environment references. The GUI never persists credential values in project files, `STATE.md`, `TASK_GRAPH.md`, logs, artifacts, analytics, query strings, or local draft storage. Error messages identify the operation and safe remediation without including request headers, provider response bodies, or secret-bearing URLs.

Endpoint URLs are visible configuration metadata but are still validated for scheme, path, and allowed network policy by the local service. A URL supplied by a user does not authorize network access by itself. External cloud routing, publication, deployment, or account changes require a separate explicit approval gate.

## Configuration states

| State | UI behavior | Next permitted action |
| --- | --- | --- |
| `draft` | Show editable fields and local validation. | Review redacted configuration. |
| `ready_for_review` | Show normalized metadata and credential-present boolean. | Save or cancel. |
| `saved` | Show safe provider/model/endpoint metadata and configuration ID. | Run explicit health check or edit. |
| `health_check_pending` | Show progress without secret or prompt content. | Wait or cancel if supported. |
| `healthy` | Show structured redacted health result and timestamp. | Use provider subject to routing policy. |
| `blocked` | Show policy or validation reason and bounded remediation. | Correct fields or request approval. |
| `failed` | Show safe operation ID and error class. | Retry or inspect local diagnostics. |

## Validation and acceptance criteria

Acceptance requires that all four supported presets load non-secret defaults, endpoint and model validation rejects invalid or empty values, credential controls remain masked, the redacted review contains no credential value, the field is cleared after save, health checks are explicit, and no external request is made by the standalone preview. Tests use synthetic values only. Production credentials must never be used in a smoke test.
