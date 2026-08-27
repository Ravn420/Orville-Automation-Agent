# Orville Repository Audit — 2026-08-27

**Audit scope:** Complete tracked repository review, including Python source, tests, configuration, documentation, roadmap state, package metadata, generated-artifact references, and documented local quality checks.

## Executive assessment

Orville retains a substantial local control-plane implementation, but it is **not release-ready**. The full regression gate completes collection only after the standard GUI runtime is available and then reports **760 passed and 20 failed tests** after the checklist reconciliation in this audit. The source compiles successfully, the base package wheel builds successfully, and the credential-free preview check passes, but the preview check reports three existing normal-text contrast warnings. The previous worker-module collection diagnosis is now obsolete: the focused roadmap-worker suite passes all 10 tests. The current blocker is therefore a post-collection regression cluster, not the former `task_status` collection error.[1] [2] [3]

> This audit distinguishes verified local behavior from environment- or provider-dependent work. It does not claim that local contracts establish production deployment readiness.

| Verification activity | Observed result | Audit interpretation |
|---|---:|---|
| Python compilation | Passed | No syntax or compilation defect was observed in the audited Python paths. |
| Base wheel build without dependencies | Passed | The distributable base package can be built. |
| Full regression suite | 760 passed, 20 failed, 1 warning | **Release gate blocked.** Failures are grouped below. |
| Clean `.[dev]` install and collection | 6 collection errors | Development extras omit API test dependencies required by six test modules. |
| Credential-free preview check | Passed with 3 contrast warnings | Static preview remains usable; accessibility remediation is still required. |
| Roadmap-worker focused suite | 10 passed | The former worker collection blocker is resolved; its documentation is stale. |
| Data-acquisition template focused suite | 3 passed | The formerly in-progress template task was already delivered and is reconciled in `TODO.md`. |

## Confirmed remediation queue

The following tasks are the authoritative queue created by this audit. They are intentionally ordered before legacy unchecked entries in `TODO.md`; each must retain its security, approval, and secret-redaction boundaries while being resolved.

| Priority | ID | Verified finding | Required completion evidence |
|---|---|---|---|
| P0 | `TODO-cff928829702` | The full suite has 20 reproducible failures after successful collection. | A clean full-suite run, per-failure triage, and updated release evidence. |
| P0 | `TODO-54d8ec6f80b9` | Manual connector and Blackbox API-key persistence unconditionally require Windows DPAPI, while documented Linux/macOS installation and tests exercise these routes. | A reviewed portable secure-storage approach, or explicit OS-specific skips/unsupported responses with tests and documentation. |
| P0 | `TODO-25105284c9fc` | The visual-regression checker unconditionally requires `artifacts/visual_regression_baseline.json`, but the baseline is absent. | A reviewed committed baseline and passing visual-regression tests. |
| P1 | `TODO-f7347e19331a` | Five documentation-contract tests replace `/` with `\\` before resolving paths, causing false failures on POSIX hosts. | Platform-neutral path resolution with focused test coverage. |
| P1 | `TODO-f83deb76611e` | The TODO-ID utility adds a second marker whenever prose follows an existing marker, and several legacy rows duplicate newer completion records. | Idempotent marker parsing, a passing identifier test, and reconciled checkpoint/template records. |
| P1 | `TODO-1f336418c5a4` | Test expectations are stale or timing-sensitive around checkpoint schema version, timeout event position, and preview-server startup readiness. | Stable behavior-or-contract decisions, focused tests, and no order/timing dependence. |
| P1 | `TODO-3d2f46e3bd16` | The hub-download API test reports an unexpected status response; an earlier full run also left a non-empty temporary directory during cleanup. | A deterministic response contract and leak-free temporary-resource cleanup. |
| P1 | `TODO-ac288c7cbdfb` | `STATE.md`, readiness reporting, and the milestone review still name the resolved worker collection issue and old pass counts as current. | Current test baseline, active blockers, and next gates synchronized across control documents. |
| P1 | `TODO-570aaf580e3d` | SQLite WAL/shared-memory files are tracked beneath `.orville/` despite the repository’s stated separation of runtime state from source control. | A named-path retention/removal decision, secret scan, and explicit approval before any deletion. |
| P2 | `TODO-f8a70d13fc97` | The walkthrough status refers to a video outside the repository, but neither the source video nor retained validation/delivery metadata is present in the current workspace. | Retained source/evidence or an explicit archival/availability limitation before closing the video checklist. |

## Existing incomplete work retained

The roadmap already records environment-dependent work such as production trust-root ceremony execution, live Windows/Linux sandbox enforcement, non-production canary evidence, backup/recovery operations, load gates, and a controlled production canary. These tasks remain incomplete and were not represented as locally completed by this audit.[4] [5]

The audit also confirms that the existing static Signal Room checker reports normal-text contrast warnings. That work is already represented by the GUI accessibility and release-gate backlog and is not duplicated in the new queue.[6]

## Control-file reconciliation

The data-acquisition record is complete locally. `docs/DATA_ACQUISITION_RECORD_TEMPLATE.md` supplies the requested reproducible acquisition structure, and its focused tests pass; the corresponding `TODO.md` entry is changed from in progress to complete. The standard execution-record template is clarified as a **reusable execution-record** and its task-ID markers are moved to line endings so the current identifier tool can recognize them without generating duplicate IDs. This wording/layout correction does not turn template placeholders into actionable work.[7] [8]

The walkthrough checklist is not closed. Its narrative says a fallback video was rendered, but the current repository/workspace does not retain the referenced artifact or delivery evidence. The new retention task is therefore the only status change for that area.[8]

## Explicit limitations

This review did not use live provider credentials, submit external requests, deploy infrastructure, delete repository data, or change third-party accounts. All external-provider, hosting, identity, backup, and production-canary claims remain bounded by the existing roadmap and must be validated in their approved target environments.[4] [5]

## References

[1]: ../pyproject.toml "Package and test configuration"
[2]: ../tools/project_checks.py "Documented aggregate quality check"
[3]: ../tools/orville_manus_worker.py "Persistent roadmap worker"
[4]: ../STATE.md "Current project execution state"
[5]: ../TASK_GRAPH.md "Roadmap task graph and milestones"
[6]: ../tools/signal_room_checks.py "Credential-free Signal Room smoke and accessibility check"
[7]: DATA_ACQUISITION_RECORD_TEMPLATE.md "Reproducible data-acquisition record template"
[8]: ../TODO.md "Authoritative roadmap and checklist"
