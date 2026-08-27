# Theme and Status Behavior

## Theme contract

The GUI supports `light` and `dark` themes through the same semantic token roles. The default is light unless a user preference is present. A theme control is labelled with the action it performs, exposes its current state through `aria-pressed`, and applies the selected theme without changing route or task context.

The preference key is `orville-theme` and may contain only `light` or `dark`. Invalid, missing, or inaccessible preference values fall back to light. Theme preference is a non-secret client setting; credentials, prompts, provider responses, and personal data are never stored in it. Preference persistence is local to the current client and is not treated as an account or project setting.

Both themes must define canvas, surface, text, muted, border, accent, focus, success, warning, and danger roles. Text and focus indicators retain sufficient contrast against their current surface. Theme state must not rely on color alone for meaning, and non-essential motion is disabled when reduced motion is requested.

## Status-indicator contract

Every operational status uses a text label and may add an icon or semantic color. The label remains present in loading, ready, blocked, failed, stale, unavailable, approval-required, and needs-review states. Status changes include a safe timestamp or operation context where useful, while raw exceptions and credentials remain hidden.

| State | Required label | User action |
| --- | --- | --- |
| `ready` | Ready or available | Continue with the permitted primary action. |
| `running` | Running with progress when available | Inspect, pause, or cancel according to permissions. |
| `needs_review` | Needs review | Open evidence and record a review decision. |
| `blocked` | Blocked | Show the reason and one bounded remediation. |
| `failed` | Failed | Show safe error context and retry or escalate. |
| `stale` | Stale | Refresh or inspect the last-updated timestamp. |
| `unavailable` | Unavailable | Explain the missing dependency without exposing secrets. |
| `approval_required` | Approval required | Open the approval record; do not execute implicitly. |

Status badges, progress bars, tables, notifications, and navigation indicators must remain understandable in both themes, at narrow widths, with keyboard navigation, and when viewed without color perception. Progress must include a text or accessible label; warnings must not be communicated only through hue.

## Verification

A theme and status implementation is accepted when both themes render from semantic tokens, the preference survives reload with only the two allowed values, invalid preference values recover safely, focus remains visible, reduced-motion behavior is present, and every status in the state table has a visible label and bounded next action. Tests must use synthetic local storage only and must not require credentials or external services.
