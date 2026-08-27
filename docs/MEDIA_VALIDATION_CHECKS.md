# Media Validation Checks

## Purpose

`orville_core.media_validation` provides deterministic, credential-free checks for media deliverables before they are retained, published, or handed to another workflow. The caller supplies modality-specific metadata when decoding is owned by a provider or media pipeline; the validator checks the declared values and the file itself without contacting external services.

## Required checks

| Area | Contract | Failure diagnostics |
|---|---|---|
| Format | Image, audio, and video files must use the policy allowlist. | `format_not_allowed` |
| File size | Files must remain below the policy byte limit. | `file_size_exceeded` |
| Resolution | Required width and height must be present and within minimum/maximum bounds. | `width_missing`, `height_missing`, `*_below_minimum`, `*_exceeded` |
| Duration | Required duration must be present and within minimum/maximum seconds. | `duration_missing`, `duration_below_minimum`, `duration_exceeded` |
| Accessibility | Images may require non-empty alt text; audio/video may require a transcript or captions. | `alt_text_missing`, `transcript_or_captions_missing` |
| Usage rights | A license, rights holder, and source are required by default. | `license_missing`, `rights_holder_missing`, `rights_source_missing` |

A `MediaValidationResult` returns `valid`, the modality, stable diagnostic codes, the checks performed, and safe metadata. The result is suitable for API responses, GUI review, or sanitized release evidence.

## Default format policy

| Modality | Default formats |
|---|---|
| Image | PNG, JPEG/JPG, WebP, GIF, AVIF |
| Audio | MP3, WAV, M4A, OGG, FLAC |
| Video | MP4, WebM, MOV, M4V |

Callers may provide a narrower allowlist for a target platform. Format acceptance is based on the file suffix; a future decoder-backed gate should additionally verify the file signature and actual codec.

## Accessibility requirements

Image deliverables require meaningful alt text when `require_alt_text=True`. Audio and video deliverables require either a transcript or captions when `require_transcript_or_captions=True`. Decorative assets may disable the relevant requirement only when the consuming UI records that the asset is decorative and conveys no information. Captions and transcripts must be reviewed for completeness and synchronization by the consuming workflow; this local checker verifies presence, not linguistic quality.

## Usage-rights requirements

Each non-decorative asset must identify its license, rights holder, and source. Values may be local identifiers or public URLs, but they must be explicit and non-empty. The validator does not assert that a license is legally sufficient, that a URL is reachable, or that a provider’s terms permit redistribution. Those checks require a separate reviewed evidence workflow. No credential or access token belongs in rights metadata.

## Workflow and evidence

1. Select a `MediaValidationPolicy` for the target modality and delivery surface.
2. Obtain or compute dimensions and duration from the local media pipeline or provider response.
3. Supply accessibility and usage-rights metadata from the asset record.
4. Run `validate_media()` before provenance recording or delivery.
5. Block invalid output, show the stable diagnostic codes, and retain only sanitized evidence.

The implementation enforces a 250 MiB default file-size bound, positive dimension limits, non-negative duration limits, and unsupported-modality rejection. It does not decode media, inspect codecs, transcribe audio, generate captions, validate remote rights pages, or certify legal clearance. Those remain pipeline or review responsibilities.
