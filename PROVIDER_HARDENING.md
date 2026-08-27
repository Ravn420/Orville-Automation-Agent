# Provider Hardening and Local Model Lifecycle

## Provider health and capability discovery

`ProviderRouter.discover_capabilities()` calls a configured provider health check and uses returned capability metadata when available, falling back to declared configuration capabilities. Routing can exclude providers whose declared capabilities do not satisfy the requested operation.

## Circuit breaking

The router records consecutive provider failures. After the configured failure threshold, the provider is temporarily excluded for the cooldown period. A successful request clears the failure counter. This is an in-process circuit breaker; persistent distributed circuit state remains future work.

## Local model lifecycle

`LocalModelCatalog` now supports validation, activation, deactivation, catalog removal, and guarded deletion behavior. Validation checks path existence, readability, recognized format, runtime and endpoint configuration, and basic disk availability. File deletion is deliberately blocked behind an explicit external confirmation flow rather than being performed by the catalog API.

## Limitations

Capability discovery is provider health metadata, not a full dynamic schema negotiation protocol. Rate-limit accounting, persistent circuit state, provider latency ranking, encrypted secret storage, endpoint SSRF enforcement at the HTTP client boundary, and process-isolated model activation remain required for production hardening.

## Verification

```bash
python -m compileall -q orville_core tests examples
python -m unittest discover -s tests -v
```

The current suite passes 44 tests.
