# M12.18 Blackbox Developer-Support Request and Verification Plan

**Document status:** Prepared—awaiting source-owner and external-send approval
**Milestone:** M12.18
**Owners:** Research Agent and Governance Agent
**Source task:** `TASK_GRAPH.md` M12.18 (`blocked-external`)
**Author:** Manus AI
**Prepared:** 2026-08-27

## 1. Purpose and current disposition

M12.18 requires a provider-confirmed answer about the supported Blackbox developer-access path and its operational boundaries. The repository’s public documentation review is not sufficient to close this task. No support request has been sent from this workflow, and no provider-side claim should be treated as verified until a response is received through an approved channel and independently checked.

The existing project contract uses an Orville-managed relay by default. The desktop application must not contain the managed provider credential, and the user-connected path must not assume an OAuth or device flow that the provider has not documented. This request therefore asks only for documentation and policy confirmation; it does not include credentials, private project files, browser cookies, test prompts containing personal data, or a request to change an account.

## 2. Approval and scope gate

Before sending, record the source-owner approval, the approved sender identity, the provider support channel, the data classification, and the exact request version. Sending the draft below is an external communication and requires its own approval checkpoint. Do not send it through an undocumented endpoint or by copying a provider credential into a project artifact.

| Gate | Required input | Stop condition |
|---|---|---|
| S-01 Source owner | Named owner approves this exact request and recipient/channel | No approval or ambiguous scope |
| S-02 Provider destination | Official support portal or documented support address | Unverified destination |
| S-03 Sender authority | Authorized account or support identity | Personal/unauthorized account |
| S-04 Data minimization | No secrets, private keys, customer data, cookies, or unpublished payloads | Sensitive content present |
| S-05 Request version | Hash or immutable copy of the final text | Text changes after approval |
| S-06 External-action checkpoint | Single-use approval ID, target, scope, and expiry | Missing, expired, or mismatched checkpoint |

## 3. Formal support request draft

Send only the text inside the following block after completing S-01 through S-06. Replace bracketed metadata before sending, but do not add secrets or private operational data.

```text
Subject: Request for documented Blackbox developer access, OAuth/device flow, and relay requirements

Hello Blackbox Developer Support,

We are evaluating a desktop application integration that uses a server-side relay boundary for Blackbox access. We need authoritative documentation so that we do not implement an unsupported authentication or account-connection path.

Please answer the following questions for the current Blackbox developer platform and terms:

1. Does Blackbox provide an officially supported third-party OAuth 2.0, device-authorization, or equivalent user-delegated authorization flow for an application such as ours? If yes, please provide the official documentation, required scopes, consent behavior, redirect requirements, token lifetime/rotation rules, and revocation behavior.
2. If no such flow is supported, is the documented integration limited to bearer API-key authentication? Please identify the supported credential ownership model and whether a server-side relay is permitted.
3. May a relay service invoke Blackbox on behalf of an authenticated application user? If so, please specify tenant/account attribution, quota and rate-limit behavior, abuse controls, audit obligations, data-processing terms, and required user disclosure.
4. What provider-side data-retention, training-use, deletion, regional-processing, and incident-notification rules apply to API prompts, responses, uploaded files, and logs? Please distinguish API traffic from any web application session.
5. What are the supported endpoints, model-discovery methods, streaming/cancellation behavior, retry guidance, error semantics, and compatibility guarantees for production integrations?
6. Are there restrictions on storing provider credentials in an application-managed secret store, and what rotation/revocation process does Blackbox recommend?
7. Which support or developer terms must an integrator accept before enabling production traffic, and where is the authoritative version of each term maintained?

Please reply with links to current official documentation or a support case reference for each answer. If a requested capability is not supported, please state that explicitly. We are not requesting account changes, credential handling, quota changes, or provider-side actions as part of this inquiry.

Application context: Orville, a desktop automation application with a server-side relay boundary.
Request version: [immutable request ID/hash]
Requester organization/account: [approved non-secret identifier]
Date: [UTC timestamp]

Thank you,
[authorized sender]
```

## 4. Evidence inventory

Capture only provider-safe metadata. Preserve the original response in the approved evidence store with access controls; use the sanitized summary in the repository. Do not commit a private support transcript if it contains personal data, account identifiers, private URLs, credentials, or confidential provider material.

