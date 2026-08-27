# Presentation Planning, Validation, and Export Procedures

## Purpose

This procedure defines the minimum lifecycle for creating a presentation or slide deck. It covers planning, content validation, design consistency, export verification, and delivery readiness. The workflow is format-neutral and remains usable in standalone environments.

## Presentation brief

Before slide creation, record a versioned brief containing:

| Field | Requirement |
| --- | --- |
| `deck_id` | Stable identifier for the presentation and its revisions. |
| `objective` | The decision, explanation, or action the deck must support. |
| `audience` | Primary audience, prior knowledge, and accessibility needs. |
| `duration` | Presentation duration and expected discussion time. |
| `slide_budget` | Maximum slide count, including title, agenda, references, and appendix slides. |
| `content_sources` | Approved source files, datasets, citations, and source scope. |
| `narrative` | Beginning, evidence or explanation sequence, conclusion, and call to action. |
| `visual_direction` | Theme, typography, palette, layout system, chart conventions, and image treatment. |
| `output_formats` | Required editable source and export formats, such as PPTX, PDF, or web slides. |
| `acceptance_criteria` | Testable content, visual, accessibility, and export requirements. |
| `approval_gates` | Required content-owner, rights, privacy, and publication approvals. |

If objective, audience, source scope, slide budget, output format, or acceptance criteria is missing, the deck remains `draft` and generation must not proceed to delivery.

## Planning workflow

1. **Define the outcome.** Convert the objective into one primary takeaway and a bounded set of supporting claims.
2. **Build the outline.** Assign each slide a purpose, title, key message, evidence or visual, speaker note, and transition. Avoid multiple unrelated messages on one slide.
3. **Map evidence.** Link each material claim, number, quotation, chart, or image to a source identifier and record the source’s scope and access date where applicable.
4. **Set the design system.** Select page size, grid, margins, typography hierarchy, color tokens, spacing, chart palette, image rules, and reusable layouts before detailed composition.
5. **Plan accessibility.** Define reading order, meaningful titles, alt text, captions or transcripts, contrast, minimum text size, keyboard navigation for web exports, and reduced-motion behavior for animated exports.
6. **Create and review.** Generate slides from the approved outline, then perform separate content and visual review passes.

## Content validation

The content reviewer verifies that the deck has a coherent narrative, each slide advances the objective, titles express the slide conclusion, claims are supported, calculations reconcile to their source data, and conclusions do not exceed the evidence. The reviewer also checks that:

- The opening identifies the purpose, audience, and expected takeaway.
- The sequence has a clear introduction, body, conclusion, and bounded next action.
- Every material number has units, a time period, a source, and a reproducible calculation when applicable.
- Charts identify axes, units, legends, relevant denominators, and source notes.
- Quotations preserve meaning and identify the speaker or source.
- Speaker notes distinguish facts, interpretation, assumptions, and prompts for discussion.
- Citations are readable on the slide or in an accessible references section.
- Placeholder text, duplicate slides, orphaned headings, empty layouts, and unsupported claims are absent.

A content failure blocks export approval until corrected or explicitly accepted as an exception by the content owner.

## Design consistency and accessibility

The visual reviewer checks the deck against its design system rather than personal preference. The review must verify consistent title placement, grid alignment, margins, typography hierarchy, color tokens, chart styling, image cropping, icon treatment, footer metadata, slide numbering, and treatment of repeated components. It must also verify that visual emphasis matches information priority and that no slide is overloaded or visually empty without purpose.

Accessibility checks must cover document language, reading order, meaningful slide titles, alternative text for informative visuals, captions or transcripts for audio/video, sufficient contrast, non-color-only distinctions, legible text at presentation distance, and a usable focus order for interactive web exports. Decorative visuals are marked decorative rather than assigned misleading alt text.

## Export and delivery checks

Export checks run against every requested format and a representative sample of slides. The validation record includes the source version, exporter and version, output filename, checksum, slide count, page or aspect-ratio settings, fonts, linked assets, warnings, and reviewer.

| Check | Acceptance condition |
| --- | --- |
| Editable source | The source opens without repair prompts and remains available when requested. |
| PDF or print export | Page count matches the source; clipping, overflow, blank pages, broken glyphs, and missing images are absent. |
| Web export | Routes load locally; navigation, keyboard focus, links, media, and reduced-motion behavior work as documented. |
| Fonts and assets | Required fonts and assets are embedded, packaged, or explicitly listed as prerequisites. |
| Charts and images | Resolution, crop, labels, source notes, alt text, and rights evidence remain intact. |
| References and links | Citations, URLs, notes, and internal links resolve or are clearly marked unavailable. |
| Visual sample | Title, dense-content, chart, image, references, and final slides pass visual inspection. |
| Delivery manifest | Output paths, formats, checksums, approvals, validation results, and known limitations are recorded. |

Export failure leaves the deck `needs_review`; it must not be represented as delivery-ready. Publishing, public visibility, external sharing, or paid export services require explicit approval and are outside this local procedure.

## Versioning, source preservation, and handoff

Preserve the editable source, outline, source records, generated assets, export settings, validation record, and final outputs when retention is required. A revision changes the deck version and records the reason, changed slides, affected sources, and rerun checks. Do not overwrite an accepted source with an export. Use lowercase kebab-case names such as `quarterly-risk-review-v1.pptx` and `quarterly-risk-review-v1.pdf`; do not use `final-final`, credentials, personal identifiers, or timestamps as the only identity.

The final handoff states the deck objective, audience, source scope, output formats, acceptance results, approvals, changed paths, known limitations, and next action owner. Credentials, private keys, cookies, bearer tokens, and unredacted personal data are never included in the deck, notes, manifest, or validation log.
