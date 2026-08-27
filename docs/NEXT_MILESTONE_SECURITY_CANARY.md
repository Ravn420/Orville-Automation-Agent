# Next Orville Milestone: Security Hardening and Automated Canary Deployments

**Milestone ID:** M13  
**Status:** Planned  
**Owner:** Orchestration Agent  
**Primary workstreams:** Security Agent, Automation Agent, Verification Agent, Prototype Agent  
**Scope assumption:** The milestone targets standalone deployments first. Production cloud credentials, tenant infrastructure, signing keys, and deployment-provider accounts are not assumed to be available in the local repository.

## Summary

This milestone closes the highest-risk gaps in process isolation, artifact trust, credential protection, and production rollout safety. It introduces platform-specific sandbox adapters and fail-closed attestation enforcement, then connects release gates to an automated canary controller that progressively shifts traffic only when health, error, latency, security, and rollback criteria remain within policy.

## Requirements and prerequisites

| Requirement | Needed for | Owner | Exit condition |
|---|---|---|---|
| Supported execution target matrix | Sandbox adapters and canary runners | Security Agent | Windows and Linux support levels are documented; unsupported hosts fail closed or remain explicitly local-only. |
| Non-root worker/runtime boundary | Sandbox execution and deployment | Security Agent / Automation Agent | Worker identity, filesystem mounts, network mode, resource limits, and process lifetime are enforceable. |
| Pinned verifier dependency | Attestation checks | Security Agent | Cosign/in-toto and optional TUF versions are pinned and validated without runtime downloads. |
| Trust-root lifecycle policy | Model and release verification | Security Agent | Bootstrap, rotation, revocation, expiry, and rollback behavior are approval-gated and auditable. |
| Deployment-provider adapter | Canary rollout | Automation Agent | Adapter supports deploy, health, traffic split, pause, rollback, and status operations with dry-run mode. |
| Metrics and event source | Canary decisions | Verification Agent | Metrics expose request count, error rate, latency percentiles, resource saturation, security findings, and audit events by release and cohort. |
| Secret manager or protected references | Production deployment | Automation Agent | Deployment credentials are resolved at runtime and never serialized into manifests, artifacts, or logs. |

## Task graph

### Security hardening workstream

| Task | Agent | Dependencies | Deliverables | Acceptance criteria |
|---|---|---|---|---|
| M13.1 Security baseline and threat model refresh | Security Agent | Existing `AGENTS.md`, `SECURITY_HARDENING_PLAN.md` | Threat model, protected assets, trust boundaries, abuse cases, platform matrix | Every new component has a documented trust boundary, input validation rule, failure mode, and audit requirement. |
| M13.2 Windows isolated worker adapter | Security Agent / Prototype Agent | M13.1 | `.wsb` generation, mapped read-only model input, writable output mapping, disabled networking, bounded resources | Harmless fixture runs outside the API process; undeclared mounts, network access, inherited credentials, output traversal, and timeout violations fail closed. |
| M13.3 Linux isolated worker adapter | Security Agent | M13.1 | Bubblewrap/container adapter, non-root execution, read-only root, private temp, no network by default, limits | Fixture runs outside the API process with dropped capabilities and bounded CPU, memory, PIDs, disk, lifetime, and output size. |
| M13.4 Sandbox execution integration | Code Synthesis Agent / IDE Agent | M13.2, M13.3 | Model inspection/conversion/loading/execution adapter path | No model code executes in GUI/API host; all lifecycle transitions include digest, policy ID, worker ID, and result status in redacted audit records. |
| M13.5 Trust-store lifecycle | Security Agent | M13.1 | Persistent trust store with approved bootstrap, rotation, revocation, expiry, and rollback | Unknown, revoked, expired, wrong-key, wrong-digest, malformed, and missing attestations fail closed for required policies. |
| M13.6 Cosign/in-toto and optional TUF verification | Security Agent | M13.5 | Version-pinned verifier adapters and synthetic signed fixtures | Valid fixtures verify; tampered payloads and metadata, rollback/freeze conditions, missing attestations, and unavailable verifiers produce stable diagnostics. |
| M13.7 Security release gate | Verification Agent / Automation Agent | M13.4, M13.6 | Extended `tools/release_gate.py`, negative-boundary fixtures, sanitized evidence | The gate blocks release on failed sandbox, trust, secret-redaction, dependency, or audit checks and emits reproducible evidence. |

### Automated canary deployment workstream

