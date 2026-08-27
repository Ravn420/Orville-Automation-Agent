# Orville Deployment-Readiness and Technical-Debt Review

**Review revision:** `40144e420014b591f28d5c7f555076a927f414d3`
**Review date:** 2026-08-28
**Author:** **Manus AI**

## Executive assessment

The current checkout has **451 unchecked TODO items**, including 13 partially complete `[-]` milestones, and 541 checked items. The unchecked work is predominantly roadmap scope rather than an untracked defect in the core test suite. The full pytest suite passes **789 tests and 6 subtests** in 24.87 seconds, and `pip check` reports no broken requirements. The code scan found no genuine source `TODO`, `FIXME`, `XXX`, `HACK`, or `NotImplementedError` markers in the core and tools paths; the remaining `pass` statements are primarily intentional exception classes, protocol hooks, optional-import fallbacks, and no-op lifecycle methods.

The project is **not ready for unrestricted production deployment** solely on the basis of the local test pass. The default security release gate fails because the checkout does not have live sandbox-boundary evidence, required attestation verification evidence, or audit evidence. This is consistent with the project’s own deployment documentation, which describes the current API as a development/local bridge and requires hardened deployment infrastructure, identity, secret handling, and sandbox validation before production use [1] [2].

## Unchecked TODOs

| Priority | TODO area | Evidence found | Deployment implication | Recommended action |
|---|---|---|---|---|
| P0 | Live security and production execution gates | Unchecked or partial milestones cover production sandbox execution, worker IPC, attestation, trust-root ceremony, canary/rollback, tenant identity, backups, and production-readiness gates. | Production execution, multi-tenant exposure, and high-risk model workloads must remain disabled or deployment-owned. | Complete the live Windows/Linux sandbox validation, trust-root ceremony, attestation evidence, canary/rollback drill, tenant authorization, and disaster-recovery evidence before production promotion. |
| P0 | Tracked SQLite WAL/shared-memory cleanup decision | `TODO-570aaf580e3d` remains unchecked. The review found tracked and present paths `.orville/orville.db-wal`, `.orville/orville.db-shm`, `data/.orville/orville.db-wal`, and `data/.orville/orville.db-shm`. | These files may contain runtime state and should not be deleted or published without a retention, archive, or approved deletion decision. | Perform the documented inspection-only workflow: secret scan, exact-path manifest, retention rationale, backup/archive decision, and explicit operator approval. No destructive cleanup was performed in this review [3]. |
| P1 | Walkthrough-video retention and delivery evidence | `TODO-f8a70d13fc97` and `TODO-c5944ab8d2c5` remain unchecked. The roadmap narrative references a fallback MP4 outside the repository, but the current workspace does not retain the source or delivery metadata. | Release auditability and user-facing onboarding evidence are incomplete. | Retain the source or a reproducible fallback metadata record, validate its integrity, record delivery status, and then close the checklist item. |
| P1 | External provider and connector completeness | Multiple unchecked items require provider-specific network handlers, OAuth presets/refresh/revocation, real credential-free fixtures, connector pagination/retries, and credentialed integration coverage. | “Connector support” should not be interpreted as production support for every listed provider. | Mark each adapter as locally validated, configuration-required, or deployment-owned; add provider-specific contract tests before making operational claims. |
| P1 | Package and artifact supply-chain gates | Unchecked items cover package-path, archive-traversal, symlink, executable-content, dependency, and unsafe-command validation. | A passing application suite does not by itself establish package or artifact trust. | Run the supply-chain review against each release artifact, retain provenance and checksums, and make the review a release-gate input [4]. |
| P2 | Platform-specific release packaging | `TODO-d27ea90cef5c` requests rebuilding and validating the Windows executable and portable release. | The Python wheel and source distribution are validated, but the desktop/portable Windows deliverable is not equivalent to those artifacts. | Build and smoke-test the Windows executable and portable bundle on the target host, including Tkinter, extension inclusion, protected configuration, and upgrade/rollback behavior. |
| P2 | Operational resiliency and observability | Roadmap items remain for encrypted off-host backups, RTO/RPO, load/soak, quota/cost gates, observability, and rollback evidence. | The local release is not yet backed by a production operations envelope. | Define target SLOs, backup/restore evidence, alerting, retention, load/soak thresholds, and rollback ownership before deployment. |

## Source-level technical debt

The source scan found no live TODO/FIXME markers or explicit unimplemented exceptions in `orville_core`, `tools`, or `windows_gui.py`. The following items are still worth tracking as technical debt because they can affect deployment confidence even though they are not unfinished code markers.

