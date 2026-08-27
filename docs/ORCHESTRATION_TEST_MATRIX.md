# Orville Orchestration Test Matrix

## Purpose

This matrix defines the minimum repeatable validation surface for the orchestration control plane. It maps each critical behavior to deterministic tests, an owning specialist, an acceptance gate, and known external limitations. The matrix is executable outside Manus and uses local fixtures or synthetic data only.

## Matrix

| ID | Capability | Required scenarios | Primary test modules | Owner | Acceptance gate |
|---|---|---|---|---|---|
| ORCH-01 | Orchestration | Intake normalization, objective classification, ordered execution, checkpoint persistence, resume, and final integration | `tests/test_core_unit_contracts.py`, `tests/test_acceptance_workflows.py`, `tests/test_smoke_workflow.py` | Orchestration Agent | Valid graph executes in dependency order and persists resumable state |
| DELEG-01 | Delegation | Capability-based routing, specialist ownership, handoff schema, missing handler, and verification handoff | `tests/test_agent_contracts.py`, `tests/test_agent_runtime.py`, `tests/test_agent_modes.py` | Delegation Agent | Every runnable task has an eligible owner and structured handoff |
| GRAPH-01 | Graph dependencies | Unknown dependency, cycle, missing input, duplicate ownership, readiness, conditional release, and parallel-batch boundaries | `tests/test_core_unit_contracts.py`, `tests/test_workflow_state_handling.py` | Orchestration Agent | Invalid graphs fail before execution; eligible nodes release deterministically |
| RETRY-01 | Retries | Bounded retry count, retryable versus terminal error, idempotency key, backoff metadata, and resume after interruption | `tests/test_workflow.py`, `tests/test_workflow_dry_run.py`, `tests/test_workflow_state_handling.py` | Automation Agent | Retries are bounded, state-safe, and never duplicate a non-idempotent side effect |
| FAIL-01 | Failures | Handler exception, dependent-task blocking, cancellation, timeout, partial output, recovery action, and sanitized diagnostics | `tests/test_workflow_state_handling.py`, `tests/test_api_error_messages.py`, `tests/test_security_attack_surfaces.py` | Verification Agent | Failure state and dependents are explicit; diagnostics contain no secrets |
| APPR-01 | Approvals | Pending approval, rejection, exact task binding, sensitive-operation confirmation, expiry, and single-use receipt | `tests/test_approval_checkpoints.py`, `tests/test_destructive_action_confirmations.py`, `tests/test_confirmations.py` | Governance Agent | No sensitive operation executes without explicit, current, scope-matched approval |
| INT-01 | Integration | Authenticated API boundary, workflow dispatch, local connector bridge, artifact registration, and event/state consistency | `tests/test_api.py`, `tests/test_boundary_integrations.py`, `tests/test_shell_api.py` | Integration Agent | Boundary contracts agree on identifiers, states, errors, and redaction |
| SEC-01 | Safety integration | Prompt/untrusted-content handling, path traversal, unsafe commands, unauthorized action, secret leakage, and redaction | `tests/test_untrusted_content.py`, `tests/test_security.py`, `tests/test_security_hardening.py`, `tests/test_credential_redaction.py` | Security Agent | External instructions remain data and cannot authorize tools; prohibited actions fail closed |

## Execution profiles

| Profile | Command | Use |
|---|---|---|
| Focused matrix | `python -m unittest tests.test_orchestration_test_matrix -v` | Validate matrix completeness and referenced test modules |
| Behavioral subset | `python -m unittest tests.test_core_unit_contracts tests.test_agent_contracts tests.test_workflow tests.test_approval_checkpoints tests.test_api -v` | Exercise the principal local control-plane behaviors |
| Security subset | `python -m unittest tests.test_untrusted_content tests.test_security_attack_surfaces tests.test_credential_redaction -v` | Validate fail-closed and secret-safe boundaries |
| Compilation | `python -m compileall -q orville_core tests` | Detect syntax and import-source compilation errors |
| Full configured suite | `python tools/project_checks.py test` | Release gate; triage every failure before release |

## Test-data and environment policy

All matrix tests must use synthetic identifiers, deterministic clocks or fixtures where timing matters, local loopback endpoints, and temporary directories inside approved test roots. They must not load credentials, contact production services, post content, make purchases, alter accounts, or perform destructive repository operations. External provider, browser, deployment, and infrastructure behavior is recorded as a deployment-owned extension of the corresponding row rather than silently treated as locally verified.

## Entry and exit criteria

A matrix run may start only after the repository control files are present and the selected test modules are importable. The matrix passes when every row has at least one executable primary test module, the focused completeness test passes, the behavioral and security subsets pass, and every failure is triaged with severity, owner, reproduction, and disposition. Completion does not claim live provider authorization, production deployment, or external-account behavior.

## Maintenance

When a critical behavior changes, update the row, primary test module, acceptance gate, and focused completeness test in the same change. Retain the matrix as a release artifact and keep test names stable enough for triage automation.
