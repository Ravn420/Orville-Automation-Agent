# Orville Blackbox Integration Research

**Project:** Orville  
**Research date:** 2026-08-26  
**Purpose:** Determine what is required for Orville to work without Blackbox credentials by default while supporting an optional Blackbox connection.

## Executive Finding

Orville can provide credential-free operation only by using its own local execution path or another explicitly configured local provider. Blackbox should be implemented as an optional provider. The reviewed official Blackbox documentation requires API-key authentication for programmatic API and Agent API access. The reviewed CLI documentation also requires account configuration and API-key setup before first use.

A normal Blackbox website sign-in must not be treated as equivalent to API authorization. No official third-party OAuth or device-authorization flow was identified in the reviewed public documentation. Orville should implement an OAuth/device flow only after Blackbox documents one for third-party applications. Until then, the supported optional path should be called **Connect Blackbox API key**, not **Sign in with Blackbox**.

## Source Findings

| Area | Finding | Orville implication | Source |
|---|---|---|---|
| Standard API authentication | Requests require an API key in the `Authorization: Bearer <key>` header. | Blackbox API adapter needs secure user-supplied credential storage. | [1] |
| Agent API prerequisites | Agent API requires a Blackbox account, API key, and Pro subscription. | Agent features need capability and plan checks; they cannot be assumed available after account login. | [2] |
| Agent API lifecycle | Public documentation exposes task-oriented operations such as create, status, continue, cancel, logs, and streaming. | Orville can map these to an optional remote-agent adapter after endpoint and schema validation. | [2], [3] |
| API protocol | Standard API is documented as OpenAI-compatible, including chat completions, streaming, and tool calling. | Orville can use an OpenAI-compatible adapter where endpoint and model behavior are verified. | [4] |
| CLI setup | CLI documentation says an account is required, configuration is required before first use, and the user is prompted for an API key. | Installing or invoking the Blackbox CLI does not provide a credential-free integration. | [5], [6] |
| OAuth/device flow | No public third-party OAuth or device-authorization documentation was identified in the reviewed sources. | Do not implement browser-cookie capture, undocumented login calls, or claim ordinary website login grants API access. | [1], [2], [5], [6] |
| API errors | Documentation distinguishes invalid/missing credentials from insufficient plan access and other request failures. | Provider status must distinguish disconnected, invalid, forbidden, quota/rate-limited, and unavailable states. | [2], [7] |
| Privacy and retention | Blackbox publishes privacy and zero-data-retention material, but guarantees can vary by product, endpoint, provider, and plan. | Orville must show the remote destination and apply explicit privacy routing before sending project content. | [8], [9] |
| Terms | Blackbox terms cover use of the platform, API, CLI, and extensions. | Review current terms before distributing an adapter or automating account interaction. | [10] |

## Required Orville Capabilities

### Default local mode

Orville must start and remain usable with no Blackbox account, sign-in, API key, or network connection. Blackbox should appear as `not_connected` rather than a startup failure. No Blackbox network request should occur until the user explicitly selects Blackbox or enables a Blackbox-dependent operation.

### Deterministic local fallback

When the managed Blackbox relay is `not_connected`, `expired`, `invalid`, `rate_limited`, `unavailable`, `disabled`, or not configured, `BlackboxFallbackPolicy` selects the first explicitly configured local provider as a fallback candidate. If no local provider exists, it returns an actionable unavailable state instructing the operator to configure a local provider or repair the relay. A `ready` relay never selects a local replacement. Public fallback status contains only state, provider ID, availability, and remediation text; provider credentials are never included.

### Optional API-key mode

Orville needs a Blackbox provider adapter with configurable endpoint family, base URL, model, timeout, streaming, tool-calling, and capability metadata. It must support connection testing and actionable handling for authentication, plan, quota, rate-limit, timeout, network, and model errors.

### Conditional OAuth/device mode

Orville may add `blackbox.oauth` or `blackbox.device` only after Blackbox confirms an official third-party flow, including client registration, redirect or device endpoints, scopes, PKCE/state requirements, access-token lifetime, refresh-token behavior, revocation, and redistribution terms. Until then, the API-key path is the only documented external integration path found in this research.

### Security and privacy

Credentials must be stored in the operating system credential store or equivalent encrypted storage. They must not appear in environment exports, project files, task state, prompts, artifacts, screenshots, errors, or logs. Orville must not capture browser cookies, scrape undocumented private endpoints, or embed a shared Blackbox credential.

Before remote execution, Orville must show the selected provider, model, endpoint family, privacy mode, and whether workspace files or tool results will leave the machine. Secret files and private keys must be excluded from context by default.

## Recommended Implementation Order

