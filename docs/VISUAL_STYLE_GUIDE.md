# Orville Visual Style Guide

## Style objective

Orville presents a **professional, modern, clear, calm, operational** interface. The visual style helps users configure models, compose objectives, monitor execution, review verification, and retrieve artifacts without competing with the work. It uses restrained warm neutrals, a violet action accent, semantic status colors, precise typography, compact-readable density, and deliberate whitespace.

The canonical profile is `config/visual-style.example.json`; foundational tokens remain in `config/design-system.example.json`. The profile is a direction and review contract, not a claim that every existing client has already migrated.

## Composition and hierarchy

Each view has one dominant surface and one primary action. Content is constrained to a maximum width of 1440 px, with a focused central work area and supporting context beside or below it. The hierarchy is stable:

1. **Status:** What is happening, blocked, healthy, or failed?
2. **Next action:** What can the user safely do now?
3. **Result:** What did the operation produce?
4. **Context:** What details support understanding or audit?

Page titles and section titles use weight and spacing before color. Supporting text and metadata are quieter but never below the documented readable size. IDs, timestamps, paths, and logs use the monospace token to distinguish machine data from user-facing explanation.

## Visual language

| Element | Style rule | Usability reason |
|---|---|---|
| Canvas and surfaces | Warm neutral canvas with white/light or charcoal/dark surfaces, visible borders, and restrained elevation. | Separates work areas without visual noise or expensive decoration. |
| Primary action | One accent or dark primary button per surface; use a stable label and loading state. | Makes the next safe action obvious and prevents competing calls to action. |
| Secondary action | Quiet bordered or tonal treatment; preserve discoverability and focus visibility. | Supports recovery and navigation without weakening hierarchy. |
| Status | Text label plus semantic color and optional icon; never color alone. | Makes operational state understandable under low contrast or assistive technology. |
| Errors | Plain-language operation context, safe diagnostic, and bounded recovery action. | Reduces ambiguity without exposing raw exceptions or secrets. |
| Cards and panels | Use a single border/elevation treatment by level; avoid nested shadows. | Maintains grouping while keeping rendering and scanning costs low. |
| Data-dense content | Use tables, metadata rows, and monospace values with clear column hierarchy. | Preserves precise operational information without chat-like visual inflation. |
| Empty states | Explain what is absent, why it matters, and one next action. | Turns a blank region into a clear workflow entry point. |

## Performance posture

The style favors token-driven CSS/native values, solid colors, small purposeful icons, and layout over decorative media. Decorative assets are limited to 100 KB by default, initial font families to two, and large background imagery is avoided. Motion uses the shared durations and disables non-essential transitions under reduced motion. Loading preserves layout dimensions so users can continue scanning without shift.

For web clients, the style review targets a usable first view at 320 px, responsive behavior at compact and desktop widths, and a single visual language across light and dark themes. For Tkinter, the same goals map to native controls, explicit grid weights, stable pane sizes, and status text. Performance measurements belong to the relevant client build and must be recorded with the environment and artifact version.

## Usability and accessibility posture

The visual style is complete only when keyboard focus is visible, controls have accessible names, touch targets are at least 44 px, body text remains at least 14 px, and meaningful status changes are announced without stealing focus. Forms retain safe user input on validation failure. Dialogs are reserved for decisions that need interruption and provide labelled primary/cancel actions. Destructive or external actions require explicit confirmation.

Light/dark parity means that every semantic role has a readable value in both themes, not that colors are numerically inverted. Focus, danger, warning, and success states must remain distinguishable without relying only on hue. Theme preferences contain no bearer token, credential, or personal data.

## Review gates

| Gate | Pass condition |
|---|---|
| Token consistency | New styles use named design tokens; no unexplained one-off colors, spacing, shadows, or icon families. |
| Hierarchy | A reviewer can identify status, next action, result, and context within one scan. |
| Light/dark parity | Core surfaces and all interactive/status states remain readable and semantically consistent in both themes. |
| Responsive reflow | Primary tasks remain available at 320 px and existing compact thresholds without horizontal clipping. |
| Interaction states | Focus, hover, pressed, disabled, loading, empty, error, and confirmation states are represented and understandable. |
| Performance budget | No avoidable large decorative assets or font proliferation; motion and loading preserve usability. |
| Visual regression | Representative views are compared at compact, desktop, light, and dark configurations before approval. |

## Validation boundary

This guide establishes an actionable style contract and review method. It does not replace rendered browser/Tkinter review, automated accessibility tooling, device testing, or performance measurement. Those checks must be attached to the client implementation that consumes the tokens. No credentials, external services, or production data belong in style fixtures, screenshots, or review artifacts.
