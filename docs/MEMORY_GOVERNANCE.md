# Memory Governance

## Purpose

This document defines the boundaries for task memory and long-term project memory. It is a policy artifact, not a storage implementation, and it does not authorize retaining secrets or user data.

## Short-term task memory

Short-term task memory contains only the minimum context required to complete the active task: the current request, user-approved constraints, selected repository paths, relevant validation output, and unresolved risks. It is scoped to the active task thread and is discarded when the task closes unless the user explicitly requests a sanitized handoff record.

Credentials, access tokens, private keys, browser cookies, raw authentication headers, and unrelated personal data are never eligible for short-term memory. Diagnostics must use references, redaction, and hashes rather than secret values.

## Long-term project memory

Long-term project memory contains durable project facts that remain useful across task turns: architecture decisions, approved operating constraints, dependency relationships, evidence locations, known blockers, and completed milestone records. It is stored only in reviewed project control files or explicitly approved project artifacts.

Long-term memory must not become a transcript archive. Raw prompts, full tool output, secrets, private user content, and transient scratch data are excluded unless a separate retention decision explicitly permits a sanitized excerpt.

## Retention and deletion

Each memory record has an owner, purpose, creation date, retention class, and deletion condition. Task-scoped context expires at task closure. Evidence records persist only for the project retention period or until the corresponding milestone is superseded. Deletion requests remove the applicable project-memory record and its derived copies, subject to a documented legal or audit hold.

Deletion is fail-closed: an incomplete deletion operation is reported as unresolved and does not claim completion. Backups, caches, logs, and generated artifacts must be included in the deletion inventory.

## Isolation

Memory is isolated by project, task thread, user authorization, and sensitivity class. A task may read only the project files and evidence required by its acceptance criteria. Memory from another project or user is not imported by default. Cross-project reuse requires an explicit, sanitized handoff reference.

## User editing and auditability

Users may inspect and edit project-memory policy records through reviewed project controls. Every edit records the actor, reason, timestamp, affected record, and resulting revision. User edits cannot bypass secret redaction, scope isolation, retention deletion, or approval gates.

## Acceptance rule

No memory feature is complete until the scope, retention, deletion, isolation, user-editing, secret-exclusion, and audit requirements are documented and covered by focused validation.
