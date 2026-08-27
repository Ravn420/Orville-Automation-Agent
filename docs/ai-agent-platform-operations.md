# Orville AI Agent Platform Operations

## Lifecycle operations

Treat `PlatformStore` as the local control-plane source of truth for projects, tasks, plans, approvals, and task events. Use the event sequence as a reconnect cursor. A plan must be reviewed before approval; rejected plans remain auditable and do not create repository mutations. Approved tasks are currently recorded at `workspace_ready` and require an execution adapter for later mutations.

## Validation operations

After every meaningful change, run the unit-test discovery command and compile check. For later execution milestones, extend the validation ladder with formatter/linter, type checking, integration tests, production build, browser smoke tests, accessibility checks, security checks, and revision-pinned preview verification. Bounded repair must stop after three attempts for a failure class and preserve the failure evidence and attempted fixes.

## Recovery operations

Use immutable revision identifiers and parent relationships for rollback. Workspace snapshots are local development artifacts and should not be treated as disaster recovery. Production operation requires durable revision/object storage, database backups, migration previews, release records, health checks, and a tested rollback target.

## Monitoring and audit

Retain append-only task events with sanitized payloads, tool status, affected paths, validation results, approvals, and artifact references. Add metrics for task duration, validation pass rate, repair attempts, provider failures, workflow retries, preview health, deployment health, and rollback frequency in later milestones.

## Recommended sequence

The next milestone should connect approved control-plane tasks to isolated workspace sessions and structured repository tools. Subsequent milestones should add the validation ladder, preview runner, identity and secret adapters, workflows, connectors, Git synchronization, deployment, and security/evaluation centers. Unsupported capabilities must remain unavailable or mock-backed until their provider, credential, and permission requirements are configured.
