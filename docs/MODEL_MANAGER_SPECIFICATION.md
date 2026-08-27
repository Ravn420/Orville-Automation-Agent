# Orville Model Manager

## Purpose

The Orville model manager is the single desktop entry point for managing four model sources: **cloud providers**, **endpoint-based models**, **Ollama servers**, and **imported local model files**. It combines provider setup and local-model inventory actions while preserving the existing API bridge and approval gates.

## Model-source workflows

| Source | Management action | Existing boundary |
|---|---|---|
| Cloud providers | Enter provider type, model, endpoint, optional user-supplied API key, timeout, capabilities, and privacy class; save, refresh, test health, discover models, and export redacted configuration. | Credentials are masked in the UI and sent only to the configured local API; no credential value is written to the interface output. |
| Endpoint-based models | Configure an OpenAI-compatible or other approved endpoint with model name, capabilities, timeout, and privacy policy. | Endpoint validation and provider policy remain server-side. |
| Ollama servers | Use the local Ollama preset with a loopback endpoint, model name, local-only policy, health check, and model discovery. | No cloud transmission is implied by the local preset. |
| Imported local model files | Select a file or directory, choose reference or copy storage, import metadata, list inventory, validate runtime compatibility, activate/deactivate, and remove only the registration. | Model files are not deleted by registration removal; activation remains approval-gated. |

## Inventory and lifecycle controls

The model manager inventory table shows model ID, status, runtime, capabilities, license, storage mode, and attestation status. Selecting a row loads safe details. Lifecycle actions are:

1. **Refresh** the local inventory.
2. **Validate** runtime, license, and attestation compatibility.
3. **Activate** a model with explicit runtime, endpoint, policy, and approval values.
4. **Deactivate** a model while retaining its files.
5. **Remove registration** while retaining model files.
6. Open **Provider setup** for cloud, endpoint, or Ollama configuration.
7. **Import local model** for a file or directory workflow.

The manager uses the existing `/api/v1/providers`, `/api/v1/providers/health`, `/api/v1/providers/{provider_id}/models`, `/api/v1/models/local`, `/api/v1/models/local/import`, and local lifecycle routes. It introduces no external credentials, new storage format, or remote operation.

## Safety and usability rules

API keys use a masked entry control and are cleared from the form after submission. Provider responses are shown as structured safe results; raw credentials and unredacted exceptions are not rendered. User approval is required for provider setup, model import, activation, and registration removal. Registration removal explicitly preserves model files. The manager remains usable at the existing 760 px minimum window width through a scrollable inventory and bounded controls.

## Validation boundary

Focused tests verify that the GUI exposes all four model-source paths, uses the required existing routes, documents lifecycle actions, clears the API-key field, and states that files are retained on registration removal. Runtime provider health, endpoint reachability, model compatibility, license review, and attestation verification remain API-owned checks and require local test fixtures or explicit operator approval.
