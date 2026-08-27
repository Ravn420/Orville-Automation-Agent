# Clean-environment product validation

## Scope

This checkpoint validates the standalone Orville product contract without external credentials or live provider calls. The scenarios use a temporary test data directory, synthetic credentials held only in the test process, and provider adapters or local HTTP-compatible fixtures already covered by the repository tests.

## Scenario matrix

| Scenario | Configuration | Evidence | Result |
|---|---|---|---|
| Configured cloud shape | Synthetic authenticated API smoke workflow and provider-neutral cloud configuration; no live cloud request | `tests/test_smoke_workflow.py`, `tests/test_providers.py`, `tests/test_provider_features.py` | Passed |
| Configured local endpoint | Local/Ollama-compatible provider configuration and routing/provider behavior tests; external endpoint variables cleared | `tests/test_providers.py`, `tests/test_provider_features.py`, `tests/test_routing.py` | Passed |
| No-provider fallback | Cloud, hosted-model, relay, and Ollama environment variables cleared; authenticated API and safe-default behavior exercised | `tests/test_smoke_workflow.py`, `tests/test_safe_defaults.py`, `tests/test_deployment_targets.py` | Passed |

The clean run also covered standalone examples, deployment target configuration, and backup/release safety checks through `tests/test_standalone_examples.py` and `tests/test_standalone_release.py`.

## Reproduction

From the repository root, clear optional provider variables in the process environment, set only a synthetic `ORVILLE_API_TOKEN`, and run:

```powershell
python -m pytest -q tests\test_smoke_workflow.py tests\test_providers.py tests\test_provider_features.py tests\test_routing.py tests\test_safe_defaults.py tests\test_deployment_targets.py tests\test_standalone_examples.py tests\test_standalone_release.py
```

The validated result on 2026-08-27 was **55 passed, 1 warning**. The warning concerns the installed Starlette/httpx test-client compatibility notice and does not represent a product-test failure.

## Boundaries

This is a credential-free clean-environment validation, not a claim of live cloud availability or production deployment readiness. It does not contact cloud providers, mutate external accounts, deploy, or exercise a user-managed Ollama process. Live provider credentials, production networking, packaged installer execution, and multi-replica deployment remain environment-owned follow-up checks.
