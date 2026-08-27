# Orville Execution Monitor

## Purpose

The desktop execution monitor provides a bounded view of a persisted run. It combines live polling of run checkpoints with event history so operators can review progress, logs, agent activity, tool calls, elapsed time, and lifecycle controls without exposing raw payloads or secrets.

## Monitor surfaces

| Surface | Source | Rendering rule |
|---|---|---|
| Live progress | `GET /api/v1/runs/{run_id}` | Shows run status, task count, task ID, task status, and attempts. |
| Logs and events | `GET /api/v1/runs/{run_id}/events` | Shows timestamp, task ID, and event type for the most recent 80 events. Event detail values are not rendered. |
| Agent activity | Persisted event `task_id` and `event_type` | Identifies the executing task and lifecycle transition without dumping context. |
| Tool calls | Persisted event types | Shows the event classification only; tool arguments and outputs remain outside the monitor. |
| Elapsed time | Event timestamps in the run checkpoint | Derives a bounded duration from the earliest and latest parseable timestamps. |

## Controls

**Pause monitor** stops polling and changes only the observation loop; it does not claim to pause a running backend handler. **Resume monitor** restarts observation. **Resume waiting task** approves the first task with `waiting_approval` status through the existing approval endpoint. **Retry run** invokes the existing objective execution route and remains subject to task retry limits. **Cancel run** requests durable cancellation through the existing cancellation endpoint; the engine applies it at an execution boundary.

The monitor polls every 1.5 seconds and each request has an eight-second client timeout through the existing manager request helper. It renders at most 80 event rows and uses a bounded text view. If a run cannot be loaded, it displays a generic recovery message rather than an exception, URL, payload, or credential.

## Safety and accessibility

Run IDs are URL-encoded before requests. The monitor uses the existing bearer-token boundary and introduces no credential entry. Raw event details, task outputs, exception strings, and provider configuration are not displayed. The window has a 760 px minimum width, keyboard-addressable controls, readable status text, and a text fallback for all event information.

## Validation boundary

`tests/test_execution_monitor.py` verifies the required monitor surfaces and control labels, persisted event coverage, bounded event rendering, elapsed-time support, and safe unavailable-run messaging. Runtime streaming, exact provider tool semantics, hard handler interruption, and web/mobile parity remain deployment or future-engine responsibilities.
