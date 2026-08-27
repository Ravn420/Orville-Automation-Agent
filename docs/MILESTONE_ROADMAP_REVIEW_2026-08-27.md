# Orville Milestone Roadmap Review

**Review date:** 2026-08-27  
**Review type:** Equivalent milestone review  
**Scope:** Durable repository state, task graph, completed-local checkpoints, readiness evidence, and remaining roadmap items.

## Review outcome

The current milestone has established a substantial standalone control-plane foundation. Recent work covers task intake and templates, orchestration and graph validation, approvals and untrusted-content boundaries, structured logs and operational reports, deployment preflight and smoke checks, standalone examples, operator recovery procedures, and canonical project terminology. The milestone is **locally evidence-bearing but not production-ready** because live provider, identity, browser, infrastructure, and hosted-observability gates remain environment-owned. The three-increment regression remediation is complete: Python 3.12 compilation and the full suite completed with 788 passed, 1 warning, and 6 subtests passed. The formerly reported `task_status` worker collection defect is resolved; its focused suite now passes.

## Progress summary

| Area | Evidence reviewed | Status | Follow-up |
|---|---|---|---|
| Core orchestration | Task graph, checkpoints, state transitions, delegation, retries, failure handling | Completed-local | Maintain regression coverage and deterministic release evidence |
| Safety and governance | Confirmation gate, untrusted-content boundary, secret rules, incident/recovery runbook | Completed-local | Integrate all external adapters with the fail-closed contracts |
| Observability | Structured correlation logging, operational report, phase metrics, dashboards/report guidance | Completed-local | Add deployment-owned retention, alerting, and SLO collection |
| Standalone operation | README, examples, templates, reusable-fixes catalog, glossary, operator runbook | Completed-local | Keep contracts synchronized as interfaces change |
| Deployment | Target selection, preflight, loopback smoke checks, rollback and recovery guidance | Conditional | Validate each real target with authorized infrastructure evidence |
| GUI and API | GUI architecture, responsive/accessibility guidance, API contracts and local readiness | Conditional | Complete integration, packaging, and environment-specific smoke gates |

## Priority review

| Priority | Next work | Impact | Dependencies | Risk |
|---|---|---|---|---|
| P0 | Maintain the restored full regression release gate | Preserves the release feedback loop | `TODO.md` audit queue and CI/local evidence | Low locally; external deployment and provider gates remain high-risk |
| P0 | Preserve approval, secret, untrusted-content, and path-safety gates during adapter integration | Prevents unauthorized or unsafe side effects | Adapter contracts and integration tests | High if bypassed; the first increment provides portable encrypted connector records and mixed-separator model-download path containment, while the second restores a reviewed visual baseline and portable reference checks |
| P1 | Resolve the cleanup item with explicit confirmation and a named-path retention review | Reduces obsolete material without deleting retained evidence | Approval and path-by-path inventory | High if broad deletion is attempted |
| P1 | Complete deployment-owned identity, secret management, TLS, monitoring, backup, and rollback evidence | Enables controlled hosted or persistent deployment | Environment owner and authorized infrastructure | High and environment-specific |
| P2 | Add coverage measurement and expand integration/GUI smoke evidence | Quantifies untested paths and improves release confidence | Working test collection and coverage tooling | Medium |
| P2 | Continue roadmap maintenance and update this review after material changes | Keeps priorities and assumptions current | Durable state and task graph | Medium |

## Decisions and scope changes

The project remains standalone-capable and local-first. Manus-specific services, external providers, browser sessions, hosted identity, production deployment, and centralized monitoring are optional integrations rather than core prerequisites. Local tests and reports must not be interpreted as live authorization or production health. Cleanup is not authorized by this review; it remains blocked until the repository’s explicit-confirmation rule is satisfied.

## Acceptance gates for the next milestone

1. The full configured suite runs to completion with no untriaged failures; final evidence records 788 passed, 1 warning, and 6 subtests passed, and the prior worker collection issue is resolved.
2. Coverage measurement is available, or its absence is documented as a release limitation with a concrete installation and collection plan.
3. Each supported deployment target has preflight, smoke, rollback, and recovery evidence appropriate to that environment.
4. External adapters preserve confirmation, secret handling, untrusted-content, path containment, and bounded retry contracts.
5. Production claims are withheld until identity, authorization, credential storage, observability, backup, recovery, and independent review evidence exists.

## Review maintenance

Run an equivalent milestone review at least quarterly and immediately after a material architecture, environment, security, deployment, or release-gate change. Update this document with date, evidence, decisions, priorities, dependencies, risks, and acceptance gates. Keep unresolved blockers visible rather than treating them as completed work.
