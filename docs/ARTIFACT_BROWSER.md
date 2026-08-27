# Artifact Browser

## Purpose

The artifact browser provides a single local workspace for viewing, downloading, exporting, versioning, and organizing generated code, documents, media, logs, and reports. It is metadata-first: previews and actions operate on an identified artifact version and must not silently execute, publish, overwrite, or delete content.

## Library model

Each row represents a versioned artifact with a stable artifact ID, truthful type, filename, revision, updated time, owner, status, source relationship, checksum, rights state, and manifest path. Supported types are `code`, `document`, `media`, `log`, and `report`; extensions and capability-specific subtypes remain metadata rather than authorization.

The library supports search by name, type, owner, and identifier, plus filters for accepted, needs-review, draft, failed, and unavailable states. Folder organization changes metadata or approved paths only; it must not duplicate, flatten, or silently move an accepted source. Empty, loading, offline, unauthorized, and failed states remain distinct and provide one safe next action.

## Preview and retrieval

Selecting an artifact opens a safe local preview with version, format, source/export relationship, checksum, rights state, and validation result. The preview does not execute code, render untrusted active content with privileges, contact an external endpoint, or publish the artifact. Download prepares the selected local file for user retrieval and reports whether any external transfer occurred.

The browser exposes the editable source when preserved, the accepted exports, and the manifest together. A missing source, checksum mismatch, incomplete manifest, unsupported format, or unverified rights state is visible as `needs_review` rather than hidden by a successful-looking preview.

## Export, compare, and version actions

Export is an explicit action that records source version, output format, exporter version, settings, checksum, and validation status. Export must not overwrite an editable source or an accepted derivative. Compare opens a local diff or side-by-side inspection between selected versions and identifies changed files, metadata, citations, and source relationships.

Create revision generates a new draft or source version with a new revision identifier. Accepted versions remain immutable. Deletion, external sharing, public publication, deployment, and irreversible retention changes are separate approval-gated actions and are not implied by download or export.

## Artifact states

| State | Meaning | Browser behavior |
| --- | --- | --- |
| `draft` | Work is not accepted for delivery. | Show revision and safe local actions; do not label as final. |
| `needs_review` | Validation, rights, source, or approval evidence is incomplete. | Show the reason and open evidence; block delivery claims. |
| `accepted` | Required review and validation gates passed. | Permit preview, download, compare, and approved export. |
| `failed` | Generation or validation failed. | Show safe operation context and remediation; preserve evidence. |
| `unavailable` | Artifact or dependency cannot be reached locally. | Show last known metadata and a bounded recovery action. |

## Validation and safety

Before an action, verify path containment, artifact identity, revision, checksum, permission, and action scope. After an action, verify the expected file or manifest exists and that the source/export relationship remains intact. Log safe operation IDs and result classes only; never place credentials, bearer tokens, cookies, private keys, or unredacted personal data in filenames, previews, manifests, logs, or browser state.

A browser implementation is accepted when it can filter supported artifact types, display versioned metadata, open a safe preview, expose source/export relationships, prepare local download, configure an explicit export, compare versions, create a non-destructive revision, and keep external sharing and deletion behind approval. Focused tests use synthetic local metadata and do not require external services.
