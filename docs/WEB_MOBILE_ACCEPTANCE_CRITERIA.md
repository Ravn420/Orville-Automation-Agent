# Web and Mobile Acceptance Criteria

## Purpose and applicability

These criteria are the release gate for Orville static sites, full-stack web applications, and mobile clients. They apply to every user-facing screen, authenticated workflow, error state, loading state, empty state, modal, navigation path, and responsive layout. A feature is not accepted until the applicable checks pass on the supported target matrix and any exception is recorded with an owner, scope, expiry date, and compensating control.

> Acceptance means that the feature is usable, secure, and bounded on the smallest supported device and the slowest supported network—not only that it renders on a developer workstation.

## Supported target matrix

| Target | Required viewport/device class | Required checks |
|---|---|---|
| Small mobile | 320 CSS px wide, touch input | No horizontal scrolling for normal content; readable text; all primary actions reachable. |
| Large mobile | 390 CSS px wide, touch input | Orientation-safe layout; keyboard/input behavior; loading and error states. |
| Tablet | 768 CSS px wide, touch and keyboard where available | Navigation, tables, dialogs, and forms remain usable without overlap. |
| Desktop | 1280 CSS px wide, mouse and keyboard | Full information density, focus order, resizing, and error recovery. |
| Narrow desktop | 1024 CSS px wide | No clipped primary controls or inaccessible overflow. |

Responsive behavior must use content-driven breakpoints and reflow rather than device-name assumptions. At 400% browser zoom, the web UI must remain operable without loss of content or functionality except for content that inherently requires two-dimensional presentation, such as a bounded data table with an accessible alternative.

## Responsive design criteria

| ID | Criterion | Acceptance evidence |
|---|---|---|
| R-01 | Primary content and controls reflow at every target width. | Screenshots or automated viewport checks at 320, 390, 768, 1024, and 1280 CSS px show no unintended clipping or overlap. |
| R-02 | Text remains readable and does not depend on color, hover, or animation to convey meaning. | Review of normal, focus, hover, disabled, error, loading, and reduced-motion states. |
| R-03 | Touch targets have at least 44 by 44 CSS px of effective hit area, with sufficient separation to prevent accidental activation. | Measurement or visual inspection of interactive controls on small mobile. |
| R-04 | Long labels, translated strings, validation messages, and user-generated content wrap or truncate with an accessible full-value path. | Long-string fixture and keyboard/screen-reader review. |
| R-05 | Orientation changes, browser zoom, virtual keyboard appearance, and safe-area insets do not hide required controls. | Portrait/landscape and zoom checks on supported mobile classes. |
| R-06 | Navigation, dialogs, toasts, tables, and forms have a usable narrow-screen representation. | Each component has a documented narrow-width check and fallback behavior. |

## Accessibility criteria

The web target must meet **WCAG 2.2 Level AA** for applicable content, with keyboard and assistive-technology review for every critical workflow. Mobile targets must provide equivalent semantics and actions through platform accessibility APIs.

| ID | Criterion | Acceptance evidence |
|---|---|---|
| A-01 | All functionality is available by keyboard on web; focus is never trapped except inside an active modal. | Keyboard-only walkthrough of navigation, objective submission, run control, approval, cancellation, and artifact access. |
| A-02 | Focus order follows the visual and task order; focus indicators are visible and not obscured. | Keyboard review at default zoom and 200% zoom. |
| A-03 | Controls have accessible names, roles, states, and values; status changes are announced without stealing focus. | Accessibility-tree inspection plus screen-reader review of critical workflows. |
| A-04 | Color contrast is at least 4.5:1 for normal text, 3:1 for large text and meaningful graphics, and focus indicators are visibly distinct. | Automated contrast scan followed by manual review of custom components. |
| A-05 | Error messages identify the failed operation, explain recovery, are associated with the affected field or region, and do not expose secrets or raw exceptions. | Invalid-input and backend-failure fixtures; inspect rendered text and accessible announcements. |
| A-06 | Motion is optional and respects `prefers-reduced-motion`; flashing content is prohibited. | Reduced-motion test and animation review. |
| A-07 | Content remains usable at 200% text/display zoom and 400% reflow where applicable. | Browser zoom/reflow review at critical routes. |
| A-08 | Images, icons, tables, charts, and non-text content have appropriate alternatives or are marked decorative. | Content inventory and accessibility-tree review. |
| A-09 | Mobile controls support dynamic text size, screen readers, switch access, and sufficient touch target size. | Platform accessibility checks on each supported mobile class. |

## Security criteria

