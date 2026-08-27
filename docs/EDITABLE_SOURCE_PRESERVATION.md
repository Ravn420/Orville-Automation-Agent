# Editable Source Preservation

## Purpose

Orville must preserve an editable source alongside exported presentation, document, audio, video, image, and other artifacts whenever an editable source exists and retention is permitted. An export is a delivery derivative, not a replacement for the source. This procedure defines the source/export bundle, naming, versioning, storage, validation, and fallback rules.

## Artifact bundle

Each retained deliverable is represented by a manifest that links the editable source to every export:

| Field | Requirement |
| --- | --- |
| `artifact_id` | Stable logical identity shared by the source and its derivatives. |
| `source_path` | Approved relative path to the editable source, or `null` when no editable source exists. |
| `source_format` | Native or editable format, such as PPTX, ODT, SVG, WAV, project JSON, or source Markdown. |
| `source_checksum` | Checksum of the exact retained source bytes. |
| `exports` | List of derivative paths, formats, checksums, exporter versions, and export timestamps. |
| `source_version` | Version of the editable source used for the exports. |
| `relationships` | Parent, derived-from, supersedes, and replacement references. |
| `retention_class` | Approved source, delivery, evidence, or temporary retention decision. |
| `validation` | Source-open, export, fidelity, accessibility, rights, and integrity results. |
| `approval_reference` | Safe reference for required content, rights, or publication approvals. |

The manifest must contain safe identifiers only. Credentials, private keys, cookies, authorization headers, and unredacted personal data are prohibited.

## Preservation workflow

1. **Identify the source.** Before export, identify the editable source and verify that its path is inside the approved workspace or is explicitly referenced by a user-approved external location.
2. **Freeze the source version.** Assign an immutable source version and calculate its checksum. Do not export from an unrecorded or mutable working copy.
3. **Export derivatives.** Create each requested export in a separate derivative path. Never overwrite the editable source with a PDF, image, flattened document, or other export.
4. **Build the manifest.** Record source metadata, derivative metadata, exporter/tool versions, settings, relationships, approvals, and validation results.
5. **Verify fidelity.** Confirm that the export opens, has the expected pages/slides/frames/tracks, preserves required fonts and assets, and retains citations, links, accessibility metadata, and visual intent where the format supports them.
6. **Deliver the bundle.** Deliver the editable source and accepted derivatives together when the brief requests editable retention or when later revision is reasonably expected.
7. **Retain or supersede.** Keep accepted source and export versions immutable. A revision creates a new source version and new derivatives; it does not silently replace the prior accepted bundle.

## Format and fallback policy

Editable retention is required when the source format is available, supported, and legally or operationally permitted to retain. When no editable source exists, the manifest must set `source_path: null`, record `source_format: unavailable`, explain why, and preserve the highest-fidelity non-editable origin available. The absence of an editable source must be visible in the handoff and must not be represented as complete source preservation.

If an exporter cannot preserve a feature, the manifest records the feature, affected derivative, exporter limitation, and reviewer decision. A lossy export may be delivered only when the acceptance criteria permit it and the limitation is disclosed. Do not flatten, transcode, strip metadata, or remove layers merely to make an export pass without recording the transformation.

## Naming and storage

Use a stable bundle directory and deterministic names:

```text
artifacts/<artifact-id>/source/<artifact-id>--<slug>--v<major>.<minor>.<source-extension>
artifacts/<artifact-id>/exports/<artifact-id>--<slug>--v<major>.<minor>.<export-extension>
artifacts/<artifact-id>/manifest.json
```

Source and export filenames use lowercase kebab-case, stable IDs, explicit versions, and truthful extensions. Do not use `final-final`, credentials, personal identifiers, or timestamps as the only identity. Temporary conversion files belong under `tmp/` and must not be confused with retained source or delivery artifacts.

All writes pass path-containment checks. Runtime data, credentials, browser state, and private provider responses remain outside source-controlled artifact paths. Generated media and downloaded models are not retained in source control unless explicitly designated as artifacts.

## Validation and handoff

The validation record must include:

- The source checksum and each export checksum.
- A successful open/parse check for the source and each derivative.
- Page, slide, frame, duration, track, or equivalent count comparisons where applicable.
- Font, linked-asset, citation, link, accessibility, and rights checks.
- Exporter and toolchain versions plus relevant settings.
- A statement that the source was not overwritten and that the bundle paths are contained.
- Approval status, retention decision, known fidelity losses, and unresolved risks.

A second review confirms that the editable source can be located and used for revision, that each export points to the correct source version, and that the manifest is complete and secret-safe. External sharing, publication, store submission, or destruction of an older bundle requires separate explicit approval.

## Completion criteria

Source preservation is complete only when the editable source, accepted derivatives, and manifest are retained together, or when the documented no-source fallback is explicitly accepted. A missing source, checksum mismatch, unverified derivative, path violation, or undisclosed lossy transformation leaves the bundle `needs_review`.
