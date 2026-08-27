# Responsive Layout Contract

## Scope

This contract covers the native desktop control center at the target widths supported by the current Tkinter application. The implementation keeps the primary objective workflow available while reducing secondary chrome and reflowing dense dashboard content as space decreases.

## Width behavior

| Window width | Shell behavior | Dashboard behavior |
|---|---|---|
| 1080 px and above | Sidebar and context rail remain available when space permits. | Six cards use three columns. |
| 980–1079 px | Context rail collapses below 980 px; primary content remains visible. | Six cards use two columns. |
| 790–979 px | Sidebar remains available where width permits; context rail is hidden. | Six cards use two columns with wrapped labels. |
| Below 790 px | Sidebar collapses; the primary objective workspace remains visible. | Six cards stack in one column and the refresh control spans the available column. |

The desktop window retains a 720 px minimum size, so the one-column mode is the smallest supported native desktop presentation. Web and mobile clients have separate responsive contracts and are not claimed as migrated by this change.

## Interaction requirements

Responsive changes are content-driven and occur without network requests. The primary objective composer, status, and recovery actions remain available at every supported width. Dashboard cards use bounded labels that wrap rather than clip, and the refresh action follows the final card row. Hidden sidebar/context regions can be restored by widening the window or using their existing controls.

## Accessibility and safety

Reflow does not remove approval gates, credential boundaries, accessible labels, keyboard entry points, or safe error feedback. Card meaning remains available through text labels and values; color is not the only status signal. No destructive action is introduced by resizing.

## Acceptance checks

Focused tests verify the three-column, two-column, and one-column thresholds, shell collapse thresholds, wrapped card labels, and refresh-row placement logic. Python compilation must pass for the GUI and test module. Pixel-level visual review, OS-specific font metrics, and web/mobile parity remain environment-dependent follow-up gates.
