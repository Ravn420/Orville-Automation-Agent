# Reusable Components and Interaction Patterns

## Purpose and scope

This contract defines the reusable interface building blocks and interaction patterns for Orville’s desktop GUI, web UI, and future mobile clients. It extends docs/VISUAL_DESIGN_SYSTEM.md by specifying ownership, composition, states, event behavior, accessibility, responsive behavior, and review evidence. New features must compose these contracts before introducing a new component.

A component is a reusable contract, not merely a visual fragment. Its public inputs, outputs, states, keyboard behavior, loading and failure behavior, responsive fallback, and token dependencies are documented before implementation. A feature may add a variant only when the existing component cannot express the required user intent without ambiguity.

## Component architecture

| Family | Reusable components | Required responsibility |
|---|---|---|
| Actions | Button, icon button, split action, confirmation action | Express intent, prevent duplicate submission, expose busy/disabled state, and require confirmation for destructive or external effects. |
| Data entry | Field, textarea, select, combobox, date/time input, form section, validation summary | Associate labels and help, preserve safe input, report validation near the field, and provide a bounded recovery path. |
| Data display | Card, panel, table, list, detail view, status badge, progress indicator | Represent loading, empty, error, offline, unauthorized, and success states without conflating them. |
| Feedback | Inline message, toast, banner, alert, progress region | Announce safe operation context, severity, recovery, and dismissal without exposing raw exceptions. |
| Navigation | App shell, sidebar, breadcrumb, tabs, stepper, pagination | Preserve current location, support keyboard navigation, and collapse predictably at narrow widths. |
| Overlays | Dialog, drawer, popover, menu, command palette | Provide a label, focus management, escape/cancel behavior, outside-click policy, and explicit action ownership. |
| Orville domain | Task row, run timeline, model selector, approval panel, artifact viewer, health summary | Reuse the generic families while preserving task state, approval gates, artifact safety, and operational status semantics. |

Each component has one owner, one canonical implementation per target platform, and one named token source. Platform adapters may change rendering mechanics but must preserve the semantic contract and state meanings.

## State contract

Every interactive component supports only documented states. Baseline states are default, hover where pointer input exists, focus-visible, pressed or selected, disabled, loading, error, empty where applicable, and success where applicable. Domain components add offline, unauthorized, expired, blocked, or approval-required only when the state is meaningful and has a documented recovery or next action.

State transitions must be deterministic. Loading preserves layout dimensions, disables duplicate submission, and exposes progress when duration is material. Errors identify the failed operation, preserve non-secret user input, provide one bounded recovery action, and never show raw exceptions, credentials, cookies, or provider responses. A successful state is not shown until the operation has returned an authoritative success result.

## Interaction patterns

| Pattern | Required behavior | Prohibited behavior |
|---|---|---|
| Submit and mutate | Disable duplicate submission, show busy state, preserve an operation identifier, and report success or safe failure. | Silent retries, double submission, or claiming success before the authoritative result. |
| Destructive or external action | Name the consequence, identify the target, require explicit confirmation, and provide cancel. | Ambiguous labels, preselected destructive confirmation, or hidden external side effects. |
| Validation | Validate at the field when possible, summarize multiple failures, preserve safe values, and move focus only when helpful. | Clearing the whole form, relying on color alone, or exposing raw server errors. |
| Async loading | Preserve geometry, announce meaningful progress, bound retries, and provide cancellation where safe. | Indefinite spinners, unbounded polling, or shifting controls. |
| Empty, offline, and error | Explain the state and provide a single safe next action appropriate to that state. | Empty state that resembles success, retry loops, or disabled recovery without explanation. |
| Selection and navigation | Show selected and current-location semantics, preserve selection through refresh where valid, and support keyboard operation. | Hover-only status, lost selection after benign refresh, or navigation that changes durable state without confirmation. |
| Dialog and overlay | Label the surface, establish focus, return focus on close, and define escape/outside-click behavior. | Multiple competing primary actions, focus loss, or routine information hidden in a modal. |
| Long-running task | Provide status, elapsed or progress context where available, cancellation semantics, and durable result access. | Claiming completion from optimistic UI alone or hiding partial failure. |

## Composition rules

Components compose through documented slots and semantic properties rather than descendant selectors or target-specific visual hacks. A component may not redefine another component’s state colors, focus treatment, spacing rhythm, icon family, or motion durations. Variants are named by user intent, such as primary, secondary, quiet, danger, or selected; they are not named by arbitrary color or page location.

A surface has one primary action. Secondary and tertiary actions remain discoverable without competing with it. Tables, cards, banners, and dialogs use the same status vocabulary. Domain states map to the shared vocabulary before they are rendered, so running, blocked, failed, approved, and completed do not receive inconsistent meanings across screens.

## Accessibility and responsive behavior

Every component exposes an accessible name, role, state, value, and relationship appropriate to its semantics. Keyboard focus is visible and predictable. Meaningful status changes are announced without stealing focus. Motion is optional and respects reduced-motion preferences. Touch targets use the project’s 44 px minimum. At narrow widths, content reflows, panels stack, tables receive an accessible alternative, and the primary task remains reachable without horizontal scrolling.

The desktop implementation follows the same semantic contract through visible labels, predictable tab order, and status text. Web and mobile adapters must add platform-specific accessibility evidence without changing the component’s meaning or acceptance states.

## Review and acceptance

A new or changed component is accepted only when its design-system tokens, public contract, state matrix, interaction pattern, responsive fallback, accessibility evidence, security boundary, and visual regression evidence are recorded. Reviewers inspect every documented state at light and dark themes, compact and desktop widths, keyboard and pointer input, reduced motion, and representative failure conditions.

Focused repository validation is:

    python -m unittest tests.test_reusable_components_interactions
    python -m compileall -q tests/test_reusable_components_interactions.py

The contract does not claim that every existing GUI or web screen has been migrated. Unmigrated screens remain follow-up work and must not introduce new one-off interaction patterns.

## References

- WCAG 2.2, W3C: https://www.w3.org/TR/WCAG22/
- WAI-ARIA Authoring Practices, W3C: https://www.w3.org/WAI/ARIA/apg/
- Web Content Accessibility Guidelines Understanding, W3C: https://www.w3.org/WAI/WCAG22/Understanding/
