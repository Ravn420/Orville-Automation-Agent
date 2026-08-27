# Accessibility Acceptance Criteria

## Scope

This contract applies to Orville desktop GUI, web UI, mockups, and future mobile clients. It extends docs/WEB_MOBILE_ACCEPTANCE_CRITERIA.md and docs/VISUAL_DESIGN_SYSTEM.md with a focused review matrix for the critical workflows: objective intake, task planning, execution monitoring, approval, model setup, artifact access, and settings.

Acceptance is evidence-based. A screen is not complete because it appears usable with a pointer; each critical workflow must pass keyboard, focus, semantic, visual, motion, and error-feedback checks for its target platform.

## Criteria

| ID | Requirement | Evidence |
|---|---|---|
| A11Y-01 | All critical functionality is available by keyboard. Tab order follows task order; no keyboard trap exists outside an active modal. | Keyboard-only walkthrough of navigation, objective submission, plan inspection, run controls, approval, cancellation, model setup, settings, and artifact access. |
| A11Y-02 | Focus is visible, sufficiently distinct from the surrounding surface, and restored to the invoking control when a dialog or drawer closes. | Review at default zoom, 200 percent zoom, light/dark themes, and compact layout. |
| A11Y-03 | Every control has a meaningful accessible name, role, state, and value. Grouped fields have associated labels and errors are programmatically related to their field or region. | Accessibility-tree inspection and screen-reader review of critical workflows. |
| A11Y-04 | Status, progress, validation, and error changes are announced without stealing focus. Status is not communicated by color alone. | Screen-reader review with loading, success, blocked, offline, failed, and approval-required fixtures. |
| A11Y-05 | Text contrast is at least 4.5:1 for normal text and 3:1 for large text and meaningful graphics. Focus indicators and disabled-state distinctions remain perceivable. | Automated contrast scan followed by manual review of custom components and both themes. |
| A11Y-06 | Non-essential motion respects the reduced-motion preference; flashing content is prohibited. | Reduced-motion media-setting test and timeline review. |
| A11Y-07 | Content remains usable at 200 percent text/display zoom and 400 percent reflow where applicable. No essential content or action depends on horizontal scrolling. | Browser reflow review and desktop compact-layout review at critical routes. |
| A11Y-08 | Images, icons, tables, charts, media, and generated artifacts have an appropriate alternative or an explicit decorative designation. | Content inventory plus accessibility-tree and rendered-output review. |
| A11Y-09 | Mobile clients provide equivalent actions through platform semantics, dynamic text sizing, screen readers, switch access, and at least 44 pixel effective touch targets. | Platform accessibility checks on every supported mobile class. |
| A11Y-10 | Error feedback names the failed operation, explains the recovery action, is associated with the affected field or region, and excludes secrets, raw exceptions, and provider response bodies. | Invalid-input, timeout, blocked, authorization, and backend-failure fixtures with UI and announcement inspection. |

## Workflow review matrix

| Workflow | Minimum review states |
|---|---|
| Objective intake | Empty, filled, invalid, loading, submitted, and preserved-input error. |
| Task plan | Keyboard node traversal, selected node announcement, dependency fallback tree, blocked task, retry state, and verification-pending state. |
| Execution monitor | Running progress, pause/resume/retry/cancel controls, partial failure, completion, and live status announcement. |
| Approval | Focus trap, labelled consequence, cancel/confirm order, rejected approval, expired approval, and focus restoration. |
| Model setup | Labelled fields, protected credential reference, endpoint error, advanced disclosure, and safe recovery guidance. |
| Artifact access | Keyboard browse, alternative text/transcript, loading, unavailable artifact, download confirmation, and permission denial. |
| Settings | Section navigation, invalid value association, reset confirmation, saved status, and protected-value redaction. |

## Failure and remediation policy

A critical workflow fails acceptance when keyboard operation, focus visibility, semantic naming, required contrast, reduced-motion behavior, or accessible error recovery is missing. The finding records the route or screen, target platform, state, severity, reproduction steps, evidence, owner, mitigation, and retest date. A warning may remain only when the affected path is non-critical, the issue does not block access, and an owner and follow-up gate are recorded.

Automated audits are screening evidence, not a substitute for manual keyboard and assistive-technology review. Platform-specific gaps remain explicit rather than being hidden behind a passing aggregate score.

## Security boundary

Accessibility labels, announcements, screenshots, telemetry, and test fixtures must not contain credentials, bearer tokens, cookies, private keys, raw authorization headers, or secret-bearing URLs. Safe operation identifiers and redacted error classes may be exposed when they help recovery.

## Validation commands

From the repository root, run:

    python -m unittest tests.test_accessibility_acceptance
    python -m compileall -q tests/test_accessibility_acceptance.py

The contract does not claim that every existing screen has passed live assistive-technology, browser, mobile, or production visual testing.

## References

- WCAG 2.2, W3C: https://www.w3.org/TR/WCAG22/
- WAI-ARIA Authoring Practices, W3C: https://www.w3.org/WAI/ARIA/apg/
- Web Content Accessibility Guidelines Understanding, W3C: https://www.w3.org/WAI/WCAG22/Understanding/
