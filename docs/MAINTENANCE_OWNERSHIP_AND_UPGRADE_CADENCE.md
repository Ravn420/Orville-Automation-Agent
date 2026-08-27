# Maintenance Ownership and Upgrade Cadence

## Purpose

This document assigns maintenance responsibility for the standalone Orville repository and defines a predictable upgrade cadence. Ownership identifies who prepares, reviews, approves, executes, and verifies a change; it does not grant credentials or authorize production actions.

## Roles and decision boundaries

| Area | Primary owner | Required reviewer | Execution boundary |
|---|---|---|---|
| Core engine, task graph, checkpoints, and workflow contracts | Orchestration Agent / core maintainer | Independent verification reviewer | Local tests and approved release process; compatibility changes require release review. |
| Provider, connector, browser, and model adapters | Integration maintainer | Security and boundary reviewer | Credentials remain environment-owned; live calls require configured permissions and approval. |
| Security, secrets, permissions, and untrusted-content controls | Security maintainer | Independent security reviewer | Fail-closed behavior, redaction, and approval gates must be reviewed before release. |
| Windows GUI and accessibility | GUI maintainer | Accessibility and visual reviewer | Validate supported Windows targets; do not infer production hardware coverage from local tests. |
| Packaging, deployment, backup, rollback, and release evidence | Release/deployment owner | Operations and security reviewers | Promotion, rollback, and credential rotation require explicit operator approval. |
| Documentation, changelog, and user-facing runbooks | Documentation owner | Relevant technical owner | Claims must match retained tests, artifacts, and target-specific evidence. |
| Incident response and recovery | Operations owner | Security and release owners | The incident owner coordinates containment; no credential or destructive action is inferred from an alert. |

The **Orchestration Agent** owns task-graph integration and durable project state. The **environment owner** remains accountable for live infrastructure, external credentials, hosted monitoring, backups, and production approvals. When an area has no assigned person, the change is blocked rather than silently assigned to an unreviewed operator.

## Standard cadence

| Cadence | Required activity | Evidence |
|---|---|---|
| Every change | Run focused tests, compilation, secret checks, and applicable review gates. | Test command, result, changed paths, reviewer, and residual risks. |
| Weekly | Review open failures, dependency alerts, backup freshness, release evidence, and blocked work. | Sanitized maintenance review record. |
| Monthly | Review supported targets, environment variables, connector scopes, access grants, operational metrics, and recovery readiness. | Signed or approved maintenance checklist. |
| Quarterly | Review dependency versions, transitive packages, downloaded scripts/artifacts, provider API changes, threat model, and disaster-recovery exercise status. | Supply-chain review, compatibility report, and recovery evidence. |
| Before every release | Verify version, changelog, release notes, full tests where feasible, target smoke checks, backup, rollback target, and approval. | Release record and retained checksums/evidence. |
| After every release | Observe health, error rate, retry/failure metrics, verification outcomes, and user-impact signals; close only after the observation window passes. | Post-release report or incident record. |

Security advisories, credential exposure, data integrity concerns, repeated health failures, unsupported dependency changes, or a failed rollback trigger an **immediate review** and suspend routine cadence until the incident owner resolves or accepts the risk.

## Upgrade policy

Routine upgrades are grouped into the monthly maintenance window when risk permits. Security fixes, end-of-support deadlines, exploitable dependency issues, broken provider contracts, or data-integrity fixes are expedited. Major upgrades require a compatibility assessment, migration plan, backup verification, rollback target, and explicit approval before execution.

Each upgrade record must include the current and target versions, reason, affected components, dependency and supply-chain review, configuration changes, migration steps, test results, target limitations, owner, reviewer, approval, and rollback procedure. Version changes must follow `docs/VERSIONING_AND_RELEASE_NOTES.md`; secrets and personal data must never appear in the record.

## Handoff and escalation

A maintenance handoff identifies the owner, task or incident ID, inputs, changed paths, validation performed, known limitations, and unresolved risks. Escalate to the security owner for secret exposure, permission bypass, untrusted-content execution, or suspicious artifacts; to the release/deployment owner for rollback, backup, or target failures; and to the core maintainer for data-model or compatibility regressions. If ownership or approval is ambiguous, stop at the planning boundary and record the blocker.

## Standalone validation

The ownership and cadence contract is documentation-only and credential-free. Validate its structure with:

```bash
python -m pytest tests/test_maintenance_ownership.py -q
python -m py_compile tests/test_maintenance_ownership.py
```

Live schedules, alert delivery, infrastructure monitoring, dependency scanners, and recovery exercises remain environment-specific responsibilities.
