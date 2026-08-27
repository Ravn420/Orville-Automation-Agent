# Real-time execution events

Orville exposes authenticated execution-event delivery through a stable polling endpoint and a resumable Server-Sent Events (SSE) endpoint. The contract is local-first, bounded, and compatible with GUI clients without requiring a WebSocket runtime.

## Endpoints

| Delivery mode | Endpoint | Contract |
|---|---|---|
| Polling | `GET /api/v1/runs/{run_id}/events` | Returns `{ "run_id": ..., "events": [...] }` from the latest checkpoint. The client may poll with bounded backoff while a run is active. |
| SSE | `GET /api/v1/runs/{run_id}/events/stream` | Returns `text/event-stream`; each event includes an SSE `id` equal to its monotonic sequence and a JSON `data` payload. |
| Run state | `GET /api/v1/runs/{run_id}` | Returns the current checkpoint and lifecycle state for reconciliation after reconnect or missed events. |

All endpoints require the same exact bearer authentication as the GUI backend bridge. Missing or invalid credentials are rejected before run data is returned.

## SSE resume behavior

The client stores the last received numeric event ID and reconnects with either `Last-Event-ID: <sequence>` or `?last_event_id=<sequence>`. The server emits only events whose sequence is greater than the cursor, preventing duplicate delivery after reconnect. Events are emitted in sequence order. The stream ends after the run reaches a terminal state and no new event remains, or after the bounded idle limit is reached.

A client should reconcile with the polling endpoint or run checkpoint after reconnect, treat event data as untrusted data, and tolerate a lost connection. The client must not infer authorization, approval, completion, or external side effects from an event alone; those states must be verified against the run checkpoint and applicable approval contracts.

## GUI handling rules

1. Start with polling or SSE after receiving a run ID from the execution endpoint.
2. Render sanitized event fields and correlation identifiers; do not display secrets, raw authorization headers, or unredacted provider payloads.
3. Use the monotonic sequence as the deduplication key and retain the last cursor only in local protected state.
4. On `401`, stop and request authentication recovery. On `404`, stop because the run is unavailable. On disconnect, reconnect with the last cursor using bounded backoff.
5. On terminal run state, perform one final checkpoint reconciliation and close the stream.

## Verification

Run the focused contract checks with:

```powershell
python -m unittest tests.test_realtime_execution_events -v
python -m py_compile orville_core\api.py tests\test_realtime_execution_events.py
```

These checks are local and do not contact a provider, browser session, account, or external endpoint. Live deployment checks remain covered by the deployment smoke-test procedure.
