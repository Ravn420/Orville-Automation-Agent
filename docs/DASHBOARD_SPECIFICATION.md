# Orville Operational Dashboard

## Purpose

The desktop control center now includes a compact operational dashboard above the task workspace. It summarizes **active tasks**, **recent runs**, **model availability**, **system health**, **failures**, and **generated artifacts** without changing the existing API contracts or displaying raw payloads.

## Card contract

| Card | Existing source | Display |
|---|---|---|
| Active tasks | `GET /api/v1/state` | Count of `tasks` or `active_tasks`. |
| Recent runs | `GET /api/v1/state` | Count of `runs` or `recent_runs`. |
| Model availability | `GET /api/v1/providers` | Count of returned providers. |
| System health | `GET /api/v1/health` | `ONLINE` only for `status=ok`; otherwise `CHECK`. |
| Failures | `GET /api/v1/state` | Count of `failures` or `errors`. |
| Generated artifacts | `GET /api/v1/artifacts` | Count of returned artifacts. |

The dashboard uses aggregate values only. It does not render provider configuration, bearer tokens, exception text, task payloads, or artifact contents. A request failure produces a bounded `—` value for unavailable collections and `CHECK` for health; raw exception strings are not displayed.

## Behavior

The dashboard is built as a responsive six-card grid in the existing Tkinter workspace. It refreshes after the window is initialized and through an explicit **Refresh dashboard** control. Requests run on a daemon worker thread with a five-second timeout so the UI event loop remains responsive. The dashboard uses the existing bearer-token route access and does not introduce new credentials, routes, persistence, or dependencies.

The existing task composer, conversation output, context panel, provider manager, API documentation action, and exit behavior remain intact. At compact widths, the dashboard cards reflow with the existing workspace layout; the context panel and sidebar continue to follow their established thresholds.

## Validation and limitations

`tests/test_dashboard.py` validates required cards and routes, both supported state payload shapes, safe degraded values, and source-level exclusion of raw dashboard errors. `python -m py_compile windows_gui.py tests/test_dashboard.py` verifies syntax. The current dashboard is a desktop Tkinter implementation; web/mobile dashboards and live visual regression remain future work. Provider availability is represented by registered provider count, not a live health check for each provider.
