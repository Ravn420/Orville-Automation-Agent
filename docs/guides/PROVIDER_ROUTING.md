# Provider Routing and Capability Selection

Phase 4 adds a routing layer above the provider adapters. It selects a configured provider only when its declared capabilities satisfy the request, applies local-only privacy policy, honors provider preference order, and optionally falls back after a provider failure.

## Endpoint validation

`validate_endpoint()` accepts `http` and `https` URLs, rejects missing hosts, embedded credentials, URL fragments, and invalid ports, and requires HTTPS for non-local endpoints. Local services such as Ollama may use HTTP on localhost or another explicitly designated local endpoint. The validator does not make a network request; health checks remain a separate operation.

```python
from orville_core import validate_endpoint

validate_endpoint("https://api.example.com/v1")
validate_endpoint("http://localhost:11434", local=True)
```

## Capability-aware generation

```python
from orville_core import ProviderRegistry, ProviderRouter, RoutingRequest

routing = RoutingRequest(
    required_capabilities=frozenset({"vision", "streaming"}),
    preferred_provider_ids=("local-vision", "cloud-vision"),
    local_only=False,
    allow_fallback=True,
)
response, result = ProviderRouter(registry).generate(request, routing)
```

Supported capability names are `text`, `code`, `vision`, `image_generation`, `audio`, `embeddings`, `streaming`, `structured_output`, and `tool_calling`. The router rejects unknown names and does not select providers with missing capability declarations.

## Privacy routing

Set `local_only=True` when prompts or attachments must not leave local infrastructure. The default implementation excludes Gemini from local-only candidates and selects local endpoint providers. A production policy layer should classify every provider as local, trusted cloud, or restricted rather than relying only on provider type strings.

## Fallback behavior

For complete responses, media requests, and embeddings, routing tries eligible providers in preference order and records each attempt. A failed provider is followed by the next eligible provider when `allow_fallback=True`; capability, privacy, local-only, health, and circuit state filters are applied before selection. Streaming fallback is allowed only before the first chunk. Once partial output has been emitted, the router raises an error instead of silently switching providers and producing a mixed response.

## Retries and circuit breaking

`ProviderRouter` retries transient `ProviderError`, timeout, connection, and operating-system failures using bounded exponential backoff. The defaults permit two retries with delays of 0.5 and 1.0 seconds, capped by `backoff_max_seconds`; tests inject `sleep_fn` so no real delay is required. Non-transient failures, including invalid-request errors, are not retried.

The circuit breaker counts provider-level failures. It opens after `failure_threshold` failures, excludes the provider during `cooldown_seconds`, and reports `half_open` after cooldown so the next eligible call acts as a recovery probe. A successful call closes and clears the circuit. Fallback remains constrained by `RoutingRequest.allow_fallback`; setting it to `False` prevents a second provider from being used.

## Cross-process persistence

For a single process, `ProviderRouter` keeps circuit state in memory. For multiple workers or restarts, pass `SQLiteCircuitStateStore` to `circuit_store`. The store uses short-lived SQLite connections, WAL mode, `BEGIN IMMEDIATE` atomic increments, and a 30-second busy timeout so independent router instances share failure counters and cooldown timestamps safely.

```python
from orville_core import ProviderRouter, SQLiteCircuitStateStore

router = ProviderRouter(
    registry,
    circuit_store=SQLiteCircuitStateStore("./data/provider-circuits.sqlite3"),
)
```

Use a shared filesystem path for all workers. Redis remains an optional future adapter for deployments where a shared networked state service is required; the SQLite implementation is the standalone default and does not require additional dependencies.

```python
router = ProviderRouter(
    registry,
    circuit_store=SQLiteCircuitStateStore("./data/provider-circuits.sqlite3"),
    retry_attempts=2,
    backoff_base_seconds=0.5,
    backoff_max_seconds=8.0,
    failure_threshold=3,
    cooldown_seconds=30.0,
)
```

## Current limitations

Provider capability declarations remain configuration metadata unless a health check supplies discovered capabilities. Endpoint validation is exposed as an explicit policy function and is not automatically applied by every configuration constructor. Streaming retries after partial output remain intentionally disabled to prevent mixed or duplicated responses. Provider-specific server-directed retry delays and a Redis-backed circuit-state adapter remain future infrastructure work.
