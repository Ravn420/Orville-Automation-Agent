# Orville GUI Redesign

## Summary

The existing `windows_gui.py` interface was redesigned in place as a premium, neutral, responsive Orville control center. The implementation preserves the existing Python/Tkinter framework, API bridge, authentication header behavior, routes, background request execution, validation, and workflow actions.

## Modified files

| File | Change |
|---|---|
| `windows_gui.py` | Replaced the former single-column control layout with a responsive three-pane workspace, refined styles, structured output presentation, composer controls, status states, and contextual tabs. |
| `GUI_REDESIGN_SUMMARY.md` | Documents the redesign, preserved behavior, verification, and run instructions. |

A safety copy of the original GUI is available as `windows_gui.py.pre-redesign.bak`.

## Interface changes

The interface now provides a narrow warm-gray navigation sidebar, a focused central task workspace, and a contextual panel with Preview, Files, Activity, and Details views. The sidebar preserves the existing operational actions through the workspace controls, while the central composer provides multiline objective entry, attachment/tool affordances, keyboard guidance, validation, and the existing objective submission action.

The visual system uses an off-white application background, white content surfaces, near-black primary text, muted secondary text, subtle borders, restrained violet accent treatment, medium rounded-equivalent framed surfaces, dark primary buttons, light secondary buttons, and compact status badges. API responses remain readable structured text rather than oversized chat bubbles.

Responsive behavior hides the contextual panel below approximately 980 pixels and the sidebar below approximately 790 pixels. The top-left menu control can toggle the sidebar when it is available.

## Preserved API behavior

The GUI continues to use the existing routes without backend changes:

| Existing action | Existing route | Method |
|---|---|---|
| Check Health | `/api/v1/health` | `GET` |
| Load State | `/api/v1/state` | `GET` |
| List Artifacts | `/api/v1/artifacts` | `GET` |
| Create Objective | `/api/v1/objectives` | `POST` |

Requests continue to include the configured bearer token and JSON content type. Requests remain asynchronous through daemon worker threads, and the API startup flow remains unchanged.

## Verification

The following checks completed successfully on the attached Windows project:

```text
python -m py_compile windows_gui.py
python -m unittest discover -s tests -v
Ran 114 tests in 5.922s
OK
```

The GUI was not launched interactively during verification because the attached environment is a source workspace rather than an active desktop display session. The module compiles successfully, and all repository tests pass.

## Run instructions

From the project root, configure the existing environment values as needed, then launch the GUI using the project's existing launcher or directly with:

```powershell
python windows_gui.py
```

The GUI starts the local API bridge using the existing `ORVILLE_API_HOST`, `ORVILLE_API_PORT`, and `ORVILLE_API_TOKEN` configuration behavior.

## Assumptions

This redesign targets the existing desktop Tkinter GUI identified at `windows_gui.py`. No new application, route, backend service, data model, authentication flow, or dependency was introduced.

## Next actions

For visual acceptance, launch the GUI on Windows and verify the 1240-pixel desktop layout, the compact layout below 980 pixels, the sidebar toggle below 790 pixels, objective submission, health/state/artifact actions, API documentation launch, and exit behavior.
