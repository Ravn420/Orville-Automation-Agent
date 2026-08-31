# Standalone Windows Equivalents and Manus Capability Boundaries

**Status:** Repository contract for the standalone Windows distribution  
**Owner:** Orchestration Agent  
**Updated:** 2026-08-28

## Purpose and boundary

Orville must remain useful when it is running as a local Windows application without Manus-hosted services. This document maps each integration family to a concrete local or user-configured substitute, identifies the approval and secret boundary, and states where literal Manus parity is not possible. An equivalent means the same operational class of result can be achieved; it does not mean that proprietary service behavior, capacity, latency, or user interface is reproduced.

> **Important distinction:** Manus-specific capabilities are optional adapters. Their absence must produce an explicit `unavailable`, `blocked`, or `awaiting approval` capability state rather than a silent failure or a claim of literal parity.

## Equivalent matrix

| Capability family | Standalone Windows equivalent | Local boundary and safe default | Manus-specific behavior not reproduced literally |
|---|---|---|---|
| Connectors and external apps | Versioned connector adapters using HTTPS APIs, local loopback services, filesystem adapters, and user-configured MCP-compatible bridges | Store only redacted connector metadata in the repository; keep secrets in environment variables, Windows DPAPI-backed storage, or a secret manager; require explicit approval for writes and destructive actions | Manus first-party connector catalog, managed OAuth handoff, hosted connector credentials, and proprietary connector execution fabric |
| Schedules and recurring work | Windows Task Scheduler or a long-running local Orville worker invoking the documented CLI/API; persisted interval schedules and idempotency keys remain the source of truth | Default to disabled/manual schedules, bounded concurrency, durable checkpoints, retry limits, and a local SQLite state directory outside source control | Manus-managed scheduler availability, hosted wake-up guarantees, fleet-level failover, and platform-wide schedule monitoring |
| Notifications | Local desktop notifications, Windows Event Log, email/webhook adapters configured by the user, and a sanitized local notification log | Notifications are opt-in, rate-limited, secret-redacted, and never treated as proof that a remote action succeeded; external sends require approval where applicable | Manus notification delivery, hosted inbox/task updates, managed delivery retries, and proprietary notification routing |
| Deployment helpers | PowerShell scripts, Docker Compose, local health checks, packaged Windows release artifacts, checksum verification, backup/restore, and provider-neutral deployment instructions | Preview and packaging are local; production deployment remains approval-gated; deployment helpers must not embed secrets or silently mutate accounts | Manus-managed cloud computer provisioning, hosted deployment orchestration, proprietary release infrastructure, and automatic environment repair |
| Observability | Structured JSONL/local SQLite event records, OpenTelemetry-compatible traces and metrics, `RunMetadata`, sanitized audit records, and exportable reports | Capture provider/model identifiers, timing, status, retries, approvals, artifacts, and safe error classes; hash or omit prompts according to privacy policy; keep logs bounded and redact secrets | Manus internal telemetry, hosted trace UI, proprietary cost accounting, platform-wide correlation, and service-side retention guarantees |
| Model execution | Ollama or another local OpenAI-compatible runtime, user-configured hosted APIs, and the existing provider adapters | Explicit endpoint preflight, capability checks, bounded timeouts, local-only fallback, and no credential values in logs or fixtures | Manus-hosted model selection, private model fleet, proprietary routing policy, and guaranteed hosted capacity |
| Browser operation | A separately installed Playwright/browser-session adapter with visible user takeover, domain allowlists, and action audit records | Disabled until a browser session and approval are available; no silent login, CAPTCHA bypass, or uncontrolled browsing | Manus browser session, managed login state, hosted browser computer, and proprietary browser-operator orchestration |
| Artifact storage and sharing | Local project directory, configured portable/AppData directory, ZIP export, checksums, and an optional user-configured S3-compatible endpoint | Enforce path containment, retention policy, redaction, and explicit export/share approval; generated media is temporary unless deliberately retained | Manus-managed artifact storage, public share links, hosted retention, and proprietary access-control integration |

## Operational rules by family

### Connectors

