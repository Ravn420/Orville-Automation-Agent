# Destructive-Action Confirmation Contract

## Scope

This contract applies to any Orville action that can delete, overwrite, revoke, publish, deploy, expose, or otherwise create an irreversible or high-impact external effect. It complements EXECUTION_CONTROLS.md: a confirmation explains the action to a person; the execution engine and backend remain responsible for authorization and enforcement.

No destructive handler may begin solely because a control was clicked, a keyboard shortcut was pressed, a request was replayed, or a confirmation dialog was opened. The action remains pending until an authorized confirmation is accepted for the exact action scope.

## Actions requiring confirmation

| Action class | Consequence preview must identify | Safe alternative or recovery |
|---|---|---|
| Delete artifact, model, project, or data | Exact object, scope, dependencies, retention impact, and whether recovery is possible. | Export, archive, deactivate, or create a backup before deletion. |
| Overwrite or replace a file/resource | Target path, current version, replacement source, and loss of prior content. | Save as a new version or create a backup. |
| Revoke credential, connector, session, or access | Principal, affected scopes, active sessions, and reconnection impact. | Disable temporarily or review scopes first. |
| Publish, deploy, or promote | Environment, release/version, audience, external effects, and rollback route. | Dry run, preview, canary, or staged promotion. |
| Enable schedule or external notification | Trigger, cadence, target, data class, and stop action. | Keep manual or run a local preview. |
| Reset or remove durable configuration | Scope, settings lost, inherited values, and restart/migration impact. | Export settings or reset a narrower scope. |

## Confirmation requirements

A confirmation surface must use a specific action verb and name the exact target and scope. It must present the expected consequence in plain language, distinguish reversible from irreversible effects, identify what will not be changed, show the required approval or authorization, and expose a cancel action with equal keyboard reachability. Destructive actions must not use ambiguous labels such as Continue, OK, or Submit as the only confirmation text.

The confirm action remains disabled until required scope, target, and consequence data are loaded and validated. For high-impact actions, require an explicit typed acknowledgement or equivalent deliberate gesture in addition to the confirmation control. Confirmation tokens are single-use, bound to the action fingerprint and scope, expire after a bounded interval, and cannot be reused after cancellation, rejection, expiry, or a material change.

## State and failure behavior

The action states are `preview`, `awaiting_confirmation`, `awaiting_approval`, `confirmed`, `rejected`, `expired`, `cancelled`, `executing`, `completed`, and `failed`. Opening a dialog never transitions to `confirmed`. Rejected, expired, cancelled, or failed confirmations do not advance the task. A stale preview must be regenerated before confirmation. The standalone `orville_core.confirmations.ConfirmationGate` issues receipts only for allowlisted sensitive operation kinds, binds them to the request fingerprint, bounds their lifetime to 15 minutes or less, and consumes each receipt once immediately before execution.

If the operation fails after confirmation, the interface reports the operation identifier, safe error class, completed sub-steps if known, and recovery action. It must not claim success, silently retry a destructive action, hide partial effects, or display raw exceptions or secrets. Recovery may offer restore, retry only when idempotency is proven, reconcile status, or contact an operator; each option repeats its consequence.

## Accessibility and security

Confirmation dialogs use a labelled heading, descriptive consequence text, a modal focus trap while open, a visible focus indicator, Escape-to-cancel where supported, and focus restoration to the invoking control. Consequences and errors are announced to assistive technology and are not conveyed by color alone.

Confirmation payloads contain a stable action fingerprint, target identifier, scope, actor or authorization reference, expiry, and policy version. They exclude credentials, bearer tokens, cookies, private keys, raw authorization headers, and secret-bearing URLs. Backend authorization, policy checks, path containment, idempotency, and audit recording remain authoritative.

## Acceptance criteria

The contract is accepted when every destructive action class has a plain-language consequence preview, explicit target and scope, reversible alternative where available, separate cancel and confirm controls, approval enforcement where required, stale-confirmation rejection, non-advancing failure behavior, accessible dialog semantics, safe diagnostics, and auditable evidence. Tests use synthetic identifiers only and make no external requests.

Focused validation is:

    python -m unittest tests.test_destructive_action_confirmations tests.test_confirmations
    python -m compileall -q orville_core/confirmations.py tests/test_confirmations.py

## References

- Execution controls: EXECUTION_CONTROLS.md
- Delivery runbook: docs/DELIVERY_RUNBOOK.md
- Accessibility acceptance criteria: docs/ACCESSIBILITY_ACCEPTANCE_CRITERIA.md
