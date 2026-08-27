# GUI Test Strategy

## Purpose

This document defines the minimum automated coverage for Orville's major GUI journeys. The strategy is designed to run without Manus, external credentials, a live provider, or a browser session. It verifies the shipped contracts and static prototypes while keeping live visual, assistive-technology, and backend integration checks explicit as separate release gates.

## Test layers

| Layer | Scope | Automated evidence |
|---|---|---|
| Component | Shared visual and interaction contracts such as labels, focus, status, buttons, dialogs, and safe messages. | Design-system and reusable-component contracts plus static markup assertions. |
| Workflow | One surface at a time: task composer, task plan, execution monitor, model configuration, generation workspace, verification, artifacts, settings, and help/recovery. | Required fields, actions, state vocabulary, approval boundaries, persistence, and redaction assertions. |
| Accessibility | Keyboard entry points, accessible names, focus-visible styling, live status/error regions, contrast guidance, reduced motion, and responsive reflow requirements. | Contract and prototype checks; manual assistive-technology review remains required. |
| Responsive | Desktop, tablet, and compact layouts where the target permits them. | Viewport metadata, media queries, responsive contract, and compact-layout markers. |
| End-to-end journey | A user creates an objective, reviews a plan, monitors execution, verifies results, and retrieves an artifact. | Deterministic cross-surface journey fixture confirms ordered entry points and safety gates without executing external actions. |

## Major journey contract

The automated journey follows this order:

1. **Objective intake:** task composer captures an objective, constraints, files, model, and acceptance criteria.
2. **Plan review:** task-plan view exposes dependencies, assigned agents, statuses, blockers, retries, and verification gates.
3. **Execution:** execution monitor exposes progress, events, elapsed time, and pause/resume/retry/cancel controls.
4. **Verification:** verification review exposes criteria, test results, evidence, defects, residual risks, and approval state.
5. **Delivery:** artifact browser exposes preview, version, export, download, and organization actions.

Each transition must remain local and reviewable until explicit execution or external approval is requested. Test fixtures use synthetic IDs and do not submit forms, call providers, access connectors, or mutate files outside the repository.

## Acceptance criteria

- Every critical GUI surface has a component-level contract assertion.
- Every major journey surface has a workflow test for required inputs, states, actions, and safe boundaries.
- Accessibility checks verify semantic names, visible focus, status/error announcements, reduced-motion handling, and secret-safe copy.
- Responsive checks verify viewport metadata, reflow guidance, compact-layout behavior, and no fixed-width-only requirement.
- The end-to-end fixture verifies the five-stage journey in dependency order and fails if a required surface or safety gate is absent.
- Failures identify the layer and surface that failed; no test relies on external credentials or network access.

## Validation commands

From the repository root:

```text
python -m unittest tests.test_gui_quality -v
python -m compileall -q tests/test_gui_quality.py
```

Existing focused tests for individual workflows remain authoritative and should be run alongside this aggregate suite. Live browser automation, screen-reader testing, visual screenshot comparison, performance measurement, and backend-integrated e2e execution are not claimed by this local contract.

## Related contracts

- `docs/VISUAL_DESIGN_SYSTEM.md`
- `docs/REUSABLE_COMPONENTS_INTERACTIONS.md`
- `docs/GUI_ACCESSIBILITY.md`
- `docs/ACCESSIBILITY_ACCEPTANCE_CRITERIA.md`
- `docs/RESPONSIVE_LAYOUTS.md`
- `docs/GUI_INFORMATION_ARCHITECTURE.md`
