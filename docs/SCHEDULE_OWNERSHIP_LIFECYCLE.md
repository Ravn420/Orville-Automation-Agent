# Schedule Ownership and Lifecycle Contract

## Scope and status

This document defines the schedule contract for recurring Orville workflows. It is a compatibility-first contract for scheduler, dispatcher, GUI, and future persistent-runtime implementations. Existing lease/claim behavior remains authoritative until the runtime fields described here are migrated; this document does not claim live provider notifications or production scheduling.

## Ownership

Every schedule belongs to exactly one project/workspace and records a non-secret owner identifier plus an audit trail of create, update, pause, resume, expire, and failure-notification decisions. The owner controls schedule configuration and may delegate operation through an authorized role. Workers receive only a bounded schedule identifier and lease metadata; they do not infer ownership from the worker identity or provider credentials.

| Responsibility | Owner |
|---|---|
| Create, edit, pause, resume, and expire schedule | Authorized project/workspace owner or delegated operator |
| Validate expression, interval, timezone, and expiration | Scheduler/API boundary |
| Select due work and hold an exclusive lease | Scheduler/dispatcher |
| Execute the workflow and record checkpoint/result | Orchestration engine and durable storage |
| Send failure notification through approved targets | Notification adapter after durable failure record |
| Review and revoke notification target | Owner/operator under project policy |

## Timezone handling

Schedules accept an IANA timezone identifier such as `UTC` or `Australia/Sydney`; fixed local abbreviations and ambiguous offsets are rejected. The scheduler evaluates calendar expressions in the declared timezone, normalizes due timestamps to UTC for storage and leases, and records both the declared timezone and normalized timestamp in audit metadata. A missing timezone defaults to `UTC` and is not silently inherited from the worker host. DST gaps are advanced to the next valid local occurrence; repeated wall-clock times run once according to the scheduler’s deduplication key.

## Expiration

A schedule may have an `expires_at` timestamp, stored and compared in UTC. It is valid only when later than its creation time. Expiration is fail-closed: an expired schedule is not selected as due, cannot acquire a new lease, and transitions to `expired` with the reason and timestamp retained. An in-flight execution is not silently terminated by expiration; it finishes or is cancelled through the normal workflow policy, while no subsequent run is dispatched.

## Pause and resume

Pause is an explicit owner/operator action that transitions an enabled schedule to `paused`, clears future due selection without deleting history, and retains the next planned occurrence. Resume is an explicit action that revalidates authorization, expiration, timezone, and schedule syntax before returning the schedule to `enabled`. Resume does not replay every missed occurrence by default; the missed-run policy is `skip` unless an explicitly configured bounded catch-up count is approved. Pause and resume are idempotent and auditable.

## Failure notifications

A failed execution is durably recorded before notification is attempted. Notification targets are approved non-secret references, never raw addresses or credentials in logs or task state. The notification adapter receives a bounded event containing schedule ID, workflow ID, execution ID, failure class, timestamp, retryability, and a safe remediation link or identifier; it never receives prompts, API keys, bearer tokens, local paths, or raw provider responses. Notification delivery is at-least-once with a bounded retry budget and deduplication key. Delivery failure does not change the authoritative execution result and is recorded as a separate notification outcome.

| Failure condition | Schedule behavior | Notification behavior |
|---|---|---|
| Retryable workflow failure | Apply the workflow retry policy; preserve schedule lease/checkpoint state. | Notify after the configured failure threshold or terminal failure. |
| Terminal workflow failure | Record failed execution; schedule remains enabled unless policy says otherwise. | Emit one deduplicated failure event to approved targets. |
| Expired schedule | Do not dispatch another run; retain history. | Optional expiration notice through approved targets. |
| Notification delivery failure | Do not mutate workflow success/failure state. | Retry within budget and record delivery failure safely. |

## Required state fields

The schedule contract requires `owner_id`, `timezone`, `expires_at`, `lifecycle_state` (`enabled`, `paused`, or `expired`), `missed_run_policy`, `catch_up_limit`, `failure_notification_targets`, and an audit record for transitions. Existing lease fields remain separate from lifecycle state. All changes require authorization, validation, and bounded audit metadata.

## Acceptance checks

A conforming implementation validates ownership and IANA timezone input, normalizes timestamps to UTC, prevents due selection after expiration or while paused, preserves history through pause/resume, applies an explicit missed-run policy, records failure before notification, bounds notification retries, and keeps notification payloads secret-safe. Focused tests cover these contract assertions. Runtime schema migration, live scheduler execution, notification-provider delivery, and production timezone/DST drills remain follow-up gates.
