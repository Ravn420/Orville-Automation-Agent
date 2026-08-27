# Regression Remediation Plan

**Status:** Implemented and validated on the `fix/regression-contracts` branch.
**Scope:** The stale roadmap-phase assertion and TODO-ID normalization defect identified by the 2026-08-27 regression run.

## Purpose

This plan records the controlled resolution of two roadmap-integrity defects. The first defect caused a test to classify a completed roadmap item as in progress. The second caused the deterministic identifier utility to append duplicate task IDs to checklist entries that already contained an ID before completion evidence.

| Defect | Root cause | Risk | Resolution |
|---|---|---|---|
| Stale roadmap-phase assertion | `tests/test_roadmap_phase_increments.py` required `[-]` for a roadmap entry whose evidence-backed status is `[x]`. | A test could encourage a false downgrade of completed work or conceal the actual roadmap state. | Assert the current completed `[x]` state while retaining the checks for the Phase 2 provider and Phase 3 media mapping evidence. |
| TODO-ID normalization | `tools/assign_todo_ids.py` recognized a `task-id` marker only at the end of a checklist body. Completion evidence after an existing marker made the parser append another marker. | The canonical roadmap was non-idempotent and task identity could become ambiguous. | Recognize a well-formed existing marker anywhere in the checklist body and add a regression fixture for marker-plus-evidence records. |

## Implementation Sequence

The remediation follows a narrow, reversible sequence. It changes the test assertion before changing no roadmap state, then fixes the identifier parser, adds a targeted regression case, runs the focused integrity checks, and finally runs the full project suite. The parser never rewrites a record that already has a valid `TODO-` marker, and it does not change the identity algorithm for records that genuinely lack a marker.

| Step | Changed path | Acceptance criterion |
|---|---|---|
| 1 | `tests/test_roadmap_phase_increments.py` | The test accepts the verified `[x]` state and continues to require both phase-mapping terms. |
| 2 | `tools/assign_todo_ids.py` | Existing machine-readable markers are detected wherever they appear in the checklist text. |
| 3 | `tests/test_todo_identifiers.py` | A line with an ID followed by completion evidence is unchanged and reports `changed == 0`. |
| 4 | `TODO.md` | The non-mutating ID check reports `identified_records=996 changed=0`. |
| 5 | Project regression suite | `python3 tools/project_checks.py test` completes successfully. |

## Validation Evidence

The focused regression modules passed **72 tests** after the wider patch set was applied. The project-prescribed test check then passed with **781 tests and 6 subtests**. The TODO-ID utility now reports zero proposed changes against the canonical roadmap, so its repeat application is idempotent.

## Ongoing Controls

Future checklist tooling changes must preserve the following invariants. Every actionable checklist record must have exactly one stable marker; the marker may be followed by human-readable evidence; repeated normalization must produce byte-identical content; and a status assertion must validate the recorded completion state rather than require a historical work-in-progress marker. Any update to status, evidence, or identifier behavior requires focused tests and a full regression check before it is committed.

## Known Limitations

This remediation does not attempt to merge duplicate markers that may exist in independently edited documents; it safely avoids creating a new marker when one valid marker is present. A future migration, if needed, must be separately approved, report its affected lines, preserve IDs referenced by `TASK_GRAPH.md` and `STATE.md`, and provide a rollback copy before any write operation.
