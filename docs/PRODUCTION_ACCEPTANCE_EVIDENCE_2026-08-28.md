# Production Acceptance Evidence — 2026-08-28

**Task:** `TODO-9d23783f4060`  
**Repository:** Orville Automation Agent  
**Branch reviewed:** `feature/final-operational-pass`  
**Review mode:** Local, credential-free, non-destructive validation only  
**Decision:** **Not production-approved**; local acceptance evidence is retained with two unrelated baseline failures and deployment-owned gates explicitly unresolved.

## Reproducible command

From the repository root:

```text
python -m pytest -q tests/test_acceptance_workflows.py tests/test_accessibility_acceptance.py tests/test_live_status_accessibility.py tests/test_performance_boundaries.py tests/test_coding_evaluation.py tests/test_standalone_release.py tests/test_deployment_commands.py tests/test_deployment_targets.py tests/test_deployment_validation.py tests/test_rollback_recovery.py tests/test_recovery_controls.py tests/test_security_hardening.py tests/test_security_attack_surfaces.py tests/test_provider_mcp_security.py
```

Observed result on 2026-08-28: **51 passed, 2 failed** in 11.86 seconds. The failures are pre-existing Windows-path representation assertions in `tests/test_performance_boundaries.py` and `tests/test_security_hardening.py` (`C:\model` versus expected `C:/model`). No production deployment, external identity provider, live TLS certificate, deployment secret, CORS origin, audit sink, browser session, provider, or external network was used.

## Acceptance matrix

| Area | Local evidence | Result | Boundary or follow-up |
|---|---|---|---|
| Production acceptance workflows | `tests/test_acceptance_workflows.py` | Passed in grouped run | Live production smoke and authenticated health remain deployment-owned. |
| Security | `tests/test_security_attack_surfaces.py`, `tests/test_provider_mcp_security.py`, `tests/test_security_hardening.py` | Security group passed except the unrelated path assertion | Production IdP, secret manager, TLS, CORS, and audit sink require deployment approval. |
| Accessibility | `tests/test_accessibility_acceptance.py`, `tests/test_live_status_accessibility.py` | Passed in grouped run | Live screen-reader, browser, and platform review remain required. |
| Performance | `tests/test_performance_boundaries.py` | One unrelated Windows-path failure | Re-run after path-normalization baseline is triaged; no performance claim is made from a failing gate. |
| Repository coding evaluation | `tests/test_coding_evaluation.py` | Passed in grouped run | Environment parity and dependency provenance remain limitations. |
| Packaging and standalone release | `tests/test_standalone_release.py` | Passed in grouped run | Actual signed artifact publication remains intentionally unperformed. |
| Deployment | `tests/test_deployment_commands.py`, `tests/test_deployment_targets.py`, `tests/test_deployment_validation.py` | Passed in grouped run | No deployment target was changed or contacted. |
| Rollback and disaster recovery | `tests/test_rollback_recovery.py`, `tests/test_recovery_controls.py` | Passed in grouped run | Live backup restore, monitoring, and operator approval remain deployment-owned. |

## Release decision

The evidence supports a **local validation checkpoint**, not a production-acceptance approval. The two baseline failures must be triaged and resolved or explicitly waived by the release owner. Before production approval, the deployment owner must additionally provide evidence for the production identity provider, scoped authorization matrix, TLS configuration, secret references and rotation, CORS allowlist, audit-log sink durability, signed package/artifact provenance, live health checks, rollback rehearsal, verified backup restore, and disaster-recovery objectives.

No credentials, private keys, bearer tokens, personal data, external account changes, uploads, purchases, deployments, or destructive recovery actions were performed.
