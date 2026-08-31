# Browser, Run, Artifact, and Shutdown Lifecycle Audit

**Roadmap item:** `TODO-2f13d5e2c921`  
**Audit date:** 2026-08-28  
**Scope:** Local standalone Orville runtime and Signal Room control plane

## Executive finding

The current implementation has explicit state and evidence boundaries for browser sessions, action dispatch, run events, artifact persistence, and process shutdown. Browser sessions persist sanitized metadata and recover into a non-operational state; action execution is policy and approval gated; run events are emitted through the local run manager; artifacts are stored under the configured checkpoint/artifact boundary; and the API registers browser shutdown cleanup with the application lifecycle. This audit validates those claims through focused tests and source inspection. It does not claim an external browser, production deployment, or remote artifact store was exercised.

## Audit matrix

| Area | Implementation evidence | Control finding |
|---|---|---|
| Browser sessions | `orville_core/browser.py` `BrowserSession` and `BrowserSessionManager` | Session IDs, allowlists, status, approval/takeover state, and bounded audit records are explicit. Persisted sessions recover as `recovered` and require explicit restart approval. |
| Action state | `BrowserSession.navigate`, form submission, download, and takeover paths | URL policy is checked before dispatch. Navigation and sensitive actions require explicit approval; missing optional runtime or invalid state fails closed. |
| Run events | `orville_core/api.py` run/event endpoints and `orville_core/observability.py` | Run lifecycle events and per-run metadata are represented separately from browser audit events, allowing outcome and tool/action evidence to be correlated without treating one as proof of the other. |
| Artifact storage | API checkpoint and artifact persistence paths; `artifacts/` retained evidence | Generated artifacts are associated with run/checkpoint evidence. Runtime data and disposable intermediates remain outside source-controlled evidence unless deliberately retained. |
| Shutdown lifecycle | `create_app` registers `browser_sessions.shutdown` on FastAPI shutdown | Browser handles are closed and session state is persisted during application shutdown. Shutdown does not replay pending external actions. |
| Audit records | Browser session audit list and API `/api/v1/browser/sessions/{session_id}/audit` projection | Lifecycle, approval, rejection, recovery, and shutdown decisions are observable with sanitized details; secrets and full payloads are excluded. |

## Required invariants

The audit treats the following as acceptance invariants. A session cannot navigate to a non-allowlisted hostname. A session created without explicit overrides is read-only and headless. A navigation request without approval remains pending rather than launching an action. A sensitive action cannot be authorized by an unrelated or malformed approval. A recovered session cannot silently reuse a browser handle. Shutdown is idempotent and does not erase retained audit evidence. Run events, browser audit events, and artifact metadata retain distinct ownership and meaning.

## Reproducible validation

Run from the repository root:

```powershell
python -m pytest tests/test_browser_run_artifact_shutdown_audit.py tests/test_browser_session_api.py tests/test_local_browser_session_adapter.py tests/test_browser.py tests/test_browser_relay.py tests/test_artifacts.py -q
python -m compileall -q orville_core windows_gui.py
 git diff --check
```

The focused audit suite recorded **18 passing tests** before the documentation-only assertion test was added; the final focused run must be recorded in the roadmap entry. Python compilation and `git diff --check` are required gates.

## Known limitations and risks

The audit does not verify a real Playwright installation, user login, CAPTCHA handoff, remote browser relay, production object store, or crash-consistent shutdown under power loss. The local API token protects the route boundary, while deployment identity, TLS, CORS, and external audit sinks remain environment-owned. Pending external side effects require operator inspection and a new approval rather than automatic replay.

## References

[1]: ../orville_core/browser.py "Orville local browser session implementation"

[2]: ../orville_core/api.py "Orville API lifecycle and event routes"

[3]: ../orville_core/observability.py "Orville per-run observability"

[4]: ../AGENTS.md "Orville repository operating rules"
