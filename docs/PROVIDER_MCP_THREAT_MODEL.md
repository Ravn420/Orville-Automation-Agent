# Provider and MCP Security Threat Model

## Scope and trust boundaries

Orville treats user instructions, retrieved provider data, provider responses, tool results, connector configuration, and approval records as different trust domains. Provider and MCP requests cross a local REST boundary, an optional connector-bridge boundary, and provider-owned network boundaries. Credentials remain in protected connector storage and are never accepted as ordinary tool arguments.

| Threat | Abuse case | Controls |
|---|---|---|
| Prompt injection | A provider response or project memory tells the agent to ignore the user and invoke a privileged tool. | Retrieved content is labeled with explicit untrusted-content boundaries; tool output is typed and marked untrusted; tools are selected from static allowlists; authorization is evaluated outside model-produced text. |
| Excessive agency | A model invokes a write, delete, publish, purchase, transfer, account-change, or production-state operation without a human decision. | Risk classes, dry-run mode, explicit approval, approval references, and fail-closed external-action checks are required for sensitive operations. |
| Insecure output handling | Provider output is treated as executable instructions or returned without bounded size/redaction. | Response-size limits, JSON validation, secret redaction, typed tool-output boundaries, and no raw exception propagation. |
| Sensitive information disclosure | Credentials or session tokens appear in arguments, logs, API responses, or error messages. | Credential-shaped argument rejection, protected credential storage, redacted public connection records, secret-free authorization records, and bounded diagnostics. |
| Supply-chain risk | A connector manifest, remote operation catalog, or model-generated operation expands the available capability set. | Static registered manifests, explicit enabled operations, operation risk classes, host allowlists, bounded discovery counts, and provider-specific configuration requirements. |
| Context poisoning | Durable project memory or retrieved content changes future behavior by masquerading as system policy. | Explicit source/boundary labels, separate instruction/data/tool-result channels, least-privilege context binding, and approval decisions that are not inferred from retrieved text. |
| Unbounded tool access | A caller fabricates an operation name, arbitrary endpoint, path, or credential-bearing argument. | Operation and tool allowlists, strict identifier schemas, filesystem-root containment, remote host/port checks, response and argument limits, and no credential passthrough. |
| SSRF and OAuth abuse | A connector redirects to a private host, uses an unexpected port, or sends an authorization code to an attacker-controlled callback. | HTTP(S)-only credential-free endpoints, private-address and port checks, no-redirect OAuth transport, localhost callback validation, PKCE, state consumption, and signed optional MCP state handles. |
| MCP state fixation/replay | A state handle is reused, tampered with, or presented under another user/task/provider. | HMAC-signed handles, expiry, nonce tracking, context binding, constant-time signature comparison, and single-use consumption. |

## Operational invariants

1. An external side effect must be both allowlisted and explicitly approved.
2. Dry-run mode must fail closed before network mutation.
3. A credential reference identifies a protected record; credential values must not travel through model or tool arguments.
4. A provider, user, task, and scope must agree before a task-bound credential is used.
5. Redirects are not followed for authorization-server, token, revocation, or connector-bridge requests.
6. Audit records contain decision metadata and bounded redacted reasons, never raw secrets or unnecessary payloads.
7. Missing configuration denies access rather than silently widening permissions.

## Residual risks and review requirements

DNS rebinding protection requires deployment-level DNS/IP pinning or an egress proxy when a provider host resolves dynamically. Provider-specific OAuth issuer metadata should be pinned or verified against an approved issuer registry before production use. The authorization context should be required by default for production connector invocations, with legacy context-free behavior restricted to local compatibility mode and covered by deployment configuration tests.
