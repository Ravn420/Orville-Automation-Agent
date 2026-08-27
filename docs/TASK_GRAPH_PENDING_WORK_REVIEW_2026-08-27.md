# TASK_GRAPH Pending-Work Review

**Review date:** 2026-08-27
**Scope:** All explicit non-completed, blocked, partial, planned, or regression-blocked records in `TASK_GRAPH.md` on `origin/main`
**Review purpose:** Confirm the M14.8 and M14.9 materials, identify every remaining tracked work item, and establish a safe, dependency-led execution order.
**Overall conclusion:** Orville is locally implementation-ready for continued development and controlled preview, but it is **not production ready**. The remaining work is concentrated in live infrastructure, identity, deployment, recovery, browser operation, and independently retained evidence.

> Local contracts, fixtures, dry runs, and synthetic tests are not substitutes for live-environment evidence. A task remains incomplete whenever its stated environment, authority, credential, provider, or independent verification gate is absent.

## 1. M14.8 and M14.9 material verification

The required M14.8 runbook and per-run acceptance-evidence template are present on `origin/main`. They define entry gates, roles, bounded promotion, restart recovery, duplicate-event idempotency, partial/injected fault handling, rollback success/failure recovery, redaction, and independent acceptance. The M14.9 plan is also present and sets out the backup/recovery execution sequence.

| Material | Current status | Purpose |
|---|---|---|
| [`M14_8_NONPRODUCTION_CANARY_ROLLBACK_DRILL_RUNBOOK.md`](M14_8_NONPRODUCTION_CANARY_ROLLBACK_DRILL_RUNBOOK.md) | Present | Controlled non-production canary and rollback procedure |
| [`M14_8_CANARY_ROLLBACK_ACCEPTANCE_EVIDENCE_TEMPLATE.md`](../artifacts/templates/M14_8_CANARY_ROLLBACK_ACCEPTANCE_EVIDENCE_TEMPLATE.md) | Present | Sanitized, independently reviewed evidence record for each drill |
| [`M14_9_BACKUP_RECOVERY_EXECUTION_PLAN.md`](M14_9_BACKUP_RECOVERY_EXECUTION_PLAN.md) | Present | Execution controls, owners, evidence, and completion gates for backup/recovery |

M14.8 remains correctly `in-progress-local`: the documentation and synthetic baseline exist, but approved non-production execution and independent acceptance are still required. M14.9 remains planned and is constrained by the task graph's stricter requirement for accepted M14.8 evidence.

## 2. Pending-work inventory

The task graph contains **15 explicit non-completed milestone records**, plus one destructive-cleanup blocker and three local-completion records whose release evidence is qualified by a known regression-collection defect. The following inventory excludes individual limitation notes attached to already-completed local contracts; those notes are consolidated in Section 4.

| ID | Work item | Status | Owner | Direct dependency or blocker | Required next outcome |
|---|---|---|---|---|---|
| M9 | Hardened execution infrastructure | blocked-by-infrastructure | Automation and Security | Non-root container/VM, resource quotas, network/package policy | Approve and validate a hardened execution environment |
| M10 | Browser operator and live preview | blocked-by-provider | Prototype | Browser runtime, screenshot/DOM instrumentation, login handoff controls | Select/configure supported browser runtime and validate safe operator boundaries |
| M11 | GitHub/GitLab synchronization and deployment | blocked-by-credentials/provider | IDE and Deployment | Remote provider, deployment provider, release approval | Split source-control integration from deployment; retain provider and approval gates |
| M12 | Persistent GUI, collaboration, notifications, RAG, multimedia, telemetry | partially specified | IDE and Research | GUI runtime, storage/search, connectors, observability backend | Decompose into individually scoped, approved milestone tasks |
| M12.8 | Process sandboxing and cryptographic attestation | partially-complete-local | Security and Verification | Production trust-root ceremony, Linux live execution, GPU isolation | Obtain live supported-host and operator evidence without weakening fail-closed behavior |
| M12.18 | Blackbox developer-support confirmation assessment | blocked-external | Research and Governance | Official provider correspondence under an authorized external-action scope | Retain blocked state until an authorized, documented provider path exists |
| M13.4 | Sandbox execution integration | partially-complete-local | Code Synthesis and IDE | M13.2/M13.3; production-path routing, guest completion, Linux live IPC | Produce live host evidence for the remaining execution path |
| M13.15 | Production deployment integration | infrastructure-dependent | Automation | M13.7, M13.9–M13.14, enterprise credentials | Integrate only after all non-production, recovery, credential, and approval gates pass |
| M14.2 | Production trust-root ceremony | partially-complete-local | Security | Approved root material, out-of-band digest, operator approval, rotation/revocation drill | Complete and independently verify the operator ceremony |
| M14.3 | Live Windows/Linux sandbox validation | partially-complete-local | Security and Verification | Supported hosts with Windows Sandbox/WSL and Linux bubblewrap; GPU where in scope | Retain live IPC, boundary, cleanup, and resource-limit evidence |
| M14.4 | Enterprise identity and authorization | partially-complete-local | Security and IDE | Approved identity provider, live tenant testing, MFA/revocation evidence | Validate production gateway, least privilege, and isolation |
| M14.8 | Non-production canary and rollback drill | in-progress-local | Automation and Verification | M14.2–M14.7 and approved non-production target | Execute the runbook and obtain independent acceptance evidence |
| M14.9 | Backup, restore, and disaster recovery | planned | Automation and Security | M14.1, M14.4, and accepted M14.8 evidence | Establish/verify encrypted off-host backup and recovery controls |
| M14.10 | Production readiness and load gates | planned | Verification | M14.3, M14.8, M14.9 | Run complete security, load, soak, observability, quota/cost, and rollback gates |
| M14.11 | Controlled production canary | infrastructure-dependent | Automation | M14.1–M14.10 plus explicit approval | Launch only the smallest approved cohort under live monitoring |

