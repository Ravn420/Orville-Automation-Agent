# Orville Security Threat Model

## Scope and assumptions

This threat model covers Orville’s agent orchestration, model and provider lifecycle, connector/MCP boundary, local workspace, external actions, GUI/API, and evidence stores. Imported files, retrieved content, provider responses, connector output, model output, task text, and repository instructions are treated as **untrusted data** unless a separately authorized policy verifies them. Credentials are process-scoped secrets and are never trusted merely because a model, task, or connector requests them.

## Protected assets and trust boundaries

| Asset or boundary | Security objective | Primary control owner |
|---|---|---|
| User credentials, tokens, and connector secrets | Confidentiality, scope binding, revocation | Secret and connector layers |
| Task, approval, and execution state | Integrity, authorization, auditability | Orchestration engine |
| Local files and model artifacts | Integrity, provenance, non-execution | Model and workspace layers |
| Provider, MCP, and browser actions | Explicit scope, least privilege, no confused deputy | Integration layers |
| Agent/model prompts and outputs | Separation of instructions from untrusted data | Prompt/output boundary |
| Evidence, logs, and telemetry | Redaction, retention, reviewer traceability | Evidence and observability layers |
| Host filesystem, network, and processes | Least privilege and containment | Sandbox/environment layer |

The principal trust boundaries are user-to-API, API-to-task state, task-to-agent/model, model-to-tool, connector-to-provider, imported-file-to-runtime, and sandbox-to-host. Crossing a boundary requires an explicit contract, validation, and an auditable decision. A successful network response or model response is not proof of authorization.

## Threat register

| Threat | Abuse case and impact | Required mitigations | Detection and evidence | Residual risk |
|---|---|---|---|---|
| Prompt injection | Retrieved text or an imported artifact instructs an agent to ignore policy, disclose secrets, or perform an external action. | Label untrusted content; separate system/developer/user instructions, retrieved data, tool results, and approvals; never let content grant capabilities; require deterministic policy checks before tools. | Boundary labels, rejected tool decision, redacted event record, regression case. | Novel indirect injection can still influence planning; human review remains required for high-impact actions. |
| Excessive agency | A model chains individually permitted tools into an unsafe result or operates beyond the user’s intended scope. | Per-task capability allowlist, bounded budgets, single-purpose tools, approval gates, target/scope confirmation, expiry, cancellation, and fail-closed unknown actions. | Capability decision log, approval record, budget counters, terminal outcome. | Mis-scoped user approval or a policy defect can still authorize too much. |
| Insecure output handling | Model output is treated as shell code, HTML, SQL, a path, or a connector request without validation. | Typed output contracts, escaping/parameterization, path containment, command allowlists, schema validation, and deterministic executors for safety-critical operations. | Validation diagnostics, rejected output evidence, sanitized previews. | Parser bugs and downstream systems outside Orville remain possible. |
| Sensitive information disclosure | Prompts, tool arguments, traces, errors, or artifacts expose credentials, private paths, tokens, or user data. | Secret scanning/redaction, metadata-only evidence, access-controlled logs, opt-in content capture, bounded retention, and no secret persistence in task state. | Redaction test fixtures, evidence projection, audit access record. | New secret formats or third-party logs may evade local patterns. |
| Supply-chain compromise | A provider package, model file, connector, dependency, or conversion tool contains malicious code or tampered content. | Checksum/provenance/license/attestation gates; safe formats; never execute imported sidecars; isolated conversion/loading; dependency review and pinned versions. | Hash, source, license, attestation, inventory, sandbox result, review disposition. | A compromised trusted source or runtime still requires external verification. |
| Context poisoning | Stale, conflicting, or malicious memory, task state, or retrieved context changes decisions invisibly. | Owner/project scoping, provenance and timestamps, bounded retention, explicit memory editing/purge, conflict visibility, and no silent promotion into instructions. | Context source references, memory audit events, conflict diagnostics. | Human interpretation of conflicting context remains fallible. |
| Unbounded tool access | A worker discovers or invokes tools/connectors beyond its task, network, filesystem, or credential scope. | Allowlisted operations, per-task credentials, egress/host/port controls, sandbox boundaries, approval-backed high-impact operations, and deterministic selection. | Selection trace, denied-operation reason, connector scope and approval evidence. | Environment-level privileges can exceed application policy if deployment is misconfigured. |

## Control ordering

Orville should apply controls in this order: classify the input as trusted or untrusted; validate syntax and schema; resolve the target and scope; check capability and credential binding; check resource and rate budgets; require explicit approval when the action is high impact; execute through the least-privilege boundary; record redacted evidence; and reconcile the observed result with the requested intent. Failure at any step is a blocked or review outcome, never an implicit approval.

## Acceptance criteria

The threat model is complete for the current local contract when each threat category has a named abuse case, mitigation family, detection/evidence path, and residual-risk statement; high-impact actions remain approval-gated; imported and retrieved content cannot grant permissions; secret-safe evidence is defined; and focused tests cover prompt/output separation, untrusted labels, least-privilege tool selection, secret redaction, and deterministic rejection of unsafe output. Live provider, deployment, browser, and production credential exercises remain environment-owned.
