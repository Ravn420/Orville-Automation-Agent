# Orville Release Gates

## Local release gate

Run `python tools/release_gate.py` from the repository root. The command compiles `orville_core` and `windows_gui.py`, runs the complete regression suite, and builds a dependency-free wheel under `tmp/release-wheels/`. The generated wheel is disposable and must not be committed.

## Model safety gate

Imported assets are inspected without deserialization or execution. GGUF, safetensors, and ONNX are classified as safe serialization formats. Pickle, PyTorch, Joblib, and ambiguous binary formats are classified as unsafe or unknown and produce diagnostics. Scripts in model directories are never run. Adapter records may declare a base model; activation accepts an optional selected base model and rejects mismatches. Attestation metadata is retained, verified through `AttestationVerificationService`, and persisted in `LocalModelRecord.activation_evidence`.

Model files remain user-owned data. Catalog removal is approval-gated and removes only the registration; it does not delete files. Runtime execution must occur through a configured local runtime or isolated deployment boundary. Windows Sandbox mapping and automatic startup execution are live-verified; Linux live execution and GPU isolation remain separately gated.

## Security gate

Before release, run `python tools/release_gate.py`. M13.7 consumes sandbox-boundary, required-attestation, dependency, source-integrity, and audit-evidence results and fails closed when any required result is false. Also confirm authentication, approval gates, endpoint validation, path containment, secret redaction, checksum validation, and failure diagnostics remain enabled. Do not place credentials, model files, generated caches, or release wheels in source control.

## Deployment gate

The standalone wheel and local API are deployable outside Manus. Production deployment remains environment-specific and requires a non-root execution boundary, resource quotas, secret management, HTTPS, monitoring, backup/rollback procedures, and provider credentials. These requirements are intentionally not represented as completed by the local release gate.
