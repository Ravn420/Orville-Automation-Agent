# Reproducible Version-Change Record

Every material release or evaluation run records the following fields without storing secret values or raw private prompts:

| Field | Required representation |
|---|---|
| Model and provider | Stable provider/model identifiers, version or build, and capability snapshot. |
| Connector | Connector identifier, capability schema version, auth-method reference, and discovery result; never the credential. |
| Prompt | Prompt-template identifier and SHA-256 hash, or an approved redacted capture reference. |
| Tool | Tool name, operation schema version, permission class, and approval result. |
| Dependency | Package name, resolved version, lockfile hash, and runtime version. |
| GUI | Application version, design-system version, accessibility-contract version, and visual-baseline hash. |
| Evidence | Run ID, task ID, commit, dataset/manifest hash, test results, reviewer, and unresolved risks. |

## Change record invariants

A record is reproducible only when all applicable versions are present, hashes are stable, and the evidence can be located without private payloads. Missing or unavailable provider, connector, GUI, or runtime information is recorded explicitly as `unknown` or `blocked`; it is never inferred from a display title or conversational context.

Credentials, bearer tokens, cookies, raw prompts, raw tool arguments, and provider response bodies are excluded by default. Any approved sensitive capture must use the separate opt-in capture policy, redaction, access control, and retention controls.
