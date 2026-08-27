# M12.18 External Verification Message and Payload

**Document status:** Draft only — not sent
**Milestone:** M12.18 — Blackbox developer-support confirmation assessment
**Owner:** Research Agent and Governance Agent
**Source task:** `TASK_GRAPH.md` M12.18 (`blocked-external`)
**Prepared:** 2026-08-27

## 1. Send gate

This package is an external communication draft, not evidence of provider confirmation. It must not be sent until the source owner approves the exact text, the official provider support destination is verified, the sender is authorized, the payload hash is recorded, and a single-use external-action approval is granted. No credentials, cookies, private project files, personal data, or raw operational logs are included.

The requested response must be returned through the verified official developer-support channel. A community post, search snippet, unsourced screenshot, or copied response does not unblock M12.18.

| Gate | Required record | Current state |
|---|---|---|
| Source-owner approval | Approver, scope, request version | Not granted |
| Official destination | Verified support URL or case system | Not recorded |
| Authorized sender | Non-secret account/role reference | Not recorded |
| Payload hash | SHA-256 of the exact approved payload | Not recorded |
| External-action approval | Single-use approval ID, expiry, and scope | Not granted |
| Provider response | Case ID, timestamp, authoritative response | Not received |
| Independent verification | Claim matrix and reviewer record | Not started |

## 2. Formal verification message

**Subject:** Request for authoritative Blackbox developer-integration verification for Orville

```text
Hello Blackbox Developer Support,

We are evaluating a desktop automation application named Orville that uses a server-side relay boundary for Blackbox access. We are requesting authoritative developer-platform confirmation so that we do not implement an unsupported authentication, account-connection, or provider-invocation path.

Please answer the following questions for the current Blackbox developer platform and applicable developer terms. Please include a link to the current official documentation or a support-case reference for every answer, and explicitly state when a capability is not supported.

1. Does Blackbox provide an officially supported third-party OAuth 2.0, device-authorization, or equivalent user-delegated authorization flow for an application such as Orville? If yes, please provide the official flow documentation, required scopes, consent behavior, redirect requirements, token lifetime and rotation rules, revocation behavior, and restrictions on desktop applications.

2. If no delegated authorization flow is supported, is the documented integration limited to bearer API-key authentication? Please identify the supported credential-ownership model and whether a server-side relay may invoke Blackbox on behalf of an authenticated application user.

3. If a relay is permitted, please specify the required tenant or account attribution, quota and rate-limit behavior, abuse controls, audit obligations, user disclosures, and whether provider-side approval is required before production traffic.

4. What provider-side rules apply to API prompts, responses, uploaded files, and operational logs concerning retention, training use, deletion, regional processing, subprocessors, and incident notification? Please distinguish API traffic from any web-application session.

5. What endpoints, model-discovery methods, streaming and cancellation behavior, retry guidance, error semantics, and compatibility guarantees are supported for production integrations? Please identify any endpoint- or account-plan-specific restrictions.

6. Are there restrictions on storing provider credentials in an application-managed protected secret store? Please provide the recommended rotation, revocation, and disconnect procedure and clarify whether provider credentials may ever be exposed to the desktop client or browser.

7. Which developer, commercial, privacy, acceptable-use, or data-processing terms must an integrator accept before enabling production traffic? Please provide the authoritative version and effective date of each applicable term.

Our current safety posture is conservative: no undocumented browser-session automation, no client-side provider secret, and no production traffic until the provider contract is confirmed. We are not requesting account changes, quota changes, credential handling, or provider-side actions as part of this inquiry.

Application context: Orville, a desktop automation application with a server-side relay boundary.
Request ID: [approved-request-id]
Request version/hash: [sha256]
Requester organization/account: [approved non-secret identifier]
Support case or destination: [verified official destination]
Date: [UTC timestamp]

Thank you,
[authorized sender]
```

## 3. Sanitized structured payload

The payload below is intended for an approved support form or documented API only. It is not an instruction to call an undocumented endpoint. Replace bracketed metadata only after approval and recompute the hash of the exact final body.

```json
{
  "request_type": "developer_integration_verification",
  "request_id": "[approved-request-id]",
  "request_version": "[sha256-of-final-message]",
  "product": "Orville",
  "integration_surface": "Blackbox developer platform",
  "application_type": "desktop automation application",
  "architecture": "server-side relay boundary",
  "questions": [
    "official third-party OAuth, device authorization, or equivalent delegated flow",
    "API-key authentication and credential ownership",
    "server-side relay permission, attribution, quotas, rate limits, and audit obligations",
    "API data retention, training use, deletion, regional processing, and incident notification",
    "supported endpoints, model discovery, streaming, cancellation, retries, errors, and compatibility",
    "protected credential storage, rotation, revocation, and disconnect requirements",
    "developer, commercial, privacy, acceptable-use, and data-processing terms"
  ],
  "safety_constraints": {
    "no_credentials": true,
    "no_cookies": true,
    "no_personal_data": true,
    "no_private_project_files": true,
    "no_production_traffic": true,
    "no_account_changes_requested": true,
    "no_undocumented_endpoint": true
  },
  "requested_response": {
    "authoritative_links_required": true,
    "support_case_reference_required": true,
    "unsupported_capabilities_must_be_explicit": true,
    "effective_date_required_for_terms": true
  },
  "destination": "[verified-official-support-channel]",
  "sender_reference": "[authorized-non-secret-sender-reference]",
  "submitted_at_utc": "[timestamp]"
}
```

## 4. Verification and unblock procedure

After an authorized send, retain the case receipt, request hash, destination, sender reference, and timestamp as evidence. Authenticate the response source, then build a claim matrix that maps each question to the exact answer, official citation, confidence, repository contract, and implementation consequence.

The Research Agent must confirm that every cited source is official, current, and directly supports the claim. The Governance Agent must reconcile the response against `BLACKBOX_INTEGRATION.md`, `BLACKBOX_INTEGRATION_RESEARCH.md`, `APPROVAL_CHECKPOINTS.md`, and the current readiness report. Any contradiction, missing answer, stale term, or unsupported source keeps M12.18 blocked.

M12.18 may be reclassified only after the provider response and independent review produce one of these explicit outcomes: `confirmed`, `unsupported`, `partially confirmed`, or `unanswered`. `Unsupported` closes only the specific capability question and must preserve Orville's safer fallback; it does not authorize an undocumented implementation.

## References

- [`TASK_GRAPH.md`](../TASK_GRAPH.md), current M12.18 blocker and owner.
- [`M12_18_BLACKBOX_DEVELOPER_SUPPORT_REQUEST_AND_VERIFICATION.md`](M12_18_BLACKBOX_DEVELOPER_SUPPORT_REQUEST_AND_VERIFICATION.md), approval gates and evidence plan.
- [`BLACKBOX_INTEGRATION.md`](BLACKBOX_INTEGRATION.md), current credential and relay boundary.
- [`APPROVAL_CHECKPOINTS.md`](APPROVAL_CHECKPOINTS.md), external-action approval rules.
- [`READINESS_REPORT.md`](READINESS_REPORT.md), current production-readiness boundaries.

_Last updated by Manus AI._