| Task | Agent | Dependencies | Deliverables | Acceptance criteria |
|---|---|---|---|---|
| M13.8 Canary policy schema | Automation Agent | M13.1, M13.7 | Versioned policy for cohorts, traffic steps, hold periods, health thresholds, approval mode, and rollback | Invalid thresholds, non-monotonic traffic, missing rollback target, and unbounded hold times are rejected. |
| M13.9 Deployment adapter contract | Automation Agent / Code Synthesis Agent | M13.8 | Provider-neutral deploy/status/traffic/pause/rollback interface with dry-run implementation | All mutations are approval-gated or explicitly authorized by policy; credentials remain outside client and artifacts. |
| M13.10 Canary controller state machine | Automation Agent | M13.8, M13.9 | Durable states: planned, deploying, observing, advancing, paused, rolled_back, completed, failed | Restart recovery is deterministic; duplicate events are idempotent; no traffic advance occurs without a fresh health decision. |
| M13.11 Canary health evaluator | Verification Agent | M13.10 | Error, latency, saturation, security, and business-health evaluation with confidence/minimum-sample rules | Sparse samples do not falsely pass; any critical security finding pauses or rolls back; all decisions include metric windows and reasons. |
| M13.12 Automated rollback and quarantine | Automation Agent / Security Agent | M13.10, M13.11 | Traffic reset, release quarantine, incident event, and operator override with approval | Rollback is bounded and idempotent; failed rollback creates an actionable blocked state and never reports success. |
| M13.13 Canary observability and audit | Verification Agent | M13.10, M13.11 | Release/cohort metrics, decision trace, audit records, and redacted operator report | Every deployment mutation and decision is attributable to release, tenant, cohort, actor/policy, timestamp, and outcome without secrets. |
| M13.14 Local synthetic canary runner | Prototype Agent | M13.9–M13.13 | Standalone simulator and deterministic fault injection | Simulates success, elevated errors, latency regression, capacity exhaustion, security finding, crash, and rollback failure. |
| M13.15 Production deployment integration | Automation Agent | M13.9–M13.14, enterprise credentials | Reviewed provider adapter and environment-specific deployment manifests | Dry-run passes first; live canary requires explicit approval, protected credentials, health evidence, rollback target, and recovery drill. |

## Execution order and parallelization

M13.1 is the prerequisite for both workstreams. After M13.1, M13.2–M13.3 may proceed in parallel, while M13.5 may proceed independently. M13.4 depends on both platform adapters. M13.6 depends on the trust store. M13.7 is the security gate before production deployment.

For canary delivery, M13.8 and M13.9 can proceed in parallel after M13.1 and the security gate contract is defined. M13.10 depends on both, M13.11 can be developed against the state-machine contract, and M13.12–M13.14 follow the controller and evaluator interfaces. M13.15 is last and remains infrastructure-dependent.

## Release and rollback gates

A release may enter canary only when compilation, unit tests, security negative tests, dependency checks, artifact verification, secret scanning, and configuration validation pass. The first traffic step must be the smallest configured cohort and must observe a minimum sample count and hold period. Advancement requires all configured metrics to remain within threshold and no critical audit or security event.

Any critical security finding, provider authentication failure, unavailable rollback target, sustained error threshold breach, latency threshold breach, resource exhaustion, or unverifiable release artifact must pause or roll back. A rollback must restore the last known-good release and traffic allocation, quarantine the failed release, write an audit event, and expose a blocked state if restoration is incomplete.

## Validation plan

The Verification Agent must run focused sandbox and attestation tests, canary state-machine tests, idempotency and restart tests, fault-injection tests, secret-redaction scans, and release-gate checks. The Automation Agent must run the local synthetic canary runner in dry-run mode and preserve sanitized evidence under `artifacts/`. Live deployment testing requires explicit approval, a non-production environment, synthetic traffic, protected credentials, and a verified rollback target.

## Next actions

1. Complete M13.1 and approve the threat model and platform support matrix.
2. Implement the Windows and Linux adapters with negative-boundary fixtures.
3. Finalize the trust-store and attestation verification gates.
4. Define the canary policy schema and provider-neutral deployment adapter.
5. Build the durable controller, evaluator, rollback path, and synthetic runner.
6. Add release-gate integration and conduct a non-production recovery drill.
7. Only after those gates pass, configure a production-specific deployment adapter.

## Definition of done

M13 is complete when supported platforms enforce process isolation, required artifact attestations fail closed, trust-root changes are auditable and recoverable, the security release gate blocks unsafe artifacts, the canary controller survives restart and duplicate events, health-based advancement and rollback are deterministic, all mutations are auditable and secret-free, and a non-production canary plus rollback drill has passed. Production deployment remains incomplete until its environment-specific credentials, identity, monitoring, backup, and recovery controls are explicitly provisioned.


## Implementation checkpoint — 2026-08-27

The local implementation now includes the Windows Sandbox and Linux bubblewrap adapter contracts, fail-closed sandbox selection, persistent trust-store and attestation controls, the local security release gate, a provider-neutral synthetic deployment adapter, SQLite-backed canary state, minimum-sample health evaluation, approval-gated advancement, pause/quarantine behavior, idempotent rollback, and secret-filtered canary audit records. The API exposes `/api/v1/canary/runs` creation, deployment, observation, rollback, status, and audit inspection routes.

Validation completed with Python compilation and **287 passing tests** with one existing Starlette/httpx deprecation warning. The local synthetic implementation is not a production deployment provider. M13.15 remains infrastructure-dependent until a deployment target, protected credentials, tenant identity, monitoring source, non-production environment, and operator-approved rollback drill are available.