### Additional tracked blockers and release qualifications

| Record | Status | Why it matters | Required disposition |
|---|---|---|---|
| Obsolete dependency/connector/instruction/artifact cleanup | blocked | Deletion is destructive; a named-path list and retention review are required | Obtain explicit scoped approval before any removal |
| Automated build/test/preview procedures | completed-local-with-regression-blocker | Focused checks pass, but the full regression collection is not clean | Fix and triage the `task_status` default-binding collection defect; rerun full suite |
| Artifact storage and lifecycle controls | completed-local-with-regression-blocker | Focused checks pass; full regression retains three unrelated connector/shell API failures | Triage those failures before a release claim |
| Standalone release workflows | completed-local-with-regression-blocker | Local validation passes; full suite retains the same three unrelated failures | Resolve/waive with evidence before production gating |

## 3. Dependency assessment and execution order

The task graph establishes a clear production-critical sequence. M14.8 cannot be accepted until M14.2–M14.7 are sufficiently evidenced for the approved non-production scope. M14.10 depends on M14.3, M14.8, and M14.9; M14.11 then depends on every preceding M14 task and explicit approval. M13.15 remains intentionally later than the M13 security/canary foundations and must not bypass M14 recovery and readiness gates.

| Order | Workstream | Rationale and completion gate |
|---:|---|---|
| 0 | Regression and documentation hygiene | Correct or independently disposition the full regression collection defect. Preserve the verified M14.8/M14.9 materials and keep tracker states aligned. |
| 1 | Environment/authority readiness | Name the enterprise environment owner, rollback authority, security reviewer, recovery owner, change process, target non-production environment, and incident route. This is required before live evidence work. |
| 2 | M14.2, M14.3, M14.4 in controlled parallel | These are distinct live-environment gaps: trust root, sandbox hosts, and identity gateway. Each needs target-specific approval and evidence. Do not treat local contracts as completed production integration. |
| 3 | M14.8 | Run the approved non-production canary and rollback drill using the existing runbook and template. The independent reviewer must verify controller state, adapter actions, health evidence, idempotency, rollback, and redaction. |
| 4 | M14.9 | Establish encrypted off-host backups and complete a controlled non-production restore drill only after M14.8 has accepted evidence. |
| 5 | M14.10 | Run the integrated production-readiness gates with sanitized evidence after M14.3/M14.8/M14.9 complete. |
| 6 | M13.15 and M14.11 | Select/integrate the reviewed provider and conduct the smallest controlled production canary only with all gates, credentials, monitoring, rollback target, and explicit operator approval in place. |
| Deferred / separate | M9, M10, M11, M12, M12.18, cleanup | These require infrastructure, provider, scope decomposition, official documentation, or deletion approval. They should not be silently folded into M14 delivery. |

### Immediate executable work

The next work that can be prepared without live production side effects is the M14.8 change package: schedule the non-production window; complete the runbook's entry gates; record immutable candidate/rollback identifiers and policy version; validate the reviewed adapter in dry-run/preflight mode; and open the evidence record. If any M14.2–M14.4 live requirement is unavailable, record M14.8 as blocked for that target rather than widening permissions or using production resources.

## 4. Consolidated residual limitations

Several completed local contracts retain explicit follow-up gates. They do not create new approved roadmap tasks by themselves, but must be accounted for in scheduling and acceptance.

