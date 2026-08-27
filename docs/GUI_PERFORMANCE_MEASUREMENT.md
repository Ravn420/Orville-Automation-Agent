# GUI Performance Measurement Contract

## Scope

This contract defines a repeatable local benchmark for the native Tkinter GUI boundary. It measures module startup, representative interaction logic, peak traced Python memory, and serialization of a fixed large task graph and artifact collection.

The benchmark uses **1,000 tasks and 500 artifacts** so regressions are visible without requiring external services or a production account. It does not create a window, contact providers, read credentials, or mutate project data.

## Measurements and acceptance thresholds

| Measurement | Method | Acceptance threshold |
|---|---|---:|
| Startup time | Fresh subprocess importing `windows_gui` | ≤ 2,500 ms |
| Interaction latency | Twenty repetitions of state classification, dependency classification, and safe status-message lookup | ≤ 200 ms average per repetition |
| Peak memory | `tracemalloc` around the representative workload and serialization | ≤ 64 MiB |
| Large collections | Fixed 1,000-task graph plus 500-artifact collection | Workload completes and all checks pass |

These thresholds are **local release gates**, not universal hardware guarantees. Record the operating system, Python version, commit, workload sizes, and measured values when comparing runs.

## Usage

From the repository root, run:

```powershell
python tools\measure_gui_performance.py --tasks 1000 --artifacts 500 --output docs\GUI_PERFORMANCE_BASELINE.json
```

The command exits with status `0` only when startup, interaction, and memory gates pass. It emits JSON suitable for CI artifacts. Repeat on the slowest supported target before release; compare medians across multiple runs when investigating a regression.

## Interpretation and limitations

The interaction workload measures pure GUI-adjacent state handling rather than human input, window painting, disk I/O, or network latency. Tkinter import startup is measured, but window creation is intentionally excluded because it requires a display and can be platform-specific. A future platform-specific UI test may extend this contract without weakening these offline checks.

## Validation

`tests/test_gui_performance_measurement.py` verifies fixed workload sizing, required output fields, threshold enforcement, and CLI argument bounds. The checked-in baseline records the successful Windows-target run used to complete this item.
