# Deprecation and Migration Policy

**Owner:** Release and compatibility owner

| Surface | Deprecation record | Migration requirements | Removal gate |
|---|---|---|---|
| Provider | Provider ID, capability version, support window, replacement | Compatibility check, fallback provider, credential-reference review, test evidence | No supported workload depends on the retired capability. |
| Model format | Format/version, converter, checksum and runtime support | Non-destructive conversion preview, backup, import validation, rollback path | Converted artifact passes compatibility and behavioral evaluation. |
| API | Route/schema/version and client impact | Versioned overlap period, contract tests, migration guide, telemetry of old clients | No active client remains or an approved exception exists. |
| MCP | Server/operation schema version and capability changes | Read-only discovery comparison, permission review, fake-transport tests, rollback | Discovery and invocation tests pass for the replacement. |
| Runtime dependency | Package/runtime version and security/support status | Lockfile update, clean-environment install, regression suite, license/security review | Reproducible build and release thresholds pass. |
| GUI component | Component/design/accessibility version and affected workflows | Visual baseline, keyboard/accessibility review, responsive checks, rollback checkpoint | Critical workflows retain equivalent accessible actions. |

## Required lifecycle

Every deprecation begins with a notice, owner, affected assets, support deadline, replacement, risk assessment, and migration evidence. During the overlap period, the old surface remains available only under an explicit compatibility policy. Migration is previewed and reversible; destructive conversion, deletion, account changes, publishing, or production promotion requires separate approval. Unknown compatibility or missing rollback evidence leaves the migration blocked.

## Evidence and rollback

Retain old and new version identifiers, checksums, contract results, dataset/manifest hashes, affected task IDs, migration run ID, reviewer, and rollback target. Never store credentials or raw private payloads in the record. A failed migration preserves the original state and records the failure class; it does not silently retry a destructive operation.