| Domain | Residual limitation | Planning implication |
|---|---|---|
| Sandbox and model execution | Linux live bubblewrap execution, GPU isolation, production-path worker IPC, and automated guest-completion evidence remain incomplete | A supported host and target-specific test plan are prerequisites for M14.3/M13.4 closure |
| Trust and identity | Production trust-root material, operator ceremony, live OIDC/SAML gateway, MFA, issuer/audience validation, and revocation propagation remain external | M14.2/M14.4 cannot close on source-level evidence alone |
| Deployment and monitoring | Provider-specific deployment adapter, workload identity, durable provider audit persistence, monitoring backend, alerting/SLO policy, and business-health source are environment-owned | M14.8/M14.10 require explicit provider and monitoring evidence |
| Recovery | Backup/restore operations, off-host retention, live recovery timing, access review, and disaster-recovery exercise are not complete | M14.9 must retain proof of recoverability, not only backup creation |
| Browser, GUI, and collaboration | Live browser operator, screenshot/DOM instrumentation, accessible rendered behavior, durable search/RAG, notifications, collaboration UI, and observability export are not fully implemented | Decompose M12 before implementation; avoid an undifferentiated scope increase during M14 |
| Provider account connection | Official Blackbox OAuth/device semantics remain undocumented and external | Preserve API-key-only/managed-first boundary; do not infer a sign-in flow or scrape browser sessions |

## 5. M14.9 execution outline

The M14.9 plan is complete as a planning artifact. Its execution is divided into the following ordered controls:

1. **Scope and ownership:** inventory every recoverable asset; assign data class, owner, RTO, RPO, backup cadence, retention, and restore priority.
2. **Approved architecture:** choose an encrypted, off-host, access-controlled backup target; document key-management responsibility, immutability/deletion safeguards, and non-secret logging.
3. **Auditable backups:** implement bounded, idempotent backups with stable identifiers, source boundaries, checksums, encryption/key references, capacity checks, and failure alerts.
4. **Integrity and retention:** prove each recovery point exists, matches its recorded checksum/immutable identifier, is retrievable by an authorized recovery role, and retains the approved policy.
5. **Non-production restoration:** restore an isolated copy under explicit approval; verify integrity, authenticated health, read-only state/checkpoint, and a representative smoke workflow; measure actual RTO/RPO.
6. **Failure exercise:** safely test an inaccessible or invalid recovery point, failed validation, or capacity/access exception; preserve the known-good backup and prove fail-closed escalation.
7. **Access/runbook review:** independently review least-privilege access for create/read/restore/delete/key use and approve the recovery procedure.
8. **Acceptance:** retain the sanitized evidence index and reviewer decision. M14.9 remains incomplete until every required control is evidenced.

## 6. Findings requiring a roadmap decision

The review identifies two governance items that should be resolved in a subsequent approved roadmap update.

First, M11 is labeled `blocked-by-credentials/provider`, but this review verified repository synchronization to GitHub on `origin/main`. That status should be split into **source-control synchronization**, which is available in the current repository context, and **deployment-provider integration**, which still needs target provider configuration, credentials, and release approval. The status should not be changed solely on this review; a task-graph revision should name the exact remaining M11 scope and acceptance evidence.

Second, M12 is a broad, partially specified umbrella covering persistent GUI, collaboration, notifications, RAG, multimedia, and telemetry. It should be decomposed into independent approved tasks with owners, dependencies, safety boundaries, acceptance tests, and evidence. This prevents M12 scope from obscuring production-critical M14 gates.

## 7. Review validation

| Validation | Result |
|---|---|
| Current remote branch checked | `main` is synchronized with `origin/main` during this review |
| M14.8 drill runbook present | Verified |
| M14.8 acceptance-evidence template present | Verified |
| M14.9 backup/recovery plan present | Verified |
| Explicit non-completed milestone rows inventoried | 15 rows |
| Cleanup blocker and regression-qualified local completions reviewed | Verified |
| Status alignment of M14.8 referenced | `[-]` in `TODO.md`; `in-progress-local` in `STATE.md` and `TASK_GRAPH.md` |
| External or destructive actions performed | None |

## References

[1]: ../TASK_GRAPH.md "Orville task graph"
[2]: ../STATE.md "Orville project state"
[3]: M14_8_NONPRODUCTION_CANARY_ROLLBACK_DRILL_RUNBOOK.md "M14.8 drill runbook"
[4]: ../artifacts/templates/M14_8_CANARY_ROLLBACK_ACCEPTANCE_EVIDENCE_TEMPLATE.md "M14.8 acceptance-evidence template"
[5]: M14_9_BACKUP_RECOVERY_EXECUTION_PLAN.md "M14.9 backup and recovery execution plan"
[6]: M14_PRODUCTION_TRUST_ROOT_CEREMONY.md "M14.2 ceremony procedure"
[7]: M14_ENTERPRISE_IDENTITY.md "M14.4 identity boundary"
[8]: READINESS_REPORT.md "Repository readiness report"
[9]: PRIORITIZED_BACKLOG.md "Prioritization method"
