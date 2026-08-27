# M14.7 Production Metrics and Health Sources

`orville_core.production_metrics` defines the standalone metrics boundary for canary health. A `HealthSource` supplies normalized samples for an explicit `(tenant_id, cohort, release_id)` scope. `ProductionMetrics` validates the scope and metric values, excludes stale samples through a caller-provided cutoff, aggregates request/error rates, latency, saturation, business health, security findings, and release quality, and can normalize a summary into the existing provider-neutral `HealthObservation` contract.

The local `InMemoryHealthSource` is intended for tests and dry runs. Production deployments must provide an approved monitoring adapter with tenant isolation, cohort labels, release identity, clock/freshness guarantees, bounded cardinality, access control, retention, and sanitized transport. The local implementation does not claim that a production metrics backend, alerting system, SLO policy, or business-health source is provisioned.

Metric samples contain no prompts, credentials, authorization headers, or arbitrary metadata. Cross-tenant and cross-cohort comparisons fail closed. Production readiness additionally requires validation of metric completeness, monitoring outage behavior, security-event ingestion, baseline/candidate comparison policy, and evidence retained for the non-production canary drill.
