# External-Boundary Validation and Output Sanitization

## Scope and decision

Orville validates untrusted input at API, provider, connector, webhook, model, and file boundaries before it reaches orchestration or side-effecting code. It projects untrusted output into bounded, secret-safe structures before it reaches logs, GUI widgets, task state, or downstream consumers. The local shared primitives are in `orville_core.boundary`; existing API/Pydantic, provider, connector, and secret-audit checks remain authoritative for their specific boundary.

## Input validation

| Boundary | Required validation |
|---|---|
| Text and objectives | Require text where required, normalize surrounding whitespace, and enforce a declared maximum length. |
| Identifiers | Allow only bounded alphanumeric identifiers with safe separators; reject whitespace/control characters and ambiguous values. |
| HTTP(S) URLs | Require `http` or `https`, a host, no embedded username/password, and explicit permission for local hosts. |
| Structured payloads | Require the expected mapping/list shape, bounded item counts, bounded nested values, and explicit enum/risk values where applicable. |
| File/model references | Validate path containment, type, size, checksum/provenance, and explicit import permission before use. |
| Webhook/provider responses | Validate signature/status/content type, size limits, JSON shape, and replay/idempotency policy before dispatch. |

Validation failures return safe field or operation errors and do not execute downstream work. Local endpoint access is never inferred from a URL alone; it requires the caller’s explicit local permission.

## Output sanitization

`sanitize_external_output` recursively projects mappings and sequences with bounded item counts and text lengths. Sensitive keys such as credentials, API keys, bearer tokens, cookies, passwords, prompts, objectives, and secret references become `[redacted]`. Credential-like text and local filesystem paths are replaced with safe markers. Unsupported objects are reduced to bounded text rather than serialized through arbitrary representations.

Sanitization is applied before output is persisted or displayed. It is defense in depth and does not replace provider-specific redaction, backend authorization, secret storage, or audit-store controls. Raw exception strings, request headers, bearer values, provider response bodies, and unbounded payloads must not cross the interface boundary.

## Error and logging behavior

A boundary failure identifies the operation and safe error class without echoing credentials, prompts, local paths, request bodies, authorization headers, or raw provider responses. Structured logs retain correlation identifiers, status, reason codes, and bounded safe references only. A sanitization or validation failure fails closed for the affected operation and is recorded as a safe boundary event.

## Compatibility and ownership

The presentation layer and downstream consumers receive the sanitized projection. The API/provider/connector boundary owns input validation. The orchestration layer decides whether validated data is authorized and safe to execute. The audit/logging boundary owns final redaction and persistence. Existing public payload models remain compatible; the new helpers provide shared checks for code paths that do not already use a typed boundary model.

## Acceptance checks

A conforming implementation validates required text, identifiers, URLs, payload shapes, limits, signatures, and local permissions; rejects embedded URL credentials; recursively bounds and sanitizes external output; preserves safe correlation data; fails closed on boundary violations; and keeps raw secrets, prompts, paths, headers, and provider bodies out of logs and interfaces. Focused tests cover the shared primitives and existing provider/cloud-relay boundary tests. Live provider fuzzing, browser payload review, file parser hardening, and production traffic inspection remain separate release gates.
