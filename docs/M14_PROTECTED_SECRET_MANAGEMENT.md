# M14.5 Protected Secret Management

`orville_core.protected_secrets` stores only secret references and metadata. Secret values are resolved at runtime from an injected resolver, with the process environment as the default resolver. Values are not persisted in SQLite, exported configuration, audit records, client bundles, checkpoints, or generated artifacts.

The local contract validates environment-variable naming, provider and environment metadata, supports metadata-only rotation with version increments, supports revocation, emits redacted metadata exports, and provides an explicit scrub operation for mutable runtime mappings. Unknown, missing, inactive, or unavailable references fail closed.

Production completion requires an approved enterprise secret manager or protected OS-backed store, runtime identity authorization, rotation scheduling, access review, leak detection, and evidence that credentials are absent from logs, artifacts, browser state, and checkpoints. This local module does not provision a secret manager or generate credentials.
