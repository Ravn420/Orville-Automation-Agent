# M14.6 Reviewed Deployment-Provider Adapter

`orville_core.reviewed_deployment_provider.ReviewedDeploymentAdapter` is the provider-neutral integration boundary for production canary control. It wraps a provider-owned backend implementing deploy, traffic assignment, pause, rollback, and status operations.

The adapter defaults to dry-run mode, validates release identifiers and traffic percentages, rejects credential material where a protected reference is required, bounds backend calls with a configurable timeout, deduplicates equivalent operations using deterministic operation IDs, and redacts provider status before returning it to orchestration code. Provider credentials must be resolved and held by the deployment integration boundary; they are not accepted by operation methods, returned in status, or persisted by this adapter.

Production completion requires a reviewed provider-specific backend, workload identity or a protected secret-manager reference, authorization and approval checks, provider-side idempotency, durable operation/audit persistence, timeout cancellation semantics, traffic-control verification, rollback-target verification, and a non-production rollback drill. The local adapter is a contract and safety wrapper; it does not contact a real provider unless an explicitly supplied backend is used with `dry_run=False`.
