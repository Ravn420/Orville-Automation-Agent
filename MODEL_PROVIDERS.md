# Orville Model Provider Layer

## Scope

The Phase 2 provider layer gives Orville one internal interface for cloud models, local model servers, and imported local assets. It is implemented with the Python standard library and does not require a vendor SDK. The application supplies credentials and endpoint URLs at runtime; provider secrets are not serialized by the adapter contracts or exposed through redacted configuration metadata.

## Supported provider types

| Provider type | Adapter | Configuration |
|---|---|---|
| `gemini` | `GeminiAdapter` | Google Gemini REST endpoint, model name, user-supplied API key |
| `ollama` | `OllamaAdapter` | Ollama `/api/chat` and `/api/tags`, model name, endpoint URL |
| `custom-local` | `CustomLocalAdapter` | User-supplied Ollama-compatible local endpoint and model name |
| `stable-horde` | `StableHordeAdapter` | AI Horde asynchronous text endpoint, active code model name, API key |

## Stable Horde code-generation contract

Stable Horde is a remote asynchronous text-generation provider for code tasks. Configure it with an active AI Horde text model, `https://aihorde.net/api` as the base URL, and the `text`, `code`, and `streaming` capabilities. `StableHordeAdapter.generate()` submits `POST /v2/generate/text/async`, polls `GET /v2/generate/text/status/{id}`, and returns a normalized `LLMResponse`. Existing code-generation objectives use the normal provider router and require `code` plus `streaming`, so Stable Horde can be selected with `provider_id` or used as a fallback. See `STABLE_HORDE.md` for environment variables, request examples, model discovery, and timeout behavior.

## Common contract

`ProviderConfig` records provider ID, provider type, model name, base URL, timeout, capabilities, and an optional API key. The `redacted()` method exposes only whether a key is configured. `LLMRequest` supports messages, temperature, maximum output tokens, JSON response schemas, and tools. `LLMResponse` normalizes provider ID, model, text, raw response, finish reason, tool calls, and token usage.

The adapters do not authorize or execute tool calls. They only return normalized tool-call proposals. Orville’s orchestration and security layers must validate the tool name, arguments, permissions, network and filesystem boundaries, approval policy, and side effects before execution.

## Gemini configuration example

```python
from orville_core import GeminiAdapter, LLMRequest, ProviderConfig

config = ProviderConfig(
    provider_id="gemini-primary",
    provider_type="gemini",
    model="gemini-model-name",
    base_url="https://generativelanguage.googleapis.com",
    api_key="value-supplied-by-the-user",
)
provider = GeminiAdapter(config)
response = provider.generate(LLMRequest([
    {"role": "system", "content": "Return concise answers."},
    {"role": "user", "content": "Describe the project architecture."},
]))
print(response.text)
```

The API key must be provided by the user or an approved secret manager. It must not be committed to source control, written to checkpoints, printed in logs, or displayed in the GUI.

## Ollama configuration example

```python
from orville_core import LLMRequest, OllamaAdapter, ProviderConfig

config = ProviderConfig(
    provider_id="ollama-local",
    provider_type="ollama",
    model="my-imported-model",
    base_url="http://localhost:11434",
)
provider = OllamaAdapter(config)
health = provider.health_check()
response = provider.generate(LLMRequest([
    {"role": "user", "content": "Generate a Python function with tests."},
]))
```

The endpoint may be changed to a user-supplied local or remote Ollama-compatible URL. Endpoint validation, network policy, and authentication requirements belong in the configuration and security layer.

## Imported local model example

```python
from pathlib import Path
from orville_core import LocalModelCatalog, OllamaAdapter, create_provider

catalog = LocalModelCatalog(Path(".orville/models.json"))
record = catalog.import_model(
    Path("/models/my-model.gguf"),
    model_id="my-model",
    runtime="ollama",
    endpoint="http://localhost:11434",
    capabilities=["text", "code", "structured_output", "tool_calling"],
)
provider = create_provider(catalog.provider_config(record.model_id))
print(provider.health_check())
```

The catalog performs metadata-first inspection and SHA-256 hashing. It does not execute model files or arbitrary scripts. A production activation workflow must add runtime-specific validation, resource checks, provenance and license review, and sandboxing before enabling an imported asset.

## Testing

Run all tests from the repository root:

```bash
python -m unittest discover -s tests -v
```

The adapter tests use an injected fake HTTP client, so tests do not contact Gemini, Ollama, Stable Horde, or any external endpoint. They cover normalized responses, structured-output and tool payloads, Gemini system instructions, Stable Horde submission and polling, health checks, factory routing, local model hashing, catalog persistence, and missing-file errors.

## Current limitations

The Phase 2 slice does not yet implement streaming responses, multimodal payloads, embeddings, native model discovery for every provider, JSON Schema validation beyond provider request construction, encrypted secret storage, endpoint SSRF policy enforcement, sandboxed runtime activation, automatic model downloads, or GUI configuration. These remain tracked in `TODO.md`. Stable Horde text generation is asynchronous; its compatibility `stream()` method emits one completed chunk rather than token-level streaming.
