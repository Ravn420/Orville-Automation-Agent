# Per-run observability contract

`orville_core.run_observability` provides a bounded, append-only record for one model or agent run. The record explicitly represents provider, model, model version, prompt capture mode, prompt digest, tool calls, agent handoffs, retries, approvals, artifacts, latency, token usage, finish reason, cache status, cost metadata, and failures.

## Privacy policy

Raw prompts are never persisted. Callers may provide a prompt transiently to `RunObservabilityRecord.start`; the record stores only a SHA-256 digest and declares `prompt_capture: hash-only`. Secrets, credentials, authorization material, and sensitive message text are redacted before nested event data is stored. The recorder writes JSONL and supports read-back of the already-redacted records. Temporary paths and private host details are not part of the record contract.

## Field semantics

| Field | Meaning |
|---|---|
| `provider`, `model`, `model_version` | Selected provider and model identity; `null` means unavailable and must not be guessed. |
| `tool_calls` | Bounded tool name, outcome, approval state, latency, and error class; arguments are intentionally absent. |
| `agent_handoffs` | Source/target agent IDs, reason, and outcome without transcript capture. |
| `retries` | Positive attempt number, bounded reason, and optional backoff duration. |
| `approvals` | Approval ID, action, scope, outcome, and optional reviewer identity. |
| `artifacts` | Artifact ID, media type, checksum, and size; bytes are not embedded. |
| `token_usage` | Non-negative input, output, cached-input, and derived total counts. |
| `finish_reason`, `failure` | Bounded completion or failure classification; exception text is redacted. |
| `cache` | Hit/miss plus an optional key digest and source, never a raw cache key. |
| `cost_metadata` | Provider-reported units such as currency and amount after redaction; values are not inferred. |

The record is additive and does not replace the existing trace recorder, checkpoint events, telemetry aggregates, or OpenTelemetry-compatible roadmap work. It provides a stable privacy-safe projection that can be attached to those systems without exposing prompt contents or tool arguments.

## Validation

Run focused tests with:

```bash
python3 -m pytest -q tests/test_run_observability.py
```

Run the full regression suite after focused validation. A passing local suite demonstrates schema and privacy behavior only; provider-side billing, token accounting, distributed trace export, and production retention enforcement remain environment-owned follow-up work.