Frontend code is an untrusted presentation layer. It must not contain provider credentials, backend bearer tokens, private keys, cookies, or secret-bearing URLs. Server-side authorization, validation, path containment, rate limiting, and secret redaction remain authoritative even when the client performs equivalent checks for usability.

| ID | Criterion | Acceptance evidence |
|---|---|---|
| S-01 | Public builds contain no secrets or protected runtime configuration. | Secret scan of source, bundles, source maps, fixtures, and generated configuration. |
| S-02 | Authentication tokens are held only in the approved runtime/session boundary and are excluded from localStorage, URLs, analytics, screenshots, and logs. | Static scan plus browser/mobile storage and log inspection using synthetic credentials. |
| S-03 | Backend authorization is enforced on every protected operation; the client cannot elevate roles by changing fields or routes. | Negative API tests for missing, invalid, expired, and insufficient-scope credentials. |
| S-04 | Inputs and rendered remote content are validated or safely encoded; unsafe HTML, script URLs, and untrusted redirects are rejected. | XSS, injection, open-redirect, malformed-JSON, and unsafe-file-name fixtures. |
| S-05 | Production web delivery uses TLS, explicit origin allowlists, secure headers, and an appropriate Content Security Policy. | Deployment header capture and configuration review; local HTTP is permitted only for loopback development. |
| S-06 | Dependencies are pinned or lockfile-controlled, scanned before release, and updated through a reviewed change. | Dependency audit output retained with the release evidence. |
| S-07 | Error responses and telemetry contain operation identifiers and safe messages, never credentials, cookies, authorization headers, raw provider responses, or full exception strings. | Synthetic secret injection into representative failures followed by log, UI, and network inspection. |
| S-08 | File and artifact access is root-bound, size-limited, MIME-checked, and denied for traversal or unexpected content. | Traversal, oversize, invalid-MIME, and symlink/junction test fixtures. |

## Performance criteria

Budgets are measured on a production build with caching behavior recorded. Measurements must include the slowest supported target and a representative cold load; a local development server is not evidence of release performance.

| ID | Criterion | Budget or threshold |
|---|---|---|
| P-01 | Initial web route has useful content quickly on a representative mobile profile. | Largest Contentful Paint (LCP) at or below 2.5 seconds at the 75th percentile. |
| P-02 | Initial interaction becomes available without long main-thread blocking. | Interaction to Next Paint (INP) at or below 200 ms at the 75th percentile; no single long task over 200 ms during the critical flow. |
| P-03 | Layout remains stable while fonts, images, data, and status messages load. | Cumulative Layout Shift (CLS) at or below 0.1 at the 75th percentile. |
| P-04 | JavaScript and asset payloads remain bounded. | The initial route budget is 250 KB compressed JavaScript and 1 MB compressed total transfer unless an approved exception exists. |
| P-05 | API calls are bounded and cancellable. | Client timeout is configured, duplicate submissions are prevented, retries are limited, and stale requests are cancelled when the view is abandoned. |
| P-06 | Mobile resource use is bounded. | No unbounded polling, listener, timer, cache, or image growth; repeated navigation does not grow retained memory in a 10-cycle check. |
| P-07 | Loading, empty, offline, timeout, and retry states are useful and accessible. | Network-throttled and service-failure checks cover every critical data request. |
| P-08 | Performance regressions fail review when a budget is exceeded. | Production-build report compares measured values with the budgets and records an approved exception if needed. |

## Release evidence and validation sequence

For each release candidate, the implementer records the target build command, supported viewport/device results, accessibility scan and manual walkthrough, security scan and negative tests, performance report, known exceptions, and reviewer. Validation runs in this order:

1. Build the production artifact with no live credentials.
2. Run static checks for type errors, lint errors, secret exposure, unsafe dependencies, and invalid configuration.
3. Run responsive viewport and component-state checks.
4. Run automated accessibility checks, then manually test critical workflows with keyboard and assistive technology.
5. Run security negative tests against the frontend and backend boundary.
6. Run throttled-network and production-build performance checks.
7. Preserve sanitized evidence under `artifacts/` only when it is required for release or audit; keep disposable reports under `tmp/`.

A failed criterion blocks completion unless the exception is explicitly documented as `[!]` in the relevant task state. A warning must identify the affected target, user impact, mitigation, owner, and review date.

## References

- [WCAG 2.2, W3C](https://www.w3.org/TR/WCAG22/)
- [Web Content Accessibility Guidelines 2.2 — Understanding](https://www.w3.org/WAI/WCAG22/Understanding/)
- [Web Vitals, web.dev](https://web.dev/articles/vitals)
