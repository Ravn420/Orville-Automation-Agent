# Capability-Aware Generation Workspace

## Purpose

The generation workspace lets a user choose a supported modality, select a compatible model, define inputs and output format, set reproducibility parameters, review privacy and approval state, and explicitly execute a generation request. The workspace is capability-driven: unsupported models and controls are not presented as available actions.

## Supported capabilities

| Capability | Typical input | Output examples | Additional controls |
|---|---|---|---|
| `text` | Prompt or instructions | Plain text, Markdown, JSON | Temperature, token limit, structured-output schema. |
| `code` | Requirements, repository context | Source files, patches, tests | Language, repository scope, test command, write boundary. |
| `image` | Prompt and optional reference files | PNG, JPEG, SVG | Width, height, aspect ratio, seed, rights and provenance. |
| `audio` | Script, prompt, or audio input | WAV, MP3 | Voice/music mode, duration, sample rate, transcript. |
| `video` | Script, storyboard, image/video inputs | MP4 or editable project | Duration, aspect ratio, captions, source and export relationship. |
| `vision` | Image, PDF, or video frame inputs | Analysis, OCR, structured JSON | Input custody, page/frame scope, confidence and redaction. |
| `embedding` | Text or bounded document batch | Vector embeddings | Chunking, dimensions, model, index destination, retention. |
| `other` | Capability-specific declared input | Provider-declared output | Explicit schema, limits, and review before execution. |

## Workspace stages

1. **Select capability.** The user chooses one supported capability. The workspace updates the available input controls, output formats, and model list.
2. **Define request.** The user provides a prompt or task instruction, optional local input files, output format, parameters, and an optional deterministic seed.
3. **Choose a compatible model.** Only models whose declared capability set includes the selected capability are selectable. The UI shows provider, model, capability, privacy mode, and readiness without exposing credentials.
4. **Review request.** The workspace renders a redacted payload, input filenames, output format, privacy mode, model, and estimated controls. It must not send a prompt or generated content during review.
5. **Execute explicitly.** Execution is a separate, visible action delegated to an approved adapter. Local-only drafts and previews make no network request. External routing, publication, or durable writes require their own approval gates.
6. **Record result.** The adapter returns a safe operation ID, capability, model ID, output paths, checksums, provenance, validation results, and limitations. Raw provider errors, credentials, and unredacted private inputs are not rendered.

## Input, output, and compatibility rules

Input file selection records safe names and local custody; it does not imply upload or execution. File type, size, page/frame count, and path containment are validated by the adapter before generation. Output paths use the artifact and editable-source preservation procedures. A model mismatch, unavailable capability, missing required input, invalid parameter, or policy restriction leaves the request in `needs_review` or `blocked` rather than silently switching models.

The model inventory must expose declared capabilities, supported input and output formats, privacy class, context or size limits, readiness, and required approval. A model can be listed but not selectable when it is unavailable, incompatible, unapproved, or missing a required local dependency.

## Safety and state contract

| State | Meaning | Permitted action |
|---|---|---|
| `draft` | Inputs are being composed locally. | Edit, save local draft, or cancel. |
| `needs_review` | Request or compatibility check needs attention. | Correct, inspect warnings, or cancel. |
| `ready` | Redacted request passes local checks. | Review and execute explicitly. |
| `running` | Approved adapter is processing the request. | Inspect status, pause/cancel when supported. |
| `completed` | Outputs and validation evidence are available. | Preview, verify, or hand off. |
| `failed` | Adapter returned a safe failure. | Retry, revise, or escalate with operation ID. |
| `blocked` | Policy, capability, or approval prevents execution. | View reason and bounded remediation. |

Credentials remain in approved secret storage or protected environment references and never enter draft payloads, browser storage, logs, screenshots, artifacts, or task state. The workspace must not execute an external request merely because a provider or endpoint was selected.

## Acceptance criteria

The workspace is accepted when all eight capabilities are selectable, compatible models are filtered from declared capability metadata, modality-specific inputs and outputs are surfaced, local file selection remains non-executing, the request review is redacted and deterministic, invalid or incompatible requests are blocked, explicit execution is separated from review, and results include safe operation and artifact evidence. Focused tests use synthetic local data and do not require credentials or external services.
