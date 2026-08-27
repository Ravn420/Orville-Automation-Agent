# Full-Regression Triage and Disposition

**Review date:** 2026-08-27
**Scope:** Current repository checkout after the M14.8 preparation updates
**Test command:** `python3 -m pytest -q`
**Disposition:** The previously reported `task_status` default-binding collection defect is **not reproducible in the current source**. The full regression gate remains **failed**, but for a different set of current environment, contract, fixture, and documentation failures described below.

> Do not change production readiness, M14.8 completion, or deployment state based on this triage. A green focused worker suite and successful test collection do not substitute for a green full regression run.

## 1. Reproduction record

| Step | Result | Evidence |
|---|---|---|
| Initial targeted worker collection | Blocked by missing `pytest` in the sandbox Python environment | `python -m pytest` reported `No module named pytest` |
| Test-runner installation | Completed locally | `pytest` was installed as the declared development test runner |
| Targeted worker collection | Passed | 10 tests collected from `tests/test_orville_manus_worker.py` |
| Initial full-suite collection | Blocked by missing Linux `tkinter` package | Five GUI test modules could not import `tkinter` |
| GUI dependency installation | Completed locally | `python3-tk` installed in the sandbox test environment |
| Current full-suite execution | Failed after complete collection | 758 passed, 22 failed, 1 warning, and 6 subtests passed |
| Source search for `task_status` | No current worker/test source reference found | The only repository match is a stale planning statement in `docs/MILESTONE_ROADMAP_REVIEW_2026-08-27.md` |

The focused worker module now collects and passes all ten of its tests. Therefore, the prior `task_status` default-binding report should be treated as **stale historical triage**, not a change request against `tools/orville_manus_worker.py`.

## 2. Formal disposition of the reported collection defect

| Item | Decision | Rationale | Required documentation action |
|---|---|---|---|
| `task_status` default-binding collection report | Dispositioned as stale/not reproducible | Targeted collection and execution pass; current source search finds no matching worker/test binding | Replace references that claim this is the active full-suite blocker with the current failure ledger |
| Missing `pytest` test runner | Environment prerequisite satisfied in this sandbox | The repository declares `pytest` under development dependencies but the base test environment did not contain it | Keep setup instructions explicit for test environments |
| Missing Linux `tkinter` package | Environment prerequisite discovered | GUI tests import `windows_gui.py`; on this Ubuntu runner, `python3-tk` was needed for collection | Document Linux GUI-test prerequisite or isolate GUI tests in an approved platform-specific test profile |
| Full regression gate | Remains failed | Collection now completes, but 22 tests fail | Triage and correct/disposition every failure before any release-gate claim |

## 3. Current failure ledger

The failures are grouped by observed symptom. These are investigation starting points, not assertions of root cause; every correction must begin with the named focused test and preserve the existing security, approval, and redaction boundaries.

| Priority | Failure group | Affected tests | Observed symptom | Corrective/disposition procedure |
|---|---|---|---|---|
| P0 | Provider/connector contract regression | `test_cloud_relay_api` (2), `test_connector_connections` (2), `test_media_api` | Expected success responses return `400`, or protected connection support is unavailable | Run each test in isolation; compare fixture configuration and API/connector validation contracts; make a minimal, secret-safe compatibility correction or revise an obsolete expectation with explicit rationale and reviewer sign-off |
| P0 | Security hardening input contract | `test_security_hardening` (2) | Tests provide a path rejected by stricter absolute-path validation | Determine whether the test fixture violates the documented safety boundary. Keep strict validation if correct; otherwise normalize only approved test/runtime paths and add a regression test for the intended boundary |
| P0 | Orchestration/runtime reliability | `test_orchestration` (2), `test_preview_runtime` (1), `test_execution_monitor` (1) | Checkpoint/timeout assertions fail, preview connection is refused, or safe monitor copy differs from expected contract | Reproduce one test at a time; inspect timing/resource isolation; repair deterministic state persistence or readiness synchronization; update only intentional message-contract changes |
| P0 | Missing baseline artifacts | `test_visual_regression` (2) | `artifacts/visual_regression_baseline.json` is absent | Restore or regenerate the versioned baseline through an approved visual-review process; record its provenance and ensure the test fails closed on unexpected changes |
| P1 | Required documentation or test references absent | `test_operator_runbook`, `test_orchestration_test_matrix`, `test_readiness_report`, `test_reusable_fixes`, `test_standalone_readme` | Referenced files or test modules do not exist | Decide for each reference whether the missing target must be created, renamed, or removed as obsolete. Update both link and validation test together; do not fabricate evidence files |
| P1 | Template/roadmap contract drift | `test_execution_record_template`, `test_roadmap_phase_increments`, `test_todo_identifiers` | Template wording, roadmap mapping evidence, or deterministic TODO identifiers differ from assertions | Treat templates and identifiers as compatibility contracts; restore expected stable text/ID generation or intentionally revise schema, migration evidence, and focused tests together |
| P1 | Shell/API contract drift | `test_shell_api` | Safe response text differs from the expected allowed-operations contract | Compare the test with current redaction/allowlist policy. Make the smallest change that preserves safe operation boundaries and document any intentional API contract update |

