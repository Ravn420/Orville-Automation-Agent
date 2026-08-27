# Orville Visual Design System

## Purpose

The Orville visual design system provides a shared language for the desktop GUI, static web UI, and future mobile clients. The canonical non-secret token example is `config/design-system.example.json`; implementations may map these tokens to Tkinter styles, CSS custom properties, or native platform resources without changing their meanings.

The visual direction is a restrained control-center interface: warm neutral canvas, white or dark elevated surfaces, near-black or light text, violet action accent, semantic status colors, compact information density, and consistent focus and motion behavior. The system prioritizes readable operational state over decorative effects.

## Foundations

| Foundation | Rule |
|---|---|
| Typography | Use the UI sans stack for navigation and controls, a monospace stack for IDs/logs/code, a 4/8 px spacing rhythm, 1.5 body line height, and semibold hierarchy. Do not communicate hierarchy through color alone. |
| Color | Use canvas, surface, text, muted, border, accent, focus, success, warning, and danger roles. Light and dark values are paired by semantic role, not by direct color inversion. |
| Spacing | Use the token scale from 4 to 64 px. Component internals use 8/12/16 px; page sections use 24/32/48 px. |
| Elevation | Use no shadow for flat regions, small shadow for cards, medium shadow for menus, and large shadow only for dialogs or transient overlays. Borders remain visible in both themes. |
| Icons | Use one consistent stroke family and 16/20/24 px sizes. Every action icon has an accessible label or visible text; decorative icons are hidden from assistive technology. |
| Motion | Use 120/200/320 ms durations for fast/standard/slow transitions. Disable non-essential motion when reduced motion is requested. |
| Responsive behavior | Follow the existing GUI’s compact thresholds near 790 and 980 px; web implementations may add content-driven breakpoints, but controls must remain usable at 320 px. |

## Themes and contrast

Light and dark themes use the same semantic roles and component states. Text, borders, status indicators, and focus rings must retain sufficient contrast against their current surface. Status must be conveyed by text or icon plus color. Theme preference may follow the system preference and may be persisted only through an approved client setting; secrets and bearer tokens are never part of theme state.

## Component inventory and states

| Component | Required states and behavior |
|---|---|
| Button and icon button | Default, hover, pressed, focus-visible, disabled, loading, and destructive-confirmation states. Prevent duplicate submission while loading. |
| Text input, textarea, and select | Default, focus, filled, disabled, read-only, invalid, and success states. Labels remain associated; errors identify the failed operation and recovery. |
| Form | Group related fields, show required/optional status, preserve entered non-secret values on validation failure, and provide a summary for multiple errors. |
| Table | Header, row hover, selected row, empty, loading, error, pagination, and narrow-screen representation. Provide an accessible alternative when horizontal scrolling is not sufficient. |
| Card and panel | Default, selected, loading, error, and empty states. Use elevation and border consistently; do not use nested shadows for hierarchy. |
| Notification and toast | Informational, success, warning, and error variants. Include text, safe operation context, dismiss behavior, and non-color semantics; do not expose raw exceptions. |
| Dialog and confirmation | Focus trap while open, labelled title, clear primary/cancel actions, escape behavior where safe, and explicit confirmation for destructive or external actions. |
| Empty state | Explain what is absent, why it matters, and the single safe next action. Distinguish empty, loading, offline, unauthorized, and failed states. |
| Status badge and progress | Pair semantic color with a text label and, where useful, icon. Announce meaningful changes without stealing focus. |
| Navigation and tabs | Persistent active indicator, keyboard navigation, responsive collapse, and a visible current location. |

## Interaction rules

Primary actions use the accent or dark action style only once per surface. Secondary actions are visually quieter but remain discoverable. Destructive actions use the danger role and require confirmation when they change external or durable state. Disabled controls explain why they are unavailable when the reason is not obvious. Loading states preserve layout dimensions and prevent duplicate requests. Error states preserve safe user input, identify the failed operation, and offer a bounded recovery action.

Forms use visible labels, helper text only when needed, inline validation near the field, and a summary when multiple fields fail. Tables never hide critical status solely in hover content. Dialogs must not be used for routine information that can fit in the page flow. Empty states must not impersonate successful completion.

## Accessibility and responsive requirements

All web controls must support keyboard operation, visible focus, semantic names and roles, screen-reader announcements for meaningful state changes, and the acceptance criteria in `docs/WEB_MOBILE_ACCEPTANCE_CRITERIA.md`. Touch targets use at least 44 px effective size. At narrow widths, panels stack or collapse without hiding the primary task. The desktop Tkinter implementation follows the same semantic rules through visible labels, predictable tab order, and status text.

## Implementation and review

Use `config/design-system.example.json` as the token source for new components. A component change must identify its token usage, states, theme behavior, responsive behavior, accessibility evidence, and visual regression evidence. Do not introduce one-off colors, arbitrary spacing, icon families, or unreviewed shadows. The design system defines reusable contracts; it does not claim that the existing GUI or static bundle has been fully migrated.

## Validation checklist

1. Verify every component uses named tokens rather than hard-coded visual values.
2. Review light and dark states at compact and desktop widths.
3. Exercise keyboard, focus, reduced-motion, loading, error, empty, and disabled states.
4. Check text, status, focus, and control contrast with automated and manual review.
5. Confirm 44 px touch targets and 320 px reflow behavior for web/mobile implementations.
6. Confirm no secret or user credential enters theme state, analytics, screenshots, or examples.
7. Record unresolved visual or accessibility gaps as scoped warnings with an owner and follow-up gate.
