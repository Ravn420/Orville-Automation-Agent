# Visual Regression Checks

## Scope

Orville uses a deterministic, source-controlled visual-regression baseline for the design system and the canonical control-center mockup. The check fingerprints reviewed design tokens and stable semantic markup rather than depending on a browser session, external provider, credential, or platform-specific screenshot renderer.

## Covered assets

| Asset | Coverage |
|---|---|
| `config/design-system.example.json` | Typography, color-role keys, spacing, responsive breakpoints, and motion tokens. |
| `docs/mockups/orville-control-center.html` | Semantic tag sequence, roles, ARIA labels, theme/status markers, responsive breakpoints, and reduced-motion marker. |
| `artifacts/visual_regression_baseline.json` | Reviewed schema version, design hash, structure hash, and normalized evidence used for comparison. |

The canonical mockup represents the critical home/control-center screen: navigation, top bar, metric cards, recent-projects content, and context rail. The baseline also covers light/dark theme behavior, compact breakpoints, pressed-state semantics, and reduced-motion support through stable markers.

## Reproducible commands

From the repository root, run:

```text
python tools/visual_regression.py check
python -m unittest tests.test_visual_regression -v
```

The checker returns success only when the current snapshot exactly matches the committed baseline. A changed design token or critical-screen marker fails closed and prints that the baseline requires explicit review and update. To inspect the candidate snapshot without changing the baseline, run `python tools/visual_regression.py snapshot`.

## Baseline review policy

A baseline update is a reviewed artifact change, not an automatic test repair. The reviewer must confirm that the visual change is intentional, preserves accessibility and responsive requirements, does not expose secrets, and updates the documented evidence. The baseline must remain JSON, deterministic, bounded, and free of generated caches or credentials.

## Current reviewed baseline

The baseline at `artifacts/visual_regression_baseline.json` was regenerated and reviewed on 2026-08-27 after verification of the current design-system token projection and canonical control-center semantic markers. It uses schema `1`, contains only deterministic hashes and normalized local structural metadata, and was validated with `python tools/visual_regression.py check` and `python -m pytest -q tests/test_visual_regression.py`. No credentials, rendered screenshots, external resources, or generated caches are retained in the artifact.

## Limitations

This local check detects structural and token drift but does not claim pixel-perfect equivalence across operating-system font rendering, display scaling, browser engines, or native Tkinter themes. Screenshot comparison, assistive-technology review, and web/mobile critical-screen baselines remain environment-dependent follow-up gates.
