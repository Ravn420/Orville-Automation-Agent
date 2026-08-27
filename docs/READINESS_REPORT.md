# Orville Readiness Report

**Report date:** 2026-08-27  
**Scope:** Repository-local control plane, deterministic tests, documentation contracts, and supported deployment target boundaries.

## Executive status

Orville is **locally implementation-ready for continued development and controlled preview**. The repository contains a typed orchestration foundation, checkpointed execution, approval and untrusted-content boundaries, structured correlation logging, bounded operational reporting, deployment preflight and smoke checks, standalone examples, reusable task templates, and operator documentation. This report records local evidence only; it does not claim production readiness for external providers, accounts, browsers, hosted infrastructure, or live credentials.

## Current readiness checks

| Check | Status | Evidence | Scope and limitation |
|---|---|---|---|
| Source compilation | Pass | `python -m compileall -q orville_core tools tests examples` | Local Python source only |
| Focused contract tests | Pass | Recent focused suites for deployment, confirmations, untrusted content, logging, reports, README, examples, glossary, reusable fixes, and runbook | Does not replace the full regression gate |
| Full regression suite | Passed with non-blocking warning | Final three-increment remediation evidence: Python 3.12 compilation and `python3 -m pytest -q` completed with 788 passed, 1 warning, and 6 subtests passed. The warning is the existing Starlette/httpx deprecation notice. All results confirm the formerly reported `task_status` worker collection defect is resolved and `tests/test_orville_manus_worker.py` passes 10 focused tests. | Maintain the clean gate, monitor the upstream HTTP-client deprecation, and retain external/provider and artifact-retention limitations as explicit follow-up work. |
| API readiness contract | Conditional | `orville readiness`, `orville config`, and `orville health` | Requires a runtime token for authenticated API readiness; values must remain protected |
| Adapter readiness | Conditional | `ProductionReadiness.evaluate` checks required adapter/capability pairs | Requires explicitly configured adapters and health evidence |
| Deployment preflight | Pass for local contract | `tools/deployment_validation.py preflight --target <target>` | Live target infrastructure remains environment-owned |
| Deployment smoke | Conditional | Loopback HTTP smoke check for `/docs` on supported running targets | No remote checks without explicit target authorization |
| Security controls | Pass for local contracts | Confirmation gate, untrusted-content authorization boundary, secret-safe logging and reports | Provider and adapter integration must preserve the contracts |
| Operational evidence | Pass for local contract | Structured JSONL events and `tools/operational_report.py` | Hosted collection, retention, and alerting are deployment-owned |

## Readiness by target

| Target | Current classification | Required next gate |
|---|---|---|
| Sandbox | Ready for deterministic preview and contract smoke checks | Run target preflight and retain sanitized evidence |
| Attached desktop | Conditionally ready for local GUI and packaged checks | Verify workspace, process, packaging, and desktop-specific smoke path |
| Web hosting | Conditionally ready for reviewed deployment | Configure identity, secrets, TLS, log collection, health probes, and rollback |
| Persistent computing | Conditionally ready for controlled service deployment | Verify durable storage, process supervision, resource limits, backups, and recovery |

## Recent architecture and operations changes reflected

The report incorporates the current standalone task-template catalog, reusable-fixes catalog, canonical glossary, operator runbook, structured correlation logging, operational report generator, explicit sensitive-operation confirmation, untrusted-content execution blocking, deployment preflight and smoke validation, and standalone examples. These additions improve local repeatability and safety but do not substitute for environment-specific authorization or infrastructure evidence.

## Blocking findings and actions

The full regression release gate is clear after three remediation increments. `docs/REPOSITORY_AUDIT_2026-08-27.md` contains the authoritative audit record and `docs/FULL_REGRESSION_TRIAGE_2026-08-27.md` retains the local failure reproduction and correction workflow. The increments covered cross-platform credential persistence and hub-download path containment; deterministic visual baselines and platform-neutral reference resolution; and deterministic schema, timeout, sandbox, preview, research-fetch, GUI, and roadmap contracts. The final suite completed with 788 passed, 1 warning, and 6 subtests passed. The prior `task_status` worker-module collection finding is resolved and must not be treated as an active blocker. Cleanup of tracked runtime artifacts remains pending explicit confirmation, a named-path deletion list, and a retention review; provider-backed, deployment, and production evidence remain external.

Before any production claim, the operator must retain the clean full-suite evidence, validate target-specific preflight and smoke checks, confirm secret and approval controls, verify backups and rollback, and obtain environment-owner evidence for identity, provider, browser, infrastructure, monitoring, and recovery.

## Reproduction commands

```powershell
python tools\project_checks.py test
python tools\project_checks.py preview
python tools\deployment_validation.py preflight --target sandbox
python -m unittest tests.test_readiness -v
```

The commands above are local checks. Do not place credentials in commands, logs, screenshots, reports, or task state. Use protected runtime configuration and redact evidence.

## Report maintenance

Update this report whenever a material environment, architecture, deployment-target, security, or release-gate change occurs. Each update must identify the date, evidence, status, limitations, unresolved blockers, and next gate. Keep local readiness, conditional target readiness, and production readiness explicitly distinct.
