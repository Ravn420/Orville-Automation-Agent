# Media Provenance and Transformation History

## Purpose

Orville preserves the lineage needed to reproduce and audit generated media without modifying caller-owned source files or storing live credentials. `MediaProvenanceStore` is a standalone local contract for prompts, source assets, generated outputs, and ordered transformations.

## Storage layout

A provenance root contains retained asset copies under `assets/<role>/`, plus an append-only JSON history file:

```text
media-history/
├── assets/
│   ├── source/<sha256-prefix>-<safe-name>
│   └── generated/<sha256-prefix>-<safe-name>
└── history.json
```

Each asset record includes an ID, role, original name, root-relative retained path, MIME type, size, SHA-256 checksum, and creation timestamp. `ingest_asset()` copies the source or generated file into the store; it never overwrites the caller's file and rejects files larger than the configured limit. Paths and role names are sanitized and resolved beneath the provenance root.

## History records

A history record contains:

| Field | Meaning |
|---|---|
| `history_id` | Stable caller-supplied or generated lineage identifier. |
| `prompt` | Prompt text after repository redaction. |
| `prompt_sha256` | Digest of the original prompt for reproducibility comparison without retaining secret values. |
| `source_asset_ids` | IDs of retained source/reference assets. |
| `generated_asset_ids` | IDs of retained outputs. |
| `transformations` | Ordered operation names, non-secret parameters, and output IDs. |
| `metadata` | Redacted non-secret provider, model, or workflow metadata. |
| `created_at` | UTC creation timestamp. |

Prompts and metadata are passed through `SecretRedactor` before persistence. This intentionally prioritizes the repository's secret-storage policy over exact retention of a prompt that contains a credential. The digest remains available to detect whether the original prompt changed, without exposing its content.

## Workflow

1. Create a `MediaProvenanceStore` beneath the configured runtime or artifact data directory.
2. Ingest each source/reference file with `role="source"` before generation.
3. Ingest each generated or edited output with `role="generated"` after the operation succeeds.
4. Record the redacted prompt, source IDs, generated IDs, ordered transformations, and safe metadata in one history record.
5. Resolve retained files only through `asset_path()` and verify checksums when exporting or auditing.

The store is local and standalone-capable. A future object-storage adapter may preserve the same metadata shape, path containment, size limit, and redaction behavior; it must not place credentials or raw provider responses in the lineage record.

## Validation and limitations

`tests/test_media_provenance.py` covers source/output retention, transformation lineage, prompt and metadata redaction, source immutability on size rejection, filename sanitization, and root containment. The current implementation uses a local JSON history file and synchronous file copies. Multi-process locking, remote object storage, cryptographic signing, and media-specific perceptual hashes remain future deployment or hardening work.
