# Orville 0.1.0 Release Notes

**Release date:** 2026-08-27  
**Maturity:** Initial standalone baseline  
**Package version:** `0.1.0`  
**Supported baseline:** Python 3.10+, standalone local process, packaged Windows releases, and documented Docker/Compose targets

## Added

Orville 0.1.0 provides a standalone dependency-aware task-graph engine with durable checkpoints, bounded retries, approval gates, cancellation state, independent verification, artifact preservation, provider-agnostic routing, local-model lifecycle controls, authenticated API routes, and Windows GUI workflow surfaces. It includes local-first fallbacks and credential-free validation paths so the core remains usable without Manus-specific services.

The release also includes documented deployment targets, environment-variable requirements, release gates, delivery procedures, security boundaries, accessibility criteria, workflow-state contracts, and representative acceptance tests.

## Changed

The initial baseline establishes `pyproject.toml` version `0.1.0` as the package version source of truth. Runtime defaults remain local-first: loopback API binding, SQLite storage, a local database path, explicit origin allowlisting, and bounded request rates. Optional providers, connectors, browser operations, deployment operations, and external notifications remain opt-in and approval-gated.

## Security and privacy

Credentials are supplied through approved environment or protected secret boundaries and are excluded from source-controlled release notes, artifacts, fixtures, and logs. High-impact external actions require explicit approval. The managed Blackbox relay credential remains server-side; the client release does not contain a Blackbox API key.

## Validation

The local baseline has been validated through the repository’s focused suites, release checks, representative workflow acceptance tests, security tests, and package/build checks recorded in `STATE.md`, `TASK_GRAPH.md`, and retained release evidence. Target-specific live provider, browser, connector, deployment, and production checks remain separate gates.

## Upgrade and rollback

Before upgrading, back up runtime data, verify the backup, review configuration changes, run the release checks, and retain the previous known-good release. Use the approval-gated procedures in `docs/DELIVERY_RUNBOOK.md`; do not delete databases, credentials, logs, backups, or release evidence during rollback.

## Known limitations

This initial release does not claim managed-cloud, Kubernetes, serverless, public multi-replica, or production deployment support without target-specific infrastructure validation. Provider credentials, external account authorization, live browser sessions, production monitoring, and deployment rollback evidence must be supplied and validated by the responsible environment owner.
