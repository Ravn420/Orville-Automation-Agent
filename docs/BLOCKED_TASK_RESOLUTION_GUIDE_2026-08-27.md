# Blocked Task Resolution Guide

**Review date:** 2026-08-27
**Scope:** Explicitly blocked `TASK_GRAPH.md` records, the tracked cleanup blocker, and dependency-gated production items
**Purpose:** State the exact evidence, authority, and safe next action required to resolve each blocked workstream without broadening permissions or misrepresenting local work as production completion.

> A blocked task is resolved only when its named prerequisite, approval, or environment condition is satisfied and independently evidenced. No blocker may be bypassed by using unapproved credentials, scraping browser sessions, deleting material without confirmation, or treating a local mock as live-provider evidence.

## 1. Explicitly blocked task-graph records

| ID | Task and current status | Blocking condition | Safe resolution path | Closure evidence |
|---|---|---|---|---|
| M9 | Hardened execution infrastructure — `blocked-by-infrastructure` | No approved non-root container/VM with resource, network, and package-source controls | Select an approved execution host; define CPU, memory, disk, process, network-egress, filesystem, and package-source limits; deploy the fail-closed policy; then run isolation and negative-boundary validation | Approved environment record, policy/configuration reference, sanitized live boundary tests, monitoring evidence, and independent review |
| M10 | Browser operator and live preview — `blocked-by-provider` | No supported browser runtime with screenshot/DOM instrumentation and login-handoff controls | Select/configure a supported browser operator; define user takeover, approval, domain allowlist, session isolation, screenshot/DOM privacy, and audit controls; validate safe read-only workflows before any mutation | Adapter health/capability record, privacy/security review, bounded smoke evidence, and approved interaction contract |
| M11 | GitHub/GitLab synchronization and deployment — `blocked-by-credentials/provider` | Task combines source-control integration with an unselected or unauthorized deployment provider and release approval | Split the work into source-control and deployment-provider scopes. Repository synchronization is available in the present context; for deployment, select target provider, protected credential/workload-identity boundary, deployment environment, rollback target, monitoring, and change approval | Revised task graph, provider-specific preflight/dry-run, authorization evidence, redacted deployment/rollback evidence, and release approval |
| M12.18 | Blackbox developer-support confirmation assessment — `blocked-external` | Public documentation does not establish an official third-party OAuth/device flow; no support request is authorized | Preserve API-key-only/managed-first behavior. If the user explicitly authorizes external outreach, submit a narrowly scoped provider support request and record only the official response/reference. Otherwise retain blocked status. | Official provider documentation or written developer-support confirmation covering client registration, scopes, redirect/device semantics, tokens, rate limits, and redistribution |
| WT2-Cleanup | Remove obsolete dependencies, connectors, instructions, and artifacts — `blocked` | Destructive deletion requires explicit confirmation, named paths, and retention review | Prepare a read-only candidate inventory that identifies each path, owner, retention requirement, backup/evidence dependency, and deletion consequence. Obtain explicit path-by-path approval. Execute only an approved, reversible or recoverable deletion plan and validate no retained runtime data/log/evidence was removed. | Approved deletion list, retention and backup review, command/effect record, post-action validation, and changelog entry |

## 2. Dependency-gated production items

These records are not labeled `blocked`, but must be treated as unavailable for execution until their dependency gates pass.

| ID | Current status | Gate that prevents execution | Required next action |
|---|---|---|---|
| M13.15 | `infrastructure-dependent` | M13 security/canary foundation evidence, enterprise credentials, reviewed target provider, non-production rollback proof, and approval | Do not integrate a production provider until M14 readiness/recovery evidence and target-specific authorization exist |
| M14.8 | `in-progress-local` | Approved target, live M14.2–M14.7 evidence for scope, bounded policy, health sources, rollback target, and single-use approval | Complete the prepared change package and entry-gate record; then run the non-production drill under independent verification |
| M14.9 | `planned` | M14.1/M14.4 controls and accepted M14.8 evidence | Establish encrypted off-host backup and controlled restore evidence using the approved M14.9 plan |
| M14.10 | `planned` | M14.3, M14.8, and M14.9 evidence | Run integrated security, load, soak, dependency, observability, quota/cost, and rollback gates with sanitized evidence |
| M14.11 | `infrastructure-dependent` | M14.1–M14.10 completion and explicit operator approval | Start only the smallest approved production cohort with live monitoring, bounded hold, known rollback target, and incident route |

## 3. Resolution sequencing

The safe order is to resolve **environment and authority** prerequisites before any external mutation. First, identify the approved non-production environment, owners, change route, identity boundary, monitoring, and rollback authority. Second, complete M14.2–M14.4's live evidence gaps as applicable to the selected non-production scope. Third, execute and independently accept M14.8. Fourth, run M14.9 backup/restore controls, followed by M14.10's integrated readiness gates. M13.15 and M14.11 remain last because they involve real deployment-provider or production traffic decisions.

M9 may proceed in parallel with target-environment preparation when it supplies the approved execution boundary. M10 and M12 should remain independent of the production-readiness sequence unless their capabilities are explicitly required by a selected M14 evidence method. M12.18 is externally constrained and should not delay API-key-only or managed-first workflows that already comply with the documented boundary.

## 4. Approval and evidence controls

| Action type | Minimum authority | Required evidence before action | Prohibited shortcut |
|---|---|---|---|
| External deployment, traffic shift, pause, or rollback | Current scope-bound approval and rollback authority | Exact target, candidate, rollback target, cohort ceiling, idempotency/retry boundary, audit location, and recovery procedure | Treating dry-run output as execution approval |
| Browser or account operation | User-approved interaction scope and applicable account authorization | Domain/provider boundary, session/takeover control, operation preview, and safe audit plan | Reusing cookies, undocumented endpoints, or browser state as API authorization |
| Credential/provider integration | Approved protected secret or workload identity source | Scope, rotation/revocation path, non-secret configuration, and health/preflight record | Committing, logging, or inferring secret values |
| Destructive cleanup | Explicit named-path confirmation and retention owner | Candidate inventory, backup/evidence review, reversal/compensation plan, and post-action checks | Deleting directories or caches based on broad categories |
| Provider support outreach | Explicit authorization to post/send externally | Exact questions, recipient/provider, data classification, and response-retention plan | Submitting a support request without approval or including credentials |

## 5. Completion and tracker update rule

For every resolved blocker, retain a repository-safe evidence summary and a protected-system evidence reference when raw operational material is sensitive. Only then update `TODO.md`, `STATE.md`, and `TASK_GRAPH.md` to the same lifecycle meaning. If a prerequisite remains unavailable, keep the original blocked or infrastructure-dependent state and record the next permitted action rather than adding an optimistic completion claim.

## References

[1]: ../TASK_GRAPH.md "Current task graph"
[2]: M14_8_NONPRODUCTION_CHANGE_PACKAGE.md "Prepared M14.8 change package"
[3]: M14_8_NONPRODUCTION_CANARY_ROLLBACK_DRILL_RUNBOOK.md "M14.8 drill runbook"
[4]: M14_9_BACKUP_RECOVERY_EXECUTION_PLAN.md "M14.9 recovery execution plan"
[5]: FULL_REGRESSION_TRIAGE_2026-08-27.md "Full-regression triage"
