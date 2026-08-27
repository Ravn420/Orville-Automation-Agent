# Document and Presentation Verification

## Purpose

`orville_core.document_verification` provides credential-free checks for Markdown documents, PDFs, and PPTX presentations before delivery. It returns stable findings suitable for a verification record and fails closed for missing or unsupported artifacts.

## Verification contract

| Area | Check | Evidence or finding |
|---|---|---|
| Page/slide count | Compare the artifact count with `expected_count` when supplied. | `count_mismatch`; Markdown uses form-feed page boundaries, PDF counts page objects, PPTX counts slide XML parts. |
| Citations | Require numeric inline citations such as `[1]` when the policy requires citations. | `citations_missing` |
| Links | Require Markdown links or HTTP(S) URLs when links are required. | `links_missing` |
| Charts | Require an image whose alt text identifies a chart, figure, plot, or graph. | `charts_missing` |
| Images | Require at least one Markdown image and non-empty alt text when images are required. | `images_missing`, `image_alt_text_missing` |
| Legibility | Require meaningful text, headings, no oversized Markdown lines, and report when PDF/PPTX text legibility requires rendering. | `legibility_text_insufficient`, `legibility_headings_missing`, `legibility_line_too_long`, `text_legibility_unavailable_without_render` |
| Format | Accept only `.md`, `.markdown`, `.pdf`, and `.pptx` in the local verifier. | `format_unsupported` |

A `DocumentVerificationResult` includes `valid`, normalized format, count, stable findings, checks performed, and safe metadata counts. It does not contact external URLs, execute embedded content, or retain document contents in a verification record.

## Procedure

1. Build or export the artifact in a reproducible environment.
2. Select a policy with the expected page or slide count and required evidence domains.
3. Run `verify_document(path, policy=policy)`.
4. Review every finding. A non-empty finding list blocks approval unless an explicitly owned exception is recorded.
5. For PDF and PPTX outputs, perform a rendered visual review in addition to the structural checks. The local verifier reports that rendered legibility is unavailable rather than claiming that a binary artifact is visually legible.
6. Preserve sanitized verification output under the approved evidence directory when it is needed for release or audit.

## Citation and link rules

Research documents must contain numeric inline citations and a references section, with links checked for syntax and reviewed for reachability by a separate passive-retrieval workflow. A syntactically valid link is not evidence that a remote page is available or authoritative. Citation completeness is likewise a structural check; source quality and claim support remain research-review responsibilities.

## Visual and legibility rules

Charts and images require meaningful alt text. A chart is identified structurally by an alt-text label containing `chart`, `figure`, `plot`, or `graph`; visual correctness, axis readability, contrast, clipping, and image resolution require rendered inspection. Long lines, absent headings, and empty text are deterministic legibility warnings for Markdown. Binary PDF/PPTX legibility remains explicitly pending rendered review.

## Limitations

The verifier does not decode media embedded in documents, render pages or slides, inspect font sizes, OCR images, validate remote URLs, judge citation quality, or certify legal accessibility compliance. Those checks require approved local renderers, accessibility tooling, or human review. No credentials or external services are required by the local contract.
