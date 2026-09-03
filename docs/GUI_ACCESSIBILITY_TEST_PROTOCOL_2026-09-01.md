# GUI Accessibility Test Protocol

**Related TODO:** `TODO-2db4ae3a211f`
**Status:** Blocked pending executable GUI target and assistive-technology environment
**Review date:** 2026-09-01

## Required matrix

| Dimension | Required test | Evidence required |
|---|---|---|
| Keyboard-only | Complete objective intake, plan review, execution controls, approval, cancellation, model setup, settings, and artifact access without a pointer. | Screen recording or step log, focus order, and keyboard trap result. |
| Screen reader | Verify names, roles, states, values, status announcements, error associations, and focus restoration. | Accessibility-tree capture and platform/screen-reader version. |
| High zoom | Test 200% text/display zoom and 400% reflow where applicable. | Viewport dimensions, screenshots, and content/functionality exceptions. |
| Reduced motion | Enable `prefers-reduced-motion` or platform equivalent and verify non-essential motion is removed or minimized. | Setting, route, and before/after behavior. |
| High contrast | Test supported high-contrast or forced-colors mode and both normal themes. | Theme/OS setting, contrast findings, and remediation status. |
| Small screens | Test supported mobile widths, virtual keyboard, orientation, safe-area insets, and 44 px effective targets. | Device/viewport, orientation, screenshots, and target-size findings. |
| Slow connections | Exercise loading, timeout, offline, retry, and preserved-input states under throttled conditions. | Network profile, timing, status announcements, and recovery result. |
| Long-running operations | Verify progress, pause/resume/retry/cancel, partial failure, completion, and non-focus-stealing announcements. | Run identifier, event trace, announcement result, and recovery evidence. |

## Execution boundary

The recovered checkout contains accessibility contracts and unit-level contract tests, but it does not contain an executable GUI target or a configured screen-reader/device/browser test environment. Therefore this document defines the reproducible procedure without claiming that the live tests passed.

## Closure criteria

Close the related TODO only after a real target is tested across the matrix, evidence is retained without credentials or private content, each critical failure has an owner and retest date, and the result is reconciled with `TODO.md`, `STATE.md`, and the release readiness report.
