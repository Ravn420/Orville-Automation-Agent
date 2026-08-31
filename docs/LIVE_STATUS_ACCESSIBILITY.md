# Live Execution Status Accessibility Contract

This contract defines how Orville communicates execution progress, completion, partial failure, cancellation, and approval-required states. It applies to desktop and web clients and supplements `docs/ACCESSIBILITY_ACCEPTANCE_CRITERIA.md`.

## Required behavior

Every live update must expose a meaningful text status in an assistive-technology-readable region. Use a single persistent `role="status"` or `aria-live="polite"` region for routine progress and completion messages; use `role="alert"` only for urgent failures that require immediate attention. Updates must not move focus or interrupt the user's current control unless the user explicitly invokes an action.

The message must identify the operation and state, such as “Model import: 3 of 5 files verified,” “Task execution: paused,” “Task execution: completed,” or “Artifact export: failed; retry export or open details.” Progress indicators should expose the current value and bounds through accessible semantics, while the same information remains available as text.

State distinctions must never depend on color alone. Status badges, progress bars, icons, borders, and charts must be paired with visible text, an accessible name/state, or a non-color pattern. Error and partial-failure states must include recovery guidance and preserve any user-entered input. Success, blocked, offline, cancelled, and approval-required states receive equivalent text and semantic treatment.

## Acceptance matrix

| State | Required announcement | Non-color evidence | Focus behavior |
|---|---|---|---|
| Running | Operation name and current progress | Text plus semantic progress value | No focus steal |
| Paused | Operation name and paused state | Text and pause label/icon | No focus steal |
| Completed | Operation name and completion | Text and completion semantics | No focus steal |
| Partial failure | Affected operation, failed count, and recovery action | Text plus error icon/marker | Keep current focus |
| Failed | Failed operation and retry/details action | Text plus alert semantics | Focus only when user requests details |
| Approval required | Required decision and consequence | Text and labelled control | Move focus only after explicit invocation |
| Offline/cancelled | State and next available action | Text plus icon/pattern | No focus steal |

## Validation boundary

The repository-level contract is validated by `tests/test_live_status_accessibility.py`. It does not claim that every existing screen has passed a live screen-reader, browser, or desktop visual review; those checks remain required for each client implementation.
