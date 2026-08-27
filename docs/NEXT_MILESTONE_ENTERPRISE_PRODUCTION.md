# Next Orville Milestone: Enterprise Production Readiness

**Milestone ID:** M14  
**Status:** Planned  
**Owner:** Orchestration Agent  
**Prerequisite:** Local M13 security and canary contracts are implemented and validated; production execution remains infrastructure-dependent.

## Objective

Move Orville from locally validated security and deployment contracts to an evidence-backed enterprise deployment. M14 must provision real execution boundaries, identity, secrets, monitoring, deployment control, backup, recovery, and operational ownership without weakening the fail-closed behavior established in M13.

## Task roadmap

| ID | Task | Owner | Dependencies | Acceptance gate |
|---|---|---|---|---|
| M14.1 | Provision enterprise environment and responsibility matrix | Automation Agent / Security Agent | Approved target environment | Named owners, tenant boundaries, data classifications, RTO/RPO, escalation paths, and rollback authority are documented. |
| M14.2 | Complete production trust-root ceremony | Security Agent | M13 trust-store and TUF contracts | Operator-reviewed root metadata, out-of-band pinned digest, rotation/revocation drill, and audit evidence pass. |
| M14.3 | Run live Windows/Linux sandbox validation | Security Agent / Verification Agent | M13 adapters, supported hosts | Worker IPC, filesystem, network, CPU/memory/PID limits, timeout, output validation, and cleanup pass on each supported host. |
| M14.4 | Add enterprise identity and authorization | Security Agent / IDE Agent | Tenant environment | SSO/OIDC or approved identity adapter, tenant isolation, least privilege, operator approval, revocation, and audit trails pass. |
| M14.5 | Integrate protected secret management | Automation Agent | Enterprise secret manager | Provider/deployment credentials are resolved at runtime, rotated, redacted, and absent from client bundles, logs, artifacts, and checkpoints. |
| M14.6 | Implement reviewed deployment-provider adapter | Automation Agent | M13 canary adapter and M14.1 | Dry-run deploy, status, traffic split, pause, rollback, timeout, idempotency, and credential-boundary tests pass. |
| M14.7 | Connect production metrics and health sources | Verification Agent | M14.4, M14.6 | Error, latency, saturation, business, security, and release metrics are tenant/cohort scoped with clock and sample-quality checks. |
| M14.8 | Execute non-production canary and rollback drill | Automation Agent / Verification Agent | M14.2–M14.7 | Canary advances and rolls back under injected faults; restart, duplicate events, partial failure, and rollback failure are recovered deterministically. |
| M14.9 | Establish backup, restore, and disaster recovery operations | Automation Agent / Security Agent | M14.1, M14.4 | Encrypted off-host backups, retention, restore verification, RTO/RPO evidence, access review, and recovery runbook pass. |
| M14.10 | Run production readiness and load gates | Verification Agent | M14.3, M14.8, M14.9 | Security, load, soak, dependency, observability, cost/quota, and rollback gates pass with retained sanitized evidence. |
| M14.11 | Controlled production canary | Automation Agent | All previous tasks and explicit operator approval | Smallest cohort launches with live monitoring, bounded hold, approval, rollback target, incident route, and post-deployment review. |

## Execution order

M14.1 and the responsibility matrix precede every production operation. M14.2–M14.5 may proceed in parallel after the environment is approved. M14.6 and M14.7 follow the identity and secret boundaries. M14.8 is the mandatory pre-production gate. M14.9 and M14.10 must pass before M14.11. No task may bypass the security release gate or use production credentials in local fixtures.

## Definition of done

M14 is complete only after a named enterprise environment passes live sandbox validation, trust-root ceremony and recovery, tenant authorization and secret rotation, a reviewed deployment adapter, a non-production canary and rollback drill, encrypted backup restoration, load/soak testing, and a controlled production canary with retained audit and monitoring evidence. If any prerequisite is unavailable, the task remains infrastructure-dependent rather than being represented as complete.
