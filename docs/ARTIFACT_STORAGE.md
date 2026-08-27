# Artifact Storage and Lifecycle Contract

Orville stores generated artifacts below the configured artifact root. Every registered artifact receives a stable metadata record containing its relative path, media type, byte size, SHA-256 digest, creation timestamp, and artifact identifier. Path resolution is root-bound; traversal attempts and the internal version manifest are not exposed as artifacts.

## API contract

Authenticated clients can use the following routes:

| Route | Purpose |
| --- | --- |
| `POST /api/v1/artifacts/text` | Create a bounded UTF-8 text artifact under `generated/`. |
| `GET /api/v1/artifacts` | List registered files and metadata. |
| `GET /api/v1/artifacts/{relative_path}` | Download a root-contained artifact with its detected media type. |
| `GET /api/v1/artifacts/preview/{relative_path}?max_bytes=12000` | Return a bounded text preview, or metadata only for binary content. |
| `GET /api/v1/artifacts/versions/{relative_path}` | Return digest-based version history for the current file path. |
| `GET /api/v1/artifacts/retention/plan?max_versions=5` | Return deletion candidates without deleting files. |

The preview limit is bounded to 1–100,000 bytes. Text is decoded with replacement for malformed UTF-8 so previewing cannot fail because of an invalid byte sequence. Binary artifacts do not return raw content through the preview route.

## Versioning

Version history is stored in the root-bound `.artifact-versions.json` manifest. A new version is recorded only when the SHA-256 digest changes. The manifest is written through a temporary file replacement, and is excluded from listing, preview, download, and registration results. Version history is metadata-only and does not duplicate artifact bytes; retaining old bytes requires the caller to preserve separate immutable paths.

## Retention

Retention is plan-only by default. `retention_plan` reports paths with more than the requested number of recorded versions and identifies the number of versions that would be removed. It never deletes artifacts. Any future deletion workflow must use the sensitive-operation confirmation gate, show the exact paths and consequences, and validate the plan again immediately before mutation.

## Validation

Run the focused contract tests and compilation checks:

```text
python -m pytest tests/test_artifact_storage.py -q
python -m py_compile orville_core/artifacts.py orville_core/api.py
```

The current focused result is four passing tests. The broader suite was also executed; it reported 747 passing tests and three unrelated pre-existing failures in connector/shell API coverage. Those failures are not changed by this artifact-scoped work and remain a release-triage item.