## 4. Correction workflow

Execute the following loop for each failure group. Do not batch unrelated changes because the full suite is already broad and contains safety-critical contracts.

1. **Claim the focused defect.** Record the exact test name, owner, expected behavior, observed behavior, target module, and acceptance test. Do not start by weakening assertions or skipping the test.
2. **Reproduce in isolation.** Run the named test with verbose output in the approved test environment. Capture only sanitized logs and deterministic inputs.
3. **Classify the failure.** Mark it as one of: missing environment prerequisite, missing approved artifact, incorrect implementation, obsolete test expectation, test nondeterminism, or missing external prerequisite.
4. **Choose the smallest safe resolution.** For implementation defects, make a minimal code/test change. For environment or provider dependencies, document an explicit prerequisite or conditional test profile. For obsolete expectations, revise test and documentation with evidence; do not silently delete the coverage.
5. **Run the local acceptance ladder.** Run the focused test, directly related suite, source compilation, and a repository whitespace/secret-safe documentation check. Retain results in a sanitized validation record.
6. **Update state only after validation.** Mark a roadmap item or regression group corrected only after focused evidence is retained. If the requirement is external, record a named blocker and the next authorized action.
7. **Rerun the full suite periodically.** After each coherent group is resolved, rerun the full suite and update this ledger with the remaining total. Do not claim a green release gate until the full suite passes in a supported environment.

## 5. Recommended correction order

| Order | Work package | Why it is first | Exit criterion |
|---:|---|---|---|
| 1 | Establish supported test environment | Ensures failures are source/fixture findings rather than missing-tool collection errors | A documented Linux/Windows test profile provides pytest and the GUI dependency needed for collection |
| 2 | Restore visual baseline and missing required reference targets | Missing fixtures and documents cause deterministic failures and hide higher-value regressions | Each target exists, is reviewed/provenanced, and its focused validation passes |
| 3 | Resolve provider/connector/media API contract failures | These are approval/credential/security-adjacent boundaries and should not be papered over | Focused tests pass with protected data redacted and no live external account action |
| 4 | Resolve orchestration, preview, and monitor reliability failures | Deterministic execution and safe monitoring support M14 operational evidence | Checkpoint, timeout, preview readiness, and monitor-copy tests are stable across repeat runs |
| 5 | Reconcile template, identifier, roadmap, and shell contracts | These preserve auditability and executable-roadmap integrity | Stable identifiers, required mappings, templates, and API wording match approved specification |
| 6 | Run full regression and independent review | Validates that fixes did not reopen a separate contract | Full suite passes, warnings are triaged, and a reviewer accepts the sanitized evidence |

## 6. M14 impact

The observed full-suite failure does not alter the prepared M14.8 change package's non-production entry gates: it remains **not approved for execution** until target-specific environment, identity, trust, health, rollback, evidence, and approval conditions pass. However, a non-green regression gate is an additional readiness risk. Before using M14.8 evidence as a production-readiness input, the applicable failure groups must be corrected or formally risk-accepted by the authorized release owner with an explicit scope and expiry.

## 7. Validation commands

Run from the repository root using the supported test profile:

```bash
python3 -m pytest tests/test_orville_manus_worker.py -q
python3 -m pytest <focused-test-path> -q
python3 -m compileall -q orville_core tests tools examples
python3 -m pytest -q
```

The first command currently passes all ten worker tests. The last command is expected to fail until the current ledger is resolved. It is retained here as the release-gate acceptance command, not as evidence of present success.

## 8. References

[1]: READINESS_REPORT.md "Repository readiness report"
[2]: MILESTONE_ROADMAP_REVIEW_2026-08-27.md "Prior roadmap review containing stale task_status finding"
[3]: M14_8_NONPRODUCTION_CHANGE_PACKAGE.md "M14.8 prepared change package"
[4]: M14_8_NONPRODUCTION_CANARY_ROLLBACK_DRILL_RUNBOOK.md "M14.8 drill procedure"
[5]: ../TASK_GRAPH.md "Current task graph"
