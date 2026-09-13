# Observability and Evaluation

## Observability

`JsonlTraceRecorder` writes one structured trace record per line and applies the existing `SecretRedactor` before persistence. This is a dependency-free baseline suitable for local development and test fixtures. Each record includes a trace identifier, UTC timestamp, event name, and redacted attributes.

Production deployments should adapt the record format to OpenTelemetry traces and metrics. The required dimensions are run ID, task ID, graph node, agent, provider, model, model version, tool, approval, retry, checkpoint, artifact, latency, finish reason, token usage, and failure class. Prompt, completion, tool argument, and tool result capture must be explicitly configured, redacted, access-controlled, and retention-limited.

## Deterministic evaluation

`evaluate_output()` provides a small acceptance evaluator. It checks that output exists, evaluates required textual criteria, and accepts additional deterministic check functions. It is intentionally not a substitute for running generated software. Repository-level evaluation must execute in an isolated reproducible environment, install dependencies, run tests, inspect the resulting diff, and record behavioral acceptance evidence.

## Release gates

| Gate | Required evidence |
|---|---|
| Package integrity | Compilation, installation from a clean environment, and import smoke test |
| Workflow correctness | Unit and integration tests for graph state, checkpoints, approvals, cancellation, retries, and resume |
| Provider safety | Fake-transport tests plus explicit credential, endpoint, capability, and fallback tests |
| Security | Tool, filesystem, network, redaction, prompt-injection, path traversal, and secret-leakage regression tests |
| GUI | Type check, production build, responsive previews, keyboard navigation, contrast, focus, and error-state checks |
| Evaluation | Representative acceptance fixtures with deterministic pass/fail thresholds |
| Operations | Health check, structured logs, backup/restore procedure, rollback procedure, and deployment smoke test |

## Failure handling

Every failed gate must become an actionable defect containing a reproduction command, expected result, observed result, severity, affected task or artifact, owner, and proposed remediation. A release must not be marked complete merely because the orchestration graph reached a terminal state.