1. Confirm the official Blackbox authentication decision with current developer documentation or support.
2. Define a provider-neutral Blackbox contract and endpoint-family matrix.
3. Implement secure credential references and provider lifecycle states.
4. Implement the documented API-key adapter with mocks and redacted diagnostics.
5. Add capability negotiation for chat, streaming, tools, multimodal operations, embeddings, Agent API tasks, GitHub operations, and remote-task resumption.
6. Integrate explicit provider selection, privacy routing, user approval, and local fallback.
7. Add GUI connection, test, model selection, disconnect, and credential deletion workflows.
8. Run unit, integration, security, clean-install, failure-recovery, and second-agent review gates.

## Open Questions Requiring Blackbox Confirmation

1. Does Blackbox offer an official third-party OAuth authorization-code flow?
2. Does Blackbox offer a device-code flow suitable for desktop applications?
3. Can an official Blackbox CLI login session be used by another application through a supported interface?
4. What scopes are available for API, Agent API, GitHub, workspace files, and remote task management?
5. What subscription and usage limits apply to standard API, Agent API, and model families?
6. What are the rate limits, retry requirements, idempotency rules, and streaming guarantees?
7. Are API keys intended for desktop-client distribution, or should they be used only by a server-side application?
8. What privacy, retention, training, and data-location guarantees apply to each endpoint and model route?
9. Are there trademark, redistribution, SDK, or integration-review requirements for the Orville adapter?

## References

[1]: https://docs.blackbox.ai/api-reference/authentication "BLACKBOX AI API Authentication"

[2]: https://docs.blackbox.ai/api-reference/v1/authentication "BLACKBOX AI Agent API Authentication"

[3]: https://docs.blackbox.ai/api-reference/v1/introduction "BLACKBOX AI Agent API Introduction"

[4]: https://docs.blackbox.ai/api-reference/introduction "BLACKBOX AI API Introduction"

[5]: https://docs.blackbox.ai/features/blackbox-cli/introduction "BLACKBOX CLI Introduction"

[6]: https://docs.blackbox.ai/features/blackbox-cli/getting-started "BLACKBOX CLI Getting Started"

[7]: https://docs.blackbox.ai/api-reference/errors "BLACKBOX AI API Errors"

[8]: https://www.blackbox.ai/privacy-policy "BLACKBOX AI Privacy Policy"

[9]: https://docs.blackbox.ai/api-reference/zdr "BLACKBOX AI Zero Data Retention"

[10]: https://www.blackbox.ai/terms-of-service "BLACKBOX AI Terms of Service"


## Verification checkpoint — 2026-08-27

Official pages reviewed:

- Agent API authentication: https://docs.blackbox.ai/api-reference/v1/authentication
- CLI getting started: https://docs.blackbox.ai/features/blackbox-cli/getting-started
- Terms of Service: https://www.blackbox.ai/terms-of-service

Verified findings: the Agent API requires a BLACKBOX API key in an `Authorization: Bearer` header; the authentication page states that an account and active Pro subscription are prerequisites, and documents 401 for missing, invalid, or revoked keys and 403 for insufficient plan access. It documents dashboard key creation and deletion-based rotation, but does not document OAuth, device authorization, scopes, redirect URIs, refresh tokens, or CLI-token interoperability. The CLI getting-started page requires a BLACKBOX account login and configures providers using a BLACKBOX API key; it does not document a reusable OAuth/device flow or a token exchange contract.

The terms page states that the application license is non-exclusive and non-transferable for personal use, that Blackbox does not claim rights in Results subject to the agreement, and that shared content receives a broad license for Blackbox to use, store, copy, display, distribute, and modify it. These clauses require legal review before redistribution, shared multi-tenant operation, or sending repository/workspace content through an Orville-managed relay. This checkpoint is documentation evidence only; no account access, credentials, support request, or live API call was performed.


## Additional verification checkpoint — 2026-08-27

Official API reference reviewed: https://docs.blackbox.ai/api-reference/chat

The current chat-completion reference requires a Bearer API key, documents `https://api.blackbox.ai/chat/completions` for public API use, and states that enterprise users should use `enterprise.blackbox.ai` instead of `api.blackbox.ai` for the endpoint. It documents model IDs, alternate model routing, provider preferences, streaming, tools, response usage fields, and a stable `user` identifier for abuse detection. This page does not publish a third-party OAuth flow, device authorization, scopes, refresh-token contract, or general rate-limit table.

No official support ticket or developer-support contact was submitted. Therefore the open questions about OAuth, device authorization, CLI token reuse, scopes, redirect URIs, refresh behavior, rate limits, and redistribution remain **unverified by support** and must not be marked complete. The current public evidence supports API-key-only integration with explicit endpoint-family configuration and an enterprise endpoint option.

The local `BlackboxApiKeyContract` now validates the public and enterprise HTTPS endpoint families, rejects embedded credentials/fragments and undocumented hosts, validates model identifiers and timeout/capability metadata, and normalizes documented error envelopes without retaining response bodies. The existing OpenAI-compatible adapter supplies the request, streaming, tool-calling, and structured-output contract. These checks are credential-free and make no live API request; live authentication, quota, cost, and rollback behavior remain external validation gates.
