# Browser Session Lifecycle Contract

**Project:** Orville  
**Roadmap item:** `TODO-effd7a331bf6`  
**Updated:** 2026-08-28  
**Owner:** Orchestration Agent

## Scope and safety boundary

Orville browser operation is a local, optional adapter. It must remain usable without a managed browser service and must fail closed when the optional runtime, paired session, domain policy, or approval record is unavailable. The adapter does not store passwords or cookies and does not infer approval from a generic request to continue.

## Lifecycle states

| State | Meaning | Allowed transition |
|---|---|---|
| `created` | A session has an identifier and normalized domain policy but no browser handle | `active` after approved navigation, `user_takeover` after approved takeover, or `closed` |
| `active` | An approved local browser handle is operating within the allowlist | `user_takeover`, `recovered`, or `closed` |
| `user_takeover` | A visible browser is available for a user-approved handoff | `active`, `recovered`, or `closed` |
| `recovered` | Persistent metadata was loaded or a process restarted; browser handles are not trusted | `user_takeover` or `closed` only after explicit approval/restart |
| `closed` | The session is terminal and must not execute new actions | No transition |

A normal process shutdown closes browser handles and persists only sanitized session metadata. Recovery never silently reopens a browser, replays a form, resubmits a download, or repeats an external side effect.

## Domain allowlist

The allowlist contains hostnames only. Domain values are normalized to lowercase, trailing dots are removed, and schemes, paths, ports, credentials, wildcards, and malformed characters are rejected. A URL is allowed only when it uses `http` or `https`, has a hostname, and matches an exact allowlisted hostname or a subdomain of it. The adapter must reject lookalike suffixes such as `notexample.com` when only `example.com` is allowed.

All navigation, extraction, screenshot, download, form, and takeover actions are associated with the session policy. A redirect or requested follow-up URL must be checked against the same policy before the operation continues.

## Approval and takeover

Read-only session creation and policy validation may be prepared locally. Navigation, form submission, downloads, visible takeover, release of takeover, and any action with an external side effect require an explicit approval record. The approval record must identify the session, action, target or domain, scope, requester, approver, timestamp, and expiry. Approval is single-use for destructive or externally visible operations unless the workflow explicitly defines a bounded repeated scope.

Without approval, the adapter returns a safe `takeover_required` or approval-required state and records the request; it must not launch a browser, submit data, download a file, or contact a remote URL. User takeover means visible control is offered to the user; it is not a mechanism for bypassing login, CAPTCHA, access controls, or domain policy.

## Audit contract

Every lifecycle and action decision records a bounded audit event containing a timestamp, safe event name, session identifier, and sanitized detail. Required events include session creation, recovery, shutdown, closure, allowlist rejection, approval request, approval acceptance, action dispatch, action rejection, and takeover transitions. Audit records must exclude passwords, cookies, authorization headers, tokens, prompts, form values, full downloaded content, and unredacted tool payloads.

The audit trail is evidence of the local decision, not proof that a remote service accepted or completed an action. Remote response status, delivery failure, and task outcome must remain separately represented.

## Failure and recovery rules

Missing Playwright, invalid allowlists, expired sessions, inactive sessions, invalid relay secrets, unsupported actions, disallowed URLs, and missing approval all fail closed with a stable error class or user-facing status. Retry must be bounded and idempotency-aware. A failed action must not be automatically replayed when its external side effect is uncertain; recovery requires inspection and a new approval where needed.

## Repository evidence

The implementation references for this contract are [`orville_core/browser.py`](../orville_core/browser.py) and [`orville_core/browser_relay.py`](../orville_core/browser_relay.py). The corresponding assertions are in [`tests/test_browser.py`](../tests/test_browser.py), [`tests/test_browser_relay.py`](../tests/test_browser_relay.py), and [`tests/test_browser_session_lifecycle_contract.py`](../tests/test_browser_session_lifecycle_contract.py). This document does not claim that a real browser runtime, user login, CAPTCHA handoff, external connector, or production deployment was exercised.

## References

[1]: ../orville_core/browser.py "Orville browser session adapter"

[2]: ../orville_core/browser_relay.py "Orville local browser relay policy"

[3]: ../AGENTS.md "Orville Repository Operating Rules"
