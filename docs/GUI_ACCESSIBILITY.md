# GUI Accessibility Contract

## Scope

This contract covers the native Tkinter control center surfaces changed for the accessibility roadmap item. It defines keyboard operation, visible focus, semantic labeling, contrast, reduced-motion behavior, and safe error feedback without changing API or authorization behavior.

## Requirements

| Criterion | Local implementation |
|---|---|
| Keyboard navigation | Native `Tab` traversal remains available; `Alt+1` focuses the objective composer, `Alt+2` opens workflow help, and `Escape` returns focus to the application shell. |
| Visible focus | Button styles expose a purple focus border; text areas use a two-pixel focus outline that changes from the neutral border to the accent color. |
| Semantic controls and labels | Controls retain descriptive visible labels, the objective workspace explains keyboard entry points, and text areas remain explicitly focusable. |
| Color contrast | Existing semantic text/status colors are retained from the design system; focus is communicated by both border treatment and keyboard state rather than color alone. |
| Reduced motion | The native desktop implementation uses no animated transitions or auto-scrolling effects as part of accessibility feedback. |
| Accessible errors | Failed objective requests use an operation-specific, secret-safe status message with a recovery instruction and return focus to the objective composer. Raw exception text and response payloads are not displayed. |

## Safety boundaries

Accessibility feedback does not bypass approvals, authorization, credential handling, or destructive-action confirmations. Error messages identify the failed operation without echoing request data, credentials, raw exceptions, or server payloads.

## Acceptance checks

Focused tests verify the keyboard bindings, focus styling, descriptive labels, reduced-motion-safe behavior, and secret-safe recovery wording. Python compilation must pass for the GUI and test module. Full visual contrast measurement, screen-reader inspection, and platform-specific keyboard testing remain human or environment-dependent review gates.
