# Model and Local-File Security

## Scope

Orville treats every imported model directory and local model file as untrusted data. Catalog inspection reads names, sizes, and selected JSON metadata only; it does not deserialize weights, import Python modules, execute hooks, or honor commands found in the directory.

## Asset and format policy

The catalog records a closed taxonomy: `full_model`, `adapter`, `quantized_model`, `tokenizer`, `configuration`, and `auxiliary_asset`. Safe serialization formats are `Safetensors`, `GGUF`, and `ONNX`. Pickle-family formats and other unsafe serialization formats are classified as unsafe and cannot pass the format gate for activation. The legacy catalog label remains available for compatibility, while the normalized taxonomy is stored in `metadata.asset_taxonomy`.

## Isolation and non-execution

Model conversion, inspection, loading, and inference are routed through the existing sandbox contract in `sandbox.py`, `sandbox_adapters.py`, and `local_execution.py`. The plan uses an absolute model path, read-only model mount, bounded scratch/output roots, filtered environment, resource limits, and an approved platform adapter. If no approved adapter is available, execution fails closed. Imported sidecar scripts, binaries, hooks, and command files are inventoried as evidence with `execution_policy=never_execute_imported_content`; they are never invoked merely because they exist.

## Activation gates

Activation verifies path existence and readability, the imported SHA-256 checksum, supported serialization, runtime compatibility, endpoint requirements, disk/RAM/VRAM/hardware requirements, and adapter/base-model compatibility. Activation additionally requires license metadata and a source or provenance reference. Required attestation policies remain fail-closed through the existing attestation service. Validation and dry-run remain non-mutating, so operators can review diagnostics before activation.

## Resource-aware admission

`ResourceScheduler` admits a request only when its aggregate CPU, RAM, GPU count, VRAM, disk, context length, concurrency, thermal, and power requirements fit within the declared capacity. Rejections return deterministic `resource_limit_exceeded:<field>` reasons; release is explicit and no resource is silently oversubscribed. Zero-valued capacity limits mean that a dimension is not constrained by that host declaration, except for explicitly requested context and concurrency limits.

## Evidence and tests

The focused test suite is `tests/test_model_security_21_2.py`. It covers safe and unsafe format classification, closed asset taxonomy, sidecar detection without execution, catalog security metadata, adapter mismatch diagnostics, and oversubscription/release behavior. Existing lifecycle, provider, attestation, and runtime-control tests were updated where activation now requires explicit license and provenance metadata.
