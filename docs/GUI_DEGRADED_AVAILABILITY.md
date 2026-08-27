# GUI Degraded Availability Contract

## Scope

The Orville GUI remains usable when a cloud provider, local endpoint, connector, or model runtime is unavailable. Unavailability changes which actions are offered; it does not make the workspace unusable, expose raw provider errors, or silently broaden privacy routing.

## Stable dependency states

| State | User-facing explanation | Safe recovery actions |
|---|---|---|
| `cloud_unavailable` | The selected cloud provider cannot be reached or is not configured. | Continue with a local provider, save the draft, or retry. |
| `local_endpoint_unavailable` | The configured local model service could not be reached. | Start or check the local service, choose another local model, or retry. |
| `connector_unavailable` | The connector is disabled, disconnected, or temporarily unavailable. | Review connector status, continue without it, or retry. |
| `runtime_unavailable` | The selected model runtime is missing or cannot activate this model. | Choose a compatible model, save the task for later, or review diagnostics. |

The GUI uses stable state names and safe summaries. It does not display credentials, bearer tokens, cookies, raw exceptions, full provider responses, or secret-bearing endpoint URLs.

## Usable degraded behavior

The objective draft, task plan, local settings, saved artifacts, diagnostics, and review surfaces remain available in every dependency state. Read-only information is shown when possible. Actions that require the unavailable dependency are disabled with an explanation, while local or offline-safe alternatives remain available.

Cloud failure never silently routes data to another cloud provider. A fallback to a local provider requires a compatible configured local model and preserves the current privacy class. Connector failure does not discard the task; the user can continue without the connector when the workflow permits, or save a resumable draft. Runtime failure does not delete an imported model or artifact.

Each degraded message contains a stable title, plain-language explanation, operation-safe recovery action, and optional diagnostic reference. Retry is bounded and does not duplicate a mutating operation unless the operation has an idempotency key. A refresh or retry preserves user input and current navigation state.

## Acceptance criteria

The GUI is accepted when each dependency state has a visible explanation and at least one safe recovery path; objective text and local artifacts remain accessible; unavailable actions are clearly disabled or gated; privacy routing is not broadened; retry behavior is bounded and idempotent; diagnostics are redacted; and the user can save, review, or leave the workspace without losing work.

Focused validation is:

    python -m unittest tests.test_gui_degraded_availability
    python -m compileall -q windows_gui.py tests/test_gui_degraded_availability.py

The contract does not claim live provider availability, external connector recovery, model-runtime installation, or full screen-reader and visual regression evidence.

## References

- Provider routing: PROVIDER_ROUTING.md
- Connector operations: CONNECTOR_OPERATIONS.md
- Accessibility acceptance: docs/ACCESSIBILITY_ACCEPTANCE_CRITERIA.md
- Workflow state handling: docs/WORKFLOW_STATE_HANDLING.md
