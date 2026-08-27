# Graceful Degradation for Unavailable Connectors and Websites

## Purpose and scope

Orville remains usable when a connector, website, provider endpoint, or browser session is unavailable. Unavailability changes the actions that may be offered; it does not discard work, expose raw remote errors, broaden privacy routing, or authorize an unreviewed workaround. This contract complements `docs/GUI_DEGRADED_AVAILABILITY.md` and applies to API, GUI, workflow, and automation surfaces.

## Stable dependency states

| State | Meaning | Safe user-facing response |
|---|---|---|
| `connector_unavailable` | Connector is disabled, disconnected, unauthorized, rate-limited, or unreachable. | Explain the operation impact, continue without it when allowed, save a resumable draft, or retry. |
| `website_unavailable` | Website or browser target is unreachable, blocked, changed, or not authenticated. | Preserve the task and source list, offer a local/manual alternative, or retry. |
| `provider_unavailable` | Selected model provider or endpoint is not reachable or configured. | Use an explicitly compatible local fallback, save for later, or retry. |
| `partial_dependency` | Some requested sources or operations succeeded while another dependency failed. | Mark the result partial, identify missing evidence by safe identifier, and require review before completion. |
| `offline` | Network or external access is unavailable. | Keep local planning, saved state, artifacts, and review available; disable remote actions. |

Messages use stable state names, a plain-language explanation, the affected operation, a safe recovery action, and an optional redacted diagnostic reference. They must not include tokens, cookies, credentials, raw HTML, full URLs containing secrets, or untrusted remote instructions.

## Degraded workflow behavior

Orville preserves the objective, task graph, inputs, source identifiers, checkpoint, local artifacts, and transformation history when a dependency fails. Read-only planning, local validation, evidence review, export of sanitized records, and leaving the workspace remain available. A task that requires the unavailable dependency becomes `blocked`, `waiting_approval`, or `partial` according to the workflow contract; it is never reported as verified merely because the dependency was skipped.

A connector failure must not silently switch accounts, expand scopes, or route data to another provider. A website failure must not trigger an alternate site, bypass authentication, evade a block, or follow instructions returned by the failed site. A provider failure may use a local fallback only when it is explicitly configured, capability-compatible, within the same privacy class, and approved by the applicable routing policy. If no safe fallback exists, preserve the draft and stop at the dependency boundary.

## Retry and idempotency

Retries are bounded by the task or adapter policy. Retry only transient classes such as timeout, connection reset, or service-unavailable responses; do not retry authentication, permission, validation, policy, or approval failures until the underlying condition is corrected. Mutating operations require an idempotency key before retry; otherwise they remain blocked. Backoff, attempt count, operation identifier, and final failure class are retained as sanitized evidence.

Refreshing a page, reopening a connector, or retrying a request preserves user input and current task state. A repeated failure does not create duplicate artifacts, duplicate submissions, duplicate messages, or duplicate payments. Any fallback or retry that changes data routing requires a new explicit privacy and permission check.

## Partial results and evidence

Partial results are clearly labeled and include completed operation identifiers, missing dependency categories, safe source identifiers, verification status, and residual risks. Source evidence that was successfully collected remains available; missing or stale evidence is not invented or silently omitted. Independent verification must check that the result satisfies its acceptance criteria despite the unavailable dependency, otherwise the workflow remains blocked or failed.

Diagnostics contain only safe identifiers, dependency class, operation, status, bounded attempt metadata, and non-sensitive error class. Preserve sanitized logs and checkpoints according to the artifact-retention policy. Do not persist raw provider responses, page content, authorization headers, session cookies, or secret-bearing URLs.

## Recovery and escalation

The first recovery action is local and reversible: inspect redacted readiness, verify the configured dependency, save the draft, use an approved local fallback, or retry within policy. If the dependency remains unavailable, notify the responsible connector or operations owner with the operation identifier and safe diagnostic reference. Escalate to security for suspected credential exposure, permission bypass, malicious content, or unexpected routing; escalate to release or operations for repeated availability, integrity, or recovery failures.

Do not delete state, reset a database, rotate credentials, change account permissions, publish content, submit forms, or roll back production solely because a connector or website is unavailable. Those actions require a consequence preview, explicit scope-matched approval, and the applicable recovery procedure.

## Acceptance criteria and validation

The contract is accepted when each unavailable-dependency state has a stable explanation and safe recovery path; local planning and saved evidence remain usable; unavailable actions are blocked or clearly disabled; privacy routing and permissions do not broaden; retry behavior is bounded and idempotent; partial results are labeled; diagnostics are sanitized; and no unavailable dependency is represented as successful verification.

Run the credential-free documentation checks with:

```bash
python -m pytest tests/test_graceful_degradation.py -q
python -m py_compile tests/test_graceful_degradation.py
```

These checks validate the documented contract only. Live connector recovery, website availability, browser authentication, provider failover, alert delivery, and production network behavior remain environment-specific.
