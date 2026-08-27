# Help, Errors, Onboarding, and Recovery Guidance

## Purpose

This contract defines how Orville helps a person understand the interface, recover from a failed or interrupted operation, and make an informed decision before a consequential action. Guidance is contextual, plain-language, accessible, and safe to expose. It applies to the desktop GUI, web mockups, and future mobile clients.

## Help model

Every critical workflow provides help at the point of need and a route to the broader **Help** area. Help content must answer three questions: **What is this? What is required? What can I do next?** The content must not require knowledge of agents, task graphs, provider-specific APIs, or command-line operation.

| Surface | Required behavior | Acceptance evidence |
|---|---|---|
| Onboarding | Show a short first-run path: describe objective, review plan, run and verify. Preserve the user's draft when guidance is opened. | First-run walkthrough and preserved-input check. |
| Contextual help | Place a concise explanation beside unfamiliar fields or states. Provide a keyboard-accessible tooltip or expandable description with a meaningful accessible name. | Keyboard and accessibility-tree review for objective, privacy, endpoint, approval, artifact, and recovery controls. |
| Error message | Name the failed operation, state the safe error class, explain the impact, provide a specific recovery action, and include a bounded operation identifier. | Invalid input, timeout, blocked, authorization, offline, and backend-failure fixtures. |
| Confirmation | Explain exact target, scope, consequence, reversibility, and what remains unchanged. Use distinct cancel and action-specific confirm labels. | Confirmation-dialog review against `docs/DESTRUCTIVE_ACTION_CONFIRMATIONS.md`. |
| Recovery action | Offer only actions permitted by state and policy: resume, retry when idempotency is proven, cancel while preserving evidence, reconcile, restore, or escalate. | Interrupted, partial, failed, expired, and unavailable-provider fixtures. |

## Error contract

User-visible errors use the following structure:

```text
<Operation> could not <action>.
Reason: <safe bounded error class>.
Impact: <what changed and what did not change>.
Next action: <one or more permitted recovery actions>.
Operation: <stable non-secret identifier>.
```

Messages must be specific enough to act on but must never include raw exceptions, response bodies, prompts, credentials, bearer tokens, cookies, private keys, local absolute paths, secret-bearing URLs, or unredacted provider identifiers. The backend remains authoritative for authorization and policy enforcement; the interface does not claim success until a confirmed result is received.

## State guidance

| State | Minimum user-facing content | Permitted actions |
|---|---|---|
| Loading | What is being checked or prepared, with last-updated context where applicable. | Cancel if supported; do not duplicate-submit. |
| Empty | What is absent and the next permitted setup or creation action. | Create, configure, import, or return. |
| Offline/unavailable | Which dependency is unavailable and whether local mode remains usable. | Retry boundedly, use local fallback, inspect diagnostics, or continue offline. |
| Blocked/approval required | Blocking condition, affected scope, and required approval or configuration. | Review, approve, configure, or cancel. |
| Failed | Operation, safe reason, impact, operation ID, and recovery. | Resume, retry if safe, reconcile, preserve evidence, or escalate. |
| Partial | Completed and not-started portions, artifact/evidence preservation, and dependency impact. | Resume, retry eligible work, export evidence, or cancel. |
| Long-running | Elapsed time, current stage, last event, expected next checkpoint, and controls. | Pause, resume, cancel, or inspect details without losing context. |

## Confirmation and recovery rules

Opening a confirmation dialog never confirms an action. Dialogs use a labelled heading, consequence preview, separate cancel and action-specific confirm controls, keyboard access, visible focus, Escape-to-cancel where supported, and focus restoration. A stale or expired preview must be regenerated. A failed post-confirmation operation must report partial effects when known and must not silently repeat a destructive action.

Recovery controls are state-aware and idempotency-aware. **Resume** starts only from a durable checkpoint; **retry** is shown only when the operation is safe to repeat; **cancel** preserves prior logs, checkpoints, and evidence; **reconcile** refreshes authoritative state without replaying work; and **escalate** provides a safe operation ID and diagnostic class without exposing sensitive data.

## Accessibility and localization

Status and errors use text and icons, not color alone, and are exposed through an appropriate live region without stealing focus. Each field error is programmatically associated with its field. Tooltips must be discoverable by keyboard and must not be the only source of essential information. Copy is stored as user-interface content rather than embedded in business logic; message keys should be stable and support future localization without changing operation semantics.

## Acceptance checklist

- [ ] A first-run user can complete the onboarding path without CLI or framework knowledge.
- [ ] Critical unfamiliar controls have contextual help with accessible names.
- [ ] Error fixtures identify operation, safe reason, impact, next action, and operation ID.
- [ ] No user-visible message contains secrets, raw exceptions, response bodies, or absolute local paths.
- [ ] Confirmation dialogs identify target and consequence and have separate cancel/confirm actions.
- [ ] Resume, retry, cancel, reconcile, and escalation actions are state- and policy-aware.
- [ ] Loading, empty, offline, blocked, failed, partial, and long-running states are distinct.
- [ ] Keyboard, focus, screen-reader announcement, contrast, reduced-motion, and responsive checks pass.

## Validation

From the repository root:

```text
python -m unittest tests.test_help_and_recovery
python -m compileall -q tests/test_help_and_recovery.py
```

The standalone prototype is `docs/mockups/help-recovery.html`. It uses synthetic identifiers only and performs no external requests or state-changing operations.

## Related contracts

- `docs/ACCESSIBILITY_ACCEPTANCE_CRITERIA.md`
- `docs/DESTRUCTIVE_ACTION_CONFIRMATIONS.md`
- `docs/GUI_INFORMATION_ARCHITECTURE.md`
- `docs/PLAIN_LANGUAGE_WORKFLOWS.md`
- `docs/RESPONSIVE_LAYOUTS.md`
