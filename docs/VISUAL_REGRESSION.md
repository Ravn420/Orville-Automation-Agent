# Visual Regression Checks

## Scope

Orville uses a deterministic, source-controlled visual-regression baseline for the design system and the canonical control-center mockup. The check fingerprints reviewed design tokens and stable semantic markup rather than depending on a browser session, external provider, credential, or platform-specific screenshot renderer.

## Covered assets

| Asset | Coverage |
|---|---|
| `config/design-system.example.json` | Typography, color-role keys, spacing, responsive breakpoints, and motion tokens. |
| `docs/mockups/orville-control-center.html` | Semantic tag sequence, roles, ARIA labels, theme/status markers, responsive breakpoints, and reduced-motion marker. |
| `tests/fixtures/visual_regression_baseline.json` | Versioned reviewed schema, design hash, structure hash, and normalized evidence used for comparison. |

The canonical mockup represents the critical home/control-center screen: navigation, top bar, metric cards, recent-projects content, and context rail. The baseline also covers light/dark theme behavior, compact breakpoints, pressed-state semantics, and reduced-motion support through stable markers.

## Reproducible commands

From the repository root, run:

```text
python tools/visual_regression.py check
python -m unittest tests.test_visual_regression -v
```

The checker returns success only when the current snapshot exactly matches the committed baseline. A changed design token or critical-screen marker fails closed and prints that the baseline requires explicit review and update. To inspect the candidate snapshot without changing the baseline, run `python tools/visual_regression.py snapshot`.

## Baseline review policy

A baseline update is a reviewed fixture change, not an automatic test repair. The reviewer must confirm that the visual change is intentional, preserves accessibility and responsive requirements, does not expose secrets, and updates the documented evidence. The baseline must remain JSON, deterministic, bounded, and free of generated caches or credentials.

The current fixture was generated from source revision `62e8df0` using `python tools/visual_regression.py snapshot`. Its file SHA-256 is `a30f0f53da5df610e5206768795636a773ef7c5bda2c723ffd07931184820ebd`. Generated comparison outputs may remain under ignored `artifacts/`; the required baseline input must remain versioned under `tests/fixtures/`.

## Limitations

This local check detects structural and token drift but does not claim pixel-perfect equivalence across operating-system font rendering, display scaling, browser engines, or native Tkinter themes. Screenshot comparison, assistive-technology review, and web/mobile critical-screen baselines remain environment-dependent follow-up gates.