| Evidence ID | Evidence | Required record |
|---|---|---|
| M12.18-E01 | Source-owner approval | Approver, timestamp, request version, scope |
| M12.18-E02 | Destination validation | Official channel URL or case system, access method, validation date |
| M12.18-E03 | Sent-request receipt | Case ID or receipt, timestamp, request hash |
| M12.18-E04 | Provider response | Response ID/date, source URL or case reference, redacted copy location |
| M12.18-E05 | Claim matrix | Each question, answer, confidence, citation/reference, unresolved point |
| M12.18-E06 | Independent review | Reviewer, comparison against repository contract, discrepancies |
| M12.18-E07 | Decision record | Supported/unsupported/unclear decision, owner, follow-up, expiry |

## 5. Verification plan

### 5.1 Authenticate the evidence source

Confirm that the response came through the approved provider channel and that its case ID, sender identity, timestamp, and referenced documentation are visible. Do not treat a pasted answer, an unsourced screenshot, a search snippet, or a generic community post as authoritative confirmation.

### 5.2 Build the claim matrix

Map each provider answer to the exact question, the relevant Orville contract, the cited source, and the implementation consequence. Mark every answer as `confirmed`, `contradicted`, `partially confirmed`, or `unanswered`. A missing answer does not count as confirmation.

| Claim area | Orville decision to verify | Closure rule |
|---|---|---|
| OAuth/device flow | Whether `user_connected` may use a provider-delegated flow | Confirmed only with official flow and scope documentation |
| API-key path | Whether server-side bearer-key relay is allowed | Confirmed only with credential and relay terms |
| Account attribution | How usage, quota, and tenant identity are attributed | Must name the authoritative identity model |
| Data handling | Retention, training use, deletion, and region behavior | Must distinguish API from web-session behavior |
| Runtime contract | Endpoints, models, streaming, cancellation, retry, errors | Must provide current developer references |
| Credential lifecycle | Storage, rotation, and revocation requirements | Must not require client-side secret exposure |
| Production terms | Required agreements and restrictions | Terms version and owner recorded |

### 5.3 Independent reconciliation

The Governance Agent compares the response with `BLACKBOX_INTEGRATION.md`, `BLACKBOX_INTEGRATION_RESEARCH.md`, `APPROVAL_CHECKPOINTS.md`, and the current readiness report. The Research Agent checks that every provider citation resolves, is current, and actually supports the mapped claim. Any contradiction keeps M12.18 blocked until the provider clarifies it.

### 5.4 Decision outcomes

Use one of four outcomes. `Confirmed` means the provider’s current authoritative response closes the named question. `Unsupported` means the provider explicitly denies the capability; the repository must retain the safer fallback. `Partially confirmed` means only a subset may be implemented and the remainder stays blocked. `Unanswered` means no status change is permitted.

## 6. Safe repository update after verification

If the provider confirms an API-key-only path, retain the current design: server-side relay credential, redacted client status, no undocumented browser session, and protected user-connected credential storage. If an official OAuth/device flow is confirmed, create a separate change proposal for the exact scopes and token lifecycle; do not silently change the implementation during M12.18 verification.

Update `TASK_GRAPH.md`, `STATE.md`, and `TODO.md` only after the claim matrix and independent review are complete. The update must include the evidence reference, decision, reviewer, response date, and any remaining scope. A response that changes the architecture or legal/data-handling posture requires a new design and approval review.

## 7. Stop conditions

Stop before sending if the support destination cannot be verified, the request contains secrets or personal data, the provider requires an unsupported login handoff, the response conflicts with current terms, or the source-owner approval has expired. Stop before closing M12.18 if the response is unsourced, incomplete, stale, or not specific to the developer surface being evaluated.

## References

- [`TASK_GRAPH.md`](../TASK_GRAPH.md), M12.18 blocker and owner.
- [`BLACKBOX_INTEGRATION.md`](BLACKBOX_INTEGRATION.md), current access modes and credential boundary.
- [`BLACKBOX_INTEGRATION_RESEARCH.md`](BLACKBOX_INTEGRATION_RESEARCH.md), existing public-documentation research record.
- [`APPROVAL_CHECKPOINTS.md`](APPROVAL_CHECKPOINTS.md), external-message approval and evidence controls.
- [`READINESS_REPORT.md`](READINESS_REPORT.md), current provider and production-readiness boundaries.

_Last updated by Manus AI._
