# Sensitive Payload Capture Policy

**Task ID:** `TODO-9ac53a3f1145`  
**Status:** Local policy and bounded in-memory implementation

Orville treats prompts, completions, tool arguments, and tool results as sensitive payloads. Capture is **disabled by default** and is not implied by ordinary tracing or run metadata. The `CapturePolicy` and `CaptureStore` in `orville_core/capture_policy.py` provide an explicit opt-in boundary for exceptional debugging or evaluation workflows.

| Control | Local contract |
|---|---|
| Opt-in | `enabled=False` is the default. Enabled capture requires explicit allow-listed readers and a positive retention period. |
| Redaction | Every payload is passed through `SecretRedactor` before retention; common API keys, bearer values, tokens, passwords, and credential fields are replaced. |
| Access control | Capture and read operations require an actor in `allowed_readers`; unauthorized actors fail closed with `SecurityViolation`. |
| Retention | Each record receives an expiry timestamp and is purged on capture/read or by an explicit `purge()` call. |
| Size bound | Strings are bounded by `max_payload_chars`; nested mappings, lists, and tuples are bounded recursively. |
| Storage | The local implementation is in-memory and does not persist sensitive payloads to files, SQLite, traces, or external services. |
| Scope | Supported kinds are `prompt`, `completion`, `tool_arguments`, and `tool_result`. Unknown kinds are rejected. |

The policy intentionally does not make raw capture safe for every environment. Operators must use synthetic data where possible, restrict reader identities, select the shortest useful retention, and avoid copying captured payloads into logs, screenshots, task state, or external systems. A production deployment requires independently reviewed durable-storage controls, encryption, access auditing, deletion guarantees, legal/organizational retention policy, and provider-specific privacy configuration.

The focused tests in `tests/test_capture_policy.py` verify default-off behavior, redaction, access denial, supported kinds, recursive size bounds, expiry, and fail-closed enabled-policy validation. No provider calls, credentials, personal data, or external mutations are used.