A standalone connector is a reviewed adapter with a declared provider, capability set, endpoint allowlist, timeout, retry policy, redaction policy, and approval requirement. Read-only discovery may run locally when configured. Create, update, delete, send, publish, permission, and account operations must fail closed until the user authorizes the exact target and scope. A connector that cannot be configured is `unavailable`, not a degraded imitation of a hosted connector.

### Schedules

The Windows equivalent is an ordinary scheduled task or an Orville worker process that starts the local entry point. The schedule record must include an owner, workflow identifier, interval or trigger, next-run time, enabled state, idempotency key, retry/dead-letter policy, and last outcome. The scheduler must not imply that work continues while the Windows host, worker, and storage are stopped. Recovery after restart is based on persisted checkpoints and duplicate-safe execution.

### Notifications

A notification describes an observed local state transition; it is not an authorization mechanism. The local implementation may write to a file or Windows Event Log and may call a configured email or webhook adapter. The message must contain a safe run identifier, state, timestamp, and recovery action, while excluding prompts, tokens, private keys, cookies, and unredacted tool payloads. Delivery failure is recorded separately from the underlying task outcome.

### Deployment helpers

PowerShell, Docker Compose, and the packaged Windows distribution provide the standalone path. Helpers may validate configuration, build a release, start a local preview, check health, create a backup, and document rollback. They must not deploy to a production account, alter DNS, rotate credentials, or delete resources without an explicit approval gate. A provider-specific deployment adapter is an optional extension, not a requirement for local use.

### Observability

The standalone recorder must work without a telemetry vendor. Local traces and metrics are the default; OTLP export is opt-in and requires a user-configured endpoint. Events must preserve enough evidence to diagnose graph-node execution, agent handoffs, model calls, tool/MCP calls, approvals, retries, artifacts, latency, and failures without storing sensitive payloads by default. The absence of an OTLP endpoint must not prevent Orville from running or recording local evidence.

## Capability-state vocabulary

Every optional integration should expose one of the following states in the standalone UI and diagnostics.

| State | Meaning | Required user-facing action |
|---|---|---|
| `ready` | The local equivalent is configured and passed preflight | Permit the operation subject to ordinary approval rules |
| `configured` | Configuration exists but the operation needs a run-time check or approval | Show the missing check or approval target |
| `awaiting_approval` | The requested operation is understood but has external or destructive side effects | Show exact target, scope, consequence, and expiry |
| `degraded` | The local equivalent is available with bounded limitations | Explain the limitation and offer a safe fallback |
| `blocked` | Policy, missing dependency, missing session, or unsafe configuration prevents use | State the blocker; do not retry silently |
| `unavailable` | No local adapter or configured service exists | Explain the non-reproduced capability and provide configuration guidance |

## Installation and validation expectations

A standalone Windows release should validate without Manus credentials. The minimum smoke path is:

1. Run the documented local configuration command with synthetic or empty optional credentials.
2. Start the local API/GUI and confirm New Task, planning, execution, verification, artifacts, and state inspection work with a local provider or deterministic test provider.
3. Create a disabled interval schedule and verify the persisted record without waiting for an external service.
4. Emit a sanitized local notification and inspect its safe identifier and state text.
5. Run deployment-helper preflight and local health checks without publishing or changing an account.
6. Record a local observability event and, if an OTLP endpoint is configured, verify export is optional and failure does not stop the run.

The repository’s focused test suite should assert that every equivalent has a local fallback, that secrets are excluded from examples and diagnostics, and that proprietary-only features are explicitly marked unavailable or blocked rather than represented as complete parity.

## References

[1]: https://learn.microsoft.com/en-us/windows/win32/taskschd/task-scheduler-2-0-examples "Microsoft Learn — Task Scheduler 2.0 Examples"

[2]: https://opentelemetry.io/docs/ "OpenTelemetry Documentation"

[3]: https://learn.microsoft.com/en-us/windows/security/identity-protection/credential-guard/ "Microsoft Learn — Windows credential protection concepts"

[4]: https://docs.docker.com/compose/ "Docker Docs — Compose"

[5]: https://manus.im/docs/introduction/welcome "Manus Documentation — Welcome"

The first four references describe public standalone technologies. The Manus reference is included only to identify the external product boundary; this repository does not depend on it for local execution.