| Finding | Severity | Why it matters | Recommended remediation |
|---|---|---|---|
| Security gate cannot pass by default | **Critical deployment gate** | `tools/release_gate.py --skip-tests` reports failed `sandbox_boundary`, `attestation_boundary`, and `audit_evidence` checks. | Treat the release as local/development-only until deployment evidence is supplied; then run the gate with the real, reviewed evidence flags. |
| Direct release-gate invocation is not self-contained | **Medium** | Running `python3 tools/release_gate.py --skip-tests` from the repository fails before the gate with `ModuleNotFoundError: No module named 'orville_core'`; adding `PYTHONPATH=.` makes the intended security result visible. | Make `tools` executable as a module, add a documented `python -m tools.release_gate` entry point, or bootstrap the repository root in the script. Add a CLI smoke test for the documented invocation. |
| Optional dependencies are skip-capable | **Medium** | API and relay tests use `skipIf`/`skipif` when FastAPI extras are absent. The base package declares no required dependencies, while `api`, `browser`, `media`, `security`, and `dev` are optional groups [5]. | Keep the base package minimal, but make release profiles explicit: install `orville-core[api,browser,security,dev]` for the complete readiness gate and fail the release if a required profile is silently skipped. |
| Test client dependency warning | **Low** | The full suite passes but emits one Starlette/httpx deprecation warning. | Update the test profile and compatibility pins according to the supported Starlette/httpx2 combination, then require a warning-free release run. |
| Desktop GUI runtime is host-dependent | **Medium for desktop deployments** | The portable helper split removes Tkinter from non-rendering tests, but `windows_gui.py` still requires Tkinter and a desktop-capable host. | Document and validate the Windows desktop runtime separately; include Tkinter availability and extension packaging in the portable release acceptance checklist. |
| Distribution scope is broader than the base install contract | **Medium** | The package has `dependencies = []`; API, browser, media, security, and development capabilities are optional. | Publish a profile matrix and installation commands with the release, and ensure the release gate validates the selected profile rather than only the base wheel. |
| Release evidence is distributed across ad hoc files | **Low/Medium** | Test logs, checksums, release notes, and artifact manifests exist, but a single machine-readable release manifest is not yet a universal gate input. | Create a signed or otherwise integrity-protected release manifest containing source revision, package hashes, test commands/results, dependency profile, platform, and known limitations. |

Several `pass` and `return None` locations are intentional: custom exception definitions, abstract/protocol hooks, optional-import fallbacks, and no-op termination methods. `CustomLocalAdapter` intentionally inherits the Ollama-compatible implementation without overriding behavior. These should not be converted into fake implementations merely to eliminate syntactic no-ops.

## Release-control results

| Check | Result | Interpretation |
|---|---|---|
| Unchecked TODO inventory | **451** | Significant roadmap and deployment work remains; not all items are release blockers for local use. |
| Full pytest suite | **789 passed, 6 subtests passed** | Core regression coverage is green at the reviewed revision. |
| Dependency consistency | **Passed** | `pip check` reports no broken requirements in the review environment. |
| TODO autopilot dry run | **Preview only** | The next queued item is the SQLite WAL/shared-memory retention decision; no changes were executed. |
| Default security release gate | **Failed** | Sandbox boundary, required attestation, and audit evidence are not available in this environment. |
| Destructive cleanup | **Not performed** | No WAL/SHM deletion, archive move, connector change, credential action, or Git-history rewrite was performed. |

## Recommended deployment decision

For a **local development or test deployment**, the release is suitable after installing the appropriate optional profile and preserving the identified runtime artifacts. The passing test suite and clean dependency check support that limited use.

For an **external production deployment**, the recommendation is **hold**. The security release gate is intentionally not green, live sandbox enforcement is host-dependent, production attestation and trust-root evidence are absent, and the remaining unchecked roadmap contains tenant authorization, backup/restore, canary, provider, and platform-release requirements. The correct next step is to complete the P0 evidence tasks rather than to delete runtime artifacts or mark the remaining TODOs complete based only on local tests.

## References

[1]: https://github.com/Ravn420/Orville-Automation-Agent/blob/main/docs/ai-agent-platform-setup.md "Orville AI agent platform setup and deployment boundaries"
[2]: https://github.com/Ravn420/Orville-Automation-Agent/blob/main/tools/release_gate.py "Orville local release gate"
[3]: https://github.com/Ravn420/Orville-Automation-Agent/blob/main/docs/WORKER_TASK_2_NAMED_PATH_DELETION_INVENTORY_AND_DRY_RUN.md "Named-path deletion inventory and dry-run procedure"
[4]: https://github.com/Ravn420/Orville-Automation-Agent/blob/main/docs/SUPPLY_CHAIN_REVIEW.md "Orville supply-chain review"
[5]: https://github.com/Ravn420/Orville-Automation-Agent/blob/main/pyproject.toml "Orville Core package metadata and optional dependencies"
