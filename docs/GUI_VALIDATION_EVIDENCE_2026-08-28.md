# GUI Validation Evidence

**Task ID:** `TODO-2db4ae3a211f`  
**Scope:** Keyboard-only navigation, screen readers, high zoom, reduced motion, high contrast, small screens, slow connections, and long-running operations.

## Validation result

The repository's GUI quality contract was validated locally on 2026-08-28 with **21 focused tests passing**. The checks are deterministic source, mockup, workflow, and degraded-availability checks; they do not contact providers or submit external forms.

```text
python -m pytest -q \
  tests/test_gui_accessibility.py \
  tests/test_gui_quality.py \
  tests/test_responsive_layouts.py \
  tests/test_gui_degraded_availability.py \
  tests/test_streaming_controls.py \
  tests/test_gui_performance_measurement.py
# 21 passed
python -m compileall -q orville_core tests
# passed
git diff --check
# passed
```

## Coverage matrix

| Dimension | Evidence checked | Result and boundary |
|---|---|---|
| Keyboard-only navigation | Native keyboard entry points, focusable controls, visible focus, responsive keyboard contract | Automated contract passed; physical keyboard traversal remains a Windows-host smoke check. |
| Screen readers | Semantic labels, status/error regions, accessible names, and screen-reader wording in the GUI strategy | Automated contract passed; NVDA/ Narrator/VoiceOver speech output was not claimed from this Linux validation environment. |
| High zoom | Reflow and compact/width-responsive layout contracts in `docs/GUI_TEST_STRATEGY.md` and `docs/RESPONSIVE_LAYOUTS.md` | Automated contract passed; 200% and 400% visual inspection remains platform-owned. |
| Reduced motion | Reduced-motion strategy marker and no-motion native GUI contract | Automated contract passed; OS preference propagation requires platform smoke validation. |
| High contrast | Focus visibility, contrast markers, and semantic-color guidance | Automated contract passed; Windows High Contrast rendering remains a Windows-host check. |
| Small screens | Mockup viewport declarations, media queries, tablet/compact/reflow contracts | Automated contract passed; real device/browser rendering remains environment-owned. |
| Slow connections | Degraded availability, offline/error/retry states, and bounded long-running status contracts | Automated contract passed; network throttling against a deployed service was not performed. |
| Long-running operations | Streaming controls, status messaging, retry/recovery, and performance measurement contracts | Automated contract passed; production-duration and cancellation behavior require deployment smoke tests. |

The result is a **completed-local contract validation**, not a claim of universal accessibility conformance. Manual assistive-technology, Windows High Contrast, high-zoom, device, throttled-network, and production-duration checks remain explicit release gates for a platform owner. No credentials, personal data, external services, or destructive actions were used.
