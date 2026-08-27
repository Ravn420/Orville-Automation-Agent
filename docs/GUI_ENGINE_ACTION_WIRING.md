# GUI-to-engine action wiring

## Purpose

This document records how `windows_gui.py` connects user-facing controls to the authenticated local Orville API. The GUI uses `OrvilleWindow._request` or `_manager_request`, which send the configured bearer token only to the local API base URL and render bounded, redacted responses.

## Action map

| GUI action | Engine request | Behavior |
| --- | --- | --- |
| Create run | `POST /api/v1/objectives` | Submits the objective and receives a `run_id`. |
| Execute/resume/retry run | `POST /api/v1/objectives/{run_id}/execute` with `{"context":{"stream":true}}` | Starts or resumes the engine-owned run; retry reuses the same idempotent lifecycle entry point. |
| Pause monitor | Local UI state only | Stops polling. It does **not** claim to pause backend execution because the current engine has no run-pause route. |
| Cancel run | `POST /api/v1/runs/{run_id}/cancel` | Persists a cancellation request in the engine checkpoint. |
| Approve task | `POST /api/v1/runs/{run_id}/tasks/{task_id}/approval` with `{"approved":true}` | Approves the selected waiting task; the engine remains responsible for subsequent execution. |
| Load checkpoint | `GET /api/v1/runs/{run_id}` | Reads the persisted run/checkpoint projection. |
| Review verification | `GET /api/v1/runs/{run_id}` | Reads the persisted verification context and task outcomes for the review view. |
| List artifacts | `GET /api/v1/artifacts` | Reads the bounded artifact catalog for the context and execution-monitor views. |

## Safety and compatibility rules

The shared `build_engine_action_request` helper rejects unknown actions and missing run/task identifiers, URL-encodes path identifiers, and uses only the routes present in the current API. GUI responses are passed through the existing display redaction and bounded rendering functions. No credentials, prompts, local paths, or raw event payloads are written to the interface.

Checkpoint and verification are intentionally read projections rather than client-owned mutations. Approval, cancellation, and execution requests are sent to the engine, which owns lifecycle transitions and persisted state. The current engine has no first-class backend pause or verification mutation route. A future route can be added without changing the action-builder boundary.

## Validation

Run:

```text
python -m pytest tests/test_gui_action_wiring.py tests/test_gui_backend_bridge.py tests/test_gui_engine_api_contract.py -q
python -m py_compile windows_gui.py tests/test_gui_action_wiring.py
```

The tests verify the complete requested action set, route and payload mappings, URL encoding, and rejection of incomplete or unsupported requests.
