# Local Model Storage, Runtime Validation, and Streaming

## Summary

Orville can import a local model file or directory without executing model-provided code. The operator may retain a reference to the original asset, copy it into a selected storage root, or create a filesystem link. Duplicate content can be registered as a second catalog entry without copying the model bytes when `deduplicate` is enabled.

## Import API

Use `POST /api/v1/models/local/import` with an approval payload. The `source` may be a file or directory. `storage_mode` accepts `reference`, `copy`, or `link`; `storage_root` is optional for references and required for copy/link behavior. The API defaults `deduplicate` to `true` so an identical checksum reuses the existing registered path rather than creating another large file. Imports are metadata-only and return `executed: false`.

The desktop control center exposes this through **Import model**. It asks for the source and an optional storage location. Choosing a location creates a copy; cancelling the storage dialog keeps a reference to the selected source.

## Metadata preservation

Every catalog record preserves the SHA-256 checksum, declared license, license restrictions, provenance, and ownership metadata. Provenance includes the original source path and may include repository, revision, URL, or other caller-supplied origin fields. Ownership is caller-supplied metadata such as an owner ID and owner type; Hub downloads record the local operator as the importing owner. Older catalogs are migrated in memory with empty provenance, ownership, and restriction values.

License restrictions are retained without being silently interpreted as permission. Activation requires explicit `accept_license_restrictions: true` when restrictions are present. This creates a visible review gate while keeping the license information attached to the model record.

## Runtime and modality validation

Imported models are connected through the catalog's provider configuration. Ollama uses its local endpoint, while `llama.cpp` and other configured local inference servers use the OpenAI-compatible adapter. Transformers is available for direct local execution when the required Python packages are installed.

`GET /api/v1/models/local/{model_id}/validate` returns structured diagnostics and preserved metadata. `POST /api/v1/models/compatibility` returns the existing conservative file/resource compatibility result and, when probing is enabled, a runtime capability report.
 The probe performs a health/catalog request only; it does not run generation, embeddings, or model code. The supported runtime families are Ollama, `llama.cpp`, Transformers, and OpenAI-compatible local servers.

Activation preserves text and code compatibility behavior. A model declaring vision, embeddings, audio, image generation, or video generation must first pass a reachable-runtime capability probe. Only modalities declared by both the model and the runtime are exposed to routing. Unsupported capabilities remain unavailable rather than being advertised optimistically.

## Streaming controls

`StreamPolicy` remains the single policy surface for `max_buffer_chars`, cooperative cancellation, `checkpoint_every_chunks`, and `preserve_partial_output`. Partial output is emitted periodically and is also checkpointed when cancellation or reconnect occurs. `reconnect_attempts` now controls bounded provider reconnects. When a provider replays the prefix after reconnect, Orville skips the already checkpointed prefix to avoid duplicate output.

The run event SSE endpoint supports both the `last_event_id` query parameter and the standard `Last-Event-ID` header. A client can reconnect with its last received event sequence and receive only later durable events. The endpoint disables proxy buffering and advertises the resume mechanism in `X-Orville-Resume`.

## Validation commands

From the repository root, run:

```powershell
python -m pytest tests/test_model_runtime_controls.py tests/test_streaming_controls.py tests/test_media_api.py -q
python -m pytest -q
python -m compileall -q orville_core windows_gui.py
```

Diagnostics use stable codes, including `unsupported_format`, `missing_runtime`, `missing_runtime_endpoint`, `corrupted_or_changed`, `insufficient_disk`, `insufficient_ram`, `insufficient_vram`, `incompatible_hardware`, and `license_restriction`. Each diagnostic includes a human-readable message and severity. The runtime probe is deliberately conservative. A configured endpoint is not sufficient for multimodal or embedding exposure; the endpoint must answer the capability/catalog probe and the requested modality must be supported by the local runtime contract.
