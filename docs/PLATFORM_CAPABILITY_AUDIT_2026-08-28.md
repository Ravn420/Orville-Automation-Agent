# Platform Capability Audit

**Project:** Orville  
**Audit date:** 2026-08-28  
**Roadmap item:** `TODO-14b1a51a18bc`  
**Scope:** Browser adapter, security policy, API initialization, and GUI capability status  
**Owner:** Orchestration Agent

## Executive finding

The current repository has explicit local implementations for all four audited areas. The browser path is fail-closed and approval-gated; the security boundary is enforced through allowlists, authentication, redaction, and bounded local state; API initialization is local-first and provider-neutral; and GUI status helpers map degraded or unavailable dependencies to user-facing states and recovery actions. The audit does **not** claim live external browser, provider, connector, production, or telemetry-vendor operation.

## Findings

| Area | Evidence reviewed | Finding | Residual limitation |
|---|---|---|---|
| Browser adapter | `orville_core/browser.py`, `orville_core/browser_relay.py`, browser tests and `browser_extension/` | Browser sessions validate HTTP(S) URLs against normalized domain allowlists, require approval for navigation/forms/downloads/takeover, avoid storing passwords/cookies, record bounded audit events, and recover sessions as requiring explicit restart approval. The relay separately authenticates paired sessions with expiring hashed secrets and allowlisted actions. | Playwright is optional and no managed browser session is claimed. A real browser, login, CAPTCHA, or takeover flow requires explicit user participation and local installation/configuration. |
| Security policy | `orville_core/security.py`, connector/browser policy modules, `AGENTS.md`, redaction helpers | Security decisions are local and fail-closed: secrets are not intended for source control or UI display, browser domains/actions are allowlisted, external side effects require approval, and local path/payload presentation is bounded and redacted. | A repository audit cannot prove production TLS, identity-provider configuration, secret-manager rotation, or external audit-sink delivery. Those remain deployment-owned. |
| API initialization | `orville_core/api.py`, provider/configuration modules, API and health tests | The application is initialized as a local FastAPI service with authenticated routes, local health/capability projections, provider-neutral adapters, and optional integrations. It can operate without Manus-specific services when a local provider or deterministic test backend is used. | Live cloud providers, external connectors, production CORS allowlists, and deployment secrets are environment-specific and are not exercised by this audit. |
| GUI capability status | `orville_core/gui_state.py`, `windows_gui.py`, accessibility/status tests | The GUI uses stable user-facing states such as empty, offline, blocked, failed, partial, long-running, ready, and dependency-unavailable states. Messages include explanations and recovery actions instead of relying on raw provider errors or color alone. | The desktop GUI cannot assert availability of an optional provider, browser runtime, connector, or OTLP endpoint until that dependency passes local preflight. |

## Acceptance checks

The audit acceptance boundary is satisfied when the repository contains a traceable implementation reference for each area, explicit limitations, and focused tests that prevent false claims. The following checks are the reproducible local audit commands:

```powershell
python -m pytest tests/test_platform_capability_audit.py -q
python -m pytest tests/test_browser.py tests/test_security_hardening.py tests/test_api.py tests/test_gui_state.py -q
python -m compileall -q orville_core windows_gui.py
```

The broader command may include unrelated baseline failures; such failures must be recorded separately and must not be silently attributed to the audited capability boundary.

## Security and privacy boundary

No credential, token, cookie, personal data, production endpoint, browser login, external connector invocation, or destructive operation was used for this audit. Evidence references source files and local tests only. Any future live browser or production audit requires a separately approved environment-specific test plan.

## Follow-up actions

Before a production readiness claim, the deployment owner should verify TLS termination, identity-provider and scoped authorization configuration, CORS allowlists, secret injection/rotation, an audit-log sink, Playwright installation and browser-session handoff, provider preflight, and a representative packaged Windows smoke test. These are follow-up deployment checks, not inferred from this repository-only audit.

## References

[1]: ../orville_core/browser.py "Orville browser session adapter"

[2]: ../orville_core/browser_relay.py "Orville local browser relay policy"

[3]: ../orville_core/gui_state.py "Orville GUI presentation-state helpers"

[4]: ../orville_core/api.py "Orville local API initialization"

[5]: ../AGENTS.md "Orville Repository Operating Rules"
