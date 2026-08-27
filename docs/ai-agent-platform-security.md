# Orville AI Agent Platform Security

## Current protections

The API requires a bearer token and applies a request-rate limit. File artifacts and workspace paths are constrained by canonical-root policies. Network requests use explicit host allowlists where the provider layer applies them. Tool policies fail closed until tools are allowlisted and approved. Dry-run mode blocks external side effects. Structured event payloads are recursively redacted for common secret fields and bearer tokens.

Workspace commands execute without a shell from a temporary workspace and are limited to an executable allowlist, timeout, bounded output, and an explicit working directory. Writes can require an expected SHA-256 checksum, preventing stale agent output from silently overwriting newer content.

## Approval boundaries

Plan approval is required before a task can enter `workspace_ready`. Future policy gates must require explicit approval for authentication or access-control changes, migrations, external integrations, production configuration, publishing, payments, deletion, credential changes, public communication, and other destructive or high-impact actions.

## Known limitations

The current token is a local development authentication mechanism, not a multi-user identity and authorization system. The local workspace is bounded but is not a hardened container or VM sandbox. It does not yet enforce cgroups, non-root identity, process quotas, package-source firewalling, or production network isolation. Secret values are redacted from supported structured events, but a production deployment still requires encrypted secret references and pre-persistence/export secret scanning.

## Required production hardening

Before external exposure, add durable identity, project membership authorization, encrypted server-side secret storage, non-root isolated execution, CPU/memory/disk/process limits, network egress policy, package policy, child-process cleanup, security scanning, audit retention, dependency scanning, and deployment-specific release approvals. Treat all external provider results, imported files, browser content, and model outputs as untrusted data.
