# Media Visual Verification and Quality Checks

## Purpose

This contract defines visual, auditory, technical, accessibility, provenance, and delivery checks for generated, edited, imported, and assembled media. It complements docs/ASSET_LIFECYCLE_PROCEDURES.md, which governs custody, rights, naming, storage, and retention.

An artifact is ACCEPTED only when applicable checks pass or an approved exception records the asset, impact, mitigation, owner, and review date. Failed decode, missing required content, unresolved rights, exposed private data, or an unreviewed critical defect leaves an artifact NEEDS_REVIEW or REJECTED.

## Verification record

Every review records asset_id, version, artifact_type, brief reference, technical result, quality result, accessibility result, rights/provenance result, security/privacy result, sanitized evidence, reviewer, timestamp, and decision. The implementer performs the first pass; a second reviewer independently checks delivery assets and high-severity findings.

## Common verification sequence

1. Confirm the intended version is inside the approved workspace and compare source and output checksums.
2. Parse or decode the complete artifact and record format, dimensions or duration, size, and metadata.
3. Inspect the complete artifact using full-size review, contact sheets, waveform/spectrograms, complete playback, page-by-page rendering, or composition review as appropriate.
4. Compare content with the brief and classify findings as CRITICAL, MAJOR, or MINOR.
5. Run applicable accessibility, provenance, rights, security/privacy, and delivery checks.
6. Promote only an accepted derivative and retain sanitized evidence.

## Artifact-specific checks

| Artifact | Quality inspection | Technical checks | Accessibility and delivery checks |
|---|---|---|---|
| image | Review crop, blur, compression, color, seams, text, anatomy, safety, and context. | Decode; verify dimensions, aspect ratio, profile, alpha, metadata, and hidden payloads. | Alternative text or decorative state; legibility, contrast, safe crop, rights, manifest. |
| audio | Listen end-to-end for clipping, clicks, dropouts, distortion, noise, levels, channel errors, pronunciation, and pacing; inspect waveform/spectrogram. | Verify codec, duration, sample rate, bit depth, channels, peak/headroom, size, and truncation. | Transcript or equivalent text alternative; language/speakers, synchronized text, rights. |
| video | Watch end-to-end for framing, exposure, color, dropped frames, overlays, synchronization, legibility, pacing, and unwanted content; review start/middle/end frames. | Verify codec, dimensions, frame rate, duration, tracks, sync, metadata, size, and seekability. | Captions/subtitles and transcript; equivalent description when needed; no flashing; reduced motion; playback. |
| document | Review every page for clipping, overlap, unreadable tables, links, fonts, rasterization, styles, and order. | Render; verify pages, dimensions, fonts, image resolution, metadata, links, and attachments. | Heading structure, reading order, selectable text, table headers, alternative text, contrast, navigation, language. |
| animation | Review full timeline for timing, layers, temporal consistency, crop, motion artifacts, loop seams, and text. | Verify frame rate, dimensions, duration, loop, codec, alpha, deterministic inputs, checksum. | Static frame or non-motion path; reduced motion; no flashing; readable text. |
| mixed | Review components and assembly for synchronization, hierarchy, transitions, overlays, contrast, consistency. | Verify tracks, timing, dimensions, format, checksum, manifest. | Apply the strictest alternative, caption, transcript, motion, rights, and privacy requirement. |

## Defects and acceptance

| Severity | Examples | Disposition |
|---|---|---|
| CRITICAL | Corruption, unsafe content, exposed secret/private data, restricted rights, inaccessible essential information, severe sync failure. | Reject; preserve evidence; correct and re-review. |
| MAJOR | Brief mismatch, unreadable text, clipping, artifacting, missing alternative, broken playback, wrong dimensions/duration. | Correct and re-review or document approved mitigation. |
| MINOR | Cosmetic variance without impact on brief, safety, rights, or access. | Record finding and reviewer decision. |

A quality score or automated scan does not replace full-artifact human inspection. Acceptance requires resolved critical/major findings, passing applicable technical checks, completed accessibility and rights checks, and evidence tied to the reviewed version.

## Standalone validation

From the repository root, run:

    python -m unittest tests.test_media_visual_verification
    python -m compileall -q tests/test_media_visual_verification.py

These checks validate contract structure and secret-safe wording. Actual asset acceptance additionally requires the artifact-specific inspection and evidence above; this contract does not claim live provider or publication verification.

## References

- WCAG 2.2, W3C: https://www.w3.org/TR/WCAG22/
- WebVTT, W3C: https://www.w3.org/TR/webvtt1/
- Media Accessibility User Requirements, W3C: https://www.w3.org/TR/media-accessibility-reqs/
- PDF/UA-1 overview, AIIM: https://www.aiim.org/standards/iso-14289-pdf-ua
