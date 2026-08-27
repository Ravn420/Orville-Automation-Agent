# Orville Verification & Review View

## Purpose

The desktop Verification & Review view provides a bounded review surface for a persisted run. It gathers the acceptance criteria, test results, source evidence, visual checks, defects, residual risks, and approval state into one operator-readable view.

## Evidence sections

| Section | Persisted source | Review intent |
|---|---|---|
| Acceptance criteria | `context.acceptance_criteria` or objective fallback | Confirm what the run promised to deliver. |
| Test results | `context.verifications` or task statuses | Confirm independent checks and task outcomes. |
| Source evidence | `context.citations` or `context.source_evidence` | Confirm cited sources and provenance records. |
| Visual checks | `context.visual_checks` | Record rendered, legibility, responsive, or accessibility evidence. |
| Defects | `context.defects` or task errors | Surface known failures for disposition. |
| Residual risks | `context.residual_risks` or `context.risks` | Preserve unresolved implementation and deployment risks. |
| Approval state | `context.approval_state` or run status | Show whether the run is awaiting approval or has reached a terminal state. |

The view reads `GET /api/v1/runs/{run_id}` through the existing authenticated local API boundary. It does not mutate run state. **Refresh review** reloads the checkpoint and replaces the text view with the latest evidence.

## Safety and usability

Review values are rendered as bounded text, with each serialized section limited to 4,000 characters. Run IDs are URL-encoded. The view displays no credentials, raw provider configuration, or unbounded exception payloads. If a run cannot be loaded, it presents a generic recovery message. The 760 px minimum window width, keyboard-accessible controls, and plain-text section headings preserve usability without requiring visual interpretation.

Approval is represented as evidence; approval actions remain in the execution monitor and existing task-approval API. Visual checks are evidence supplied by the relevant artifact or test workflow; this view does not claim to perform OCR, pixel comparison, or live accessibility testing itself.

## Validation boundary

`tests/test_verification_review.py` verifies the required evidence sections, persisted context fields, navigation exposure, refresh control, bounded output contract, and safe rendering rules. Runtime evidence quality, source correctness, visual-review completeness, and authorization decisions remain review responsibilities rather than automatic claims.
