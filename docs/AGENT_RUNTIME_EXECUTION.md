# Bounded Agent Runtime Execution

## Scope

Orville now provides a local execution boundary for a persisted `TaskThread` through `AgentRuntimeStore.execute_thread`. This is a deterministic runtime wrapper around a caller-supplied handler; it does not select a provider, invoke a model, execute arbitrary commands, or grant connector permissions.

## Lifecycle

1. A `planned` or recovered thread is transitioned to `running`.
2. The runtime validates that a referenced agent profile exists and is enabled before changing lifecycle state.
3. The handler receives only the thread request and a safe context containing identifiers, declared skills, connectors, and tool permissions.
4. Results are redacted, JSON-size bounded, persisted as an assistant `agent_result` message, and the thread is stopped with `stop_reason=completed`.
5. A stopped thread replays its persisted result and never invokes the handler again.
6. Handler failures are redacted, persisted as an `agent_error` message, and transition the thread to `failed`.
7. Failed threads remain non-retryable until the caller explicitly passes `retry_failed=True`; retry transitions through `recovering` before execution.

## Safety boundaries

- Disabled profiles fail closed while the thread remains `planned`.
- Output is limited to 65,536 UTF-8 bytes by default; callers may select a smaller positive limit.
- Secrets in result fields and exception messages are redacted before persistence and return.
- The runtime does not infer approval for sensitive operations. A handler that needs approval must use the existing task-thread waiting/approval contract.
- Provider-specific idempotency, external side-effect compensation, sandbox selection, and production deployment remain owned by their existing subsystems.

## Local validation

```bash
python -m pytest -q tests/test_agent_runtime.py tests/test_task_threads.py
python -m py_compile orville_core/agent_runtime.py tests/test_agent_runtime.py
```

The contract is intentionally standalone-capable and can be exercised with a pure local Python handler. No cloud credentials or model provider calls are required.
