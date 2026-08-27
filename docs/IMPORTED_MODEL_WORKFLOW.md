# Imported-Model Workflow

## Purpose and scope

The imported-model workflow lets an operator select a local model file or folder, inspect its metadata, validate compatibility, activate it through an approved runtime, and review safe diagnostics. It is local-first and uses the existing LocalModelCatalog as the source of durable registration, checksum, provenance, licensing, storage, and lifecycle state.

The workflow never uploads the selected path, displays credential material, or claims activation before validation and the authoritative activation response succeed. A folder import inspects supported configuration and weight files without executing model-provided code.

## Workflow stages

| Stage | Required behavior | Failure outcome |
|---|---|---|
| Select source | Allow a local file or folder within an approved path boundary; show the selected path in a review step and allow cancellation. | Reject missing, unreadable, escaped, or unsupported paths without mutating the catalog. |
| Choose storage | Offer reference, copy, or approved link mode; show the destination and deduplication behavior. | Keep the source unchanged and report an actionable storage error. |
| Scan metadata | Detect recognized format, size, dimensions or architecture where available, runtime hints, capabilities, license, provenance, and checksum. | Show incomplete metadata as a warning; never infer unsupported capabilities or execute untrusted files. |
| Validate compatibility | Check existence, readability, recognized format, checksum, configured runtime/endpoint, disk availability, RAM/VRAM requirements, hardware, license restrictions, and attestation policy. | Set the result to invalid or needs-review with stable diagnostic codes and no activation. |
| Review and activate | Present a redacted summary, validation result, license restrictions, and explicit approval before activation. | Require correction or explicit approval; preserve the imported registration without activating it. |
| View diagnostics | Show stable code, severity, safe message, affected check, and recovery action; link to retained evidence without raw exceptions. | Keep diagnostics available after refresh and do not disclose secrets or private provider responses. |
| Deactivate or remove | Allow deactivation and registration removal separately; require confirmation for durable changes and never delete model files by default. | Leave files and catalog state unchanged when cancelled or unauthorized. |

## Supported lifecycle states

The catalog state is imported, active, inactive, validation-failed, or needs-review. Imported means registered but not active. Active means the latest required validation passed and activation returned success. Validation-failed and needs-review are not eligible for activation until their diagnostic conditions are resolved or an approved exception exists.

## Diagnostics contract

Diagnostics are structured records with code, severity, safe message, field or check, and bounded recovery guidance. Representative codes include missing_source, unreadable_source, unsupported_format, corrupted_or_changed, missing_runtime, runtime_mismatch, missing_endpoint, insufficient_disk, insufficient_ram, insufficient_vram, incompatible_hardware, license_review_required, and attestation_failed. Diagnostic output is redacted before it reaches the interface.

## Security and acceptance rules

Selection, copy, reference, checksum, and catalog operations remain inside approved roots and use bounded file sizes. Importing never executes scripts, deserializes unsafe model formats, or sends source content to a provider. API credentials, bearer tokens, cookies, private keys, and raw exception text are not displayed or stored in the workflow summary. Activation and registration removal use the existing authorization and explicit approval contracts.

A workflow implementation is accepted when a synthetic file import and a synthetic folder import each produce stable metadata and checksums; unsupported format, missing source, checksum change, runtime mismatch, resource shortage, hardware mismatch, license review, and attestation failures produce safe diagnostics; copy and reference modes preserve their documented semantics; activation and deactivation are observable; duplicate imports are deterministic; and removal does not delete model files by default.

Focused validation is:

    python -m unittest tests.test_imported_model_workflow
    python -m compileall -q tests/test_imported_model_workflow.py

The contract does not claim live GPU availability, production runtime provisioning, provider upload, or full GUI visual integration.

## References

- Model file handling and lifecycle: docs/ASSET_LIFECYCLE_PROCEDURES.md
- Local model validation coverage: tests/test_local_models.py
- Local model API coverage: tests/test_media_api.py
