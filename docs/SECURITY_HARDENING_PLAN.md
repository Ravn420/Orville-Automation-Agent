# Orville Security Hardening Plan

**Status:** Foundation contracts implemented; platform adapters and production verification remain planned.  
**Scope:** Process-level isolation for local model inspection and execution, plus cryptographic verification of model attestations.

## 1. Current limitations

Orville currently performs non-executing format and metadata inspection, checksum comparison, script detection, adapter/base-model checks, approval-gated activation, endpoint validation, path containment, secret redaction, and safe catalog removal. It does not yet provide process-level sandboxing, GPU isolation, cryptographic signature verification, a bootstrapped trust store, or a complete production deployment boundary. These limitations remain explicit in `STATE.md`, `TASK_GRAPH.md`, and `docs/RELEASE_GATES.md`.

The existing release gate validates compilation, the full regression suite, and wheel packaging. It is a local correctness gate, not proof of production isolation or artifact authenticity.

## 2. Security objectives

The hardened design must satisfy five requirements. First, model inspection, conversion, loading, and execution must occur outside the GUI and API host process. Second, the worker must have a bounded filesystem view, resource budget, lifetime, and network policy. Third, model files must be addressed by immutable digest and never be activated after a checksum mismatch. Fourth, an attestation must be verified against a configured trust policy before it can satisfy a required provenance policy. Fifth, missing, deleted, hidden, expired, or unverifiable attestations must fail closed when policy requires them.

## 3. Process sandbox architecture

Introduce `orville_core/sandbox.py` with a provider-neutral `SandboxExecutor` interface:

```text
prepare(request) -> SandboxPlan
run(plan) -> SandboxResult
terminate(run_id) -> None
inspect(run_id) -> SandboxStatus
```

`SandboxPlan` must contain the immutable model digest, read-only model mount, writable scratch directory, output directory, command argv, environment allowlist, network mode, CPU/RAM/disk/process limits, timeout, and audit correlation ID. The executor must reject shell strings, implicit working directories, undeclared mounts, inherited credentials, and network access unless explicitly allowed by policy.

The first implementation should use platform adapters. On Windows, generate a minimal `.wsb` configuration with networking disabled, read-only mapped model input, a separate writable output mapping, bounded memory, and Protected Client mode where the host supports it. Do not map the user’s entire model directory writable. Windows Sandbox is a disposable boundary; output must be copied out only after the worker exits and the digest and result manifest are validated. Microsoft documents that networking and writable mapped folders increase exposure, while Protected Client enables AppContainer isolation.[1]

On Linux, support an explicit `bubblewrap` or container adapter with a read-only root filesystem, no network namespace by default, a private temporary directory, dropped capabilities, non-root UID, `no_new_privs`, seccomp or equivalent policy, CPU/memory/PIDs limits, and an explicit output bind mount. If no approved adapter is available, the policy must return `sandbox_unavailable` and block unsafe execution rather than silently falling back to the host process.

The GUI and API must receive only structured status, stdout/stderr subject to bounded redaction, output manifests, resource measurements, and diagnostic codes. They must never receive a live shell or inherited process environment. Every sandbox lifecycle transition must be written to the existing redacted trace/audit system.

## 4. Executed foundation slice

The platform-independent foundation is implemented in `orville_core/sandbox.py`. It validates immutable worker plans, rejects shell strings, rejects credential-like environment variables, requires explicit absolute paths and model digests, applies positive resource limits, defaults networking and GPU access off, and fails closed through `UnavailableSandboxExecutor` when no approved platform adapter exists.

`orville_core/attestations.py` defines versioned policies and digest-bound detached attestation records. It performs issuer, identity, predicate-type, expiry, subject-digest, and Ed25519 signature checks when the optional `cryptography` dependency is available. Required policies fail closed for missing, malformed, expired, wrong-digest, wrong-key, and unverifiable attestations. The full suite passes 278 tests with one existing HTTP-client deprecation warning, and Python compilation passes.

These contracts are not a production sandbox or trust root. The Windows Sandbox and Linux bubblewrap adapter implementations, persistent trust-store bootstrap/rotation/revocation, Cosign/in-toto envelope support, fail-closed handler selection, and a minimal signed TUF root/timestamp/snapshot/targets verifier are now implemented locally. Worker IPC, live platform execution, GPU isolation, persisted verification evidence, repository integration, and production trust-root ceremony remain planned below.

## 5. Sandbox implementation phases

| Phase | Work | Acceptance gate |
|---|---|---|
| S1 | Define `SandboxPolicy`, `SandboxPlan`, `SandboxResult`, diagnostic codes, and adapter discovery | Unit tests reject undeclared mounts, shell commands, inherited secrets, missing limits, and network-by-default requests |
| S2 | Implement Linux isolated adapter and Windows `.wsb` adapter | Harmless fixture runs outside the API process; filesystem, network, memory, process, and timeout boundaries are tested |
| S3 | Route model inspection/conversion/loading through the executor | No model code runs in the GUI/API process; worker audit records include digest and policy ID |
| S4 | Add failure and recovery handling | Timeout, crash, OOM, blocked network, output traversal, and worker termination produce stable diagnostics and clean temporary state |
| S5 | Add release gates | CI/local release gate proves adapter availability, negative boundary tests, redaction, and restart cleanup on each supported platform |

## 5. Cryptographic attestation architecture

Add `orville_core/attestations.py` with an `AttestationVerifier` interface and a versioned internal record:

```text
AttestationRecord {
  subject_digest: sha256:<digest>
  predicate_type: str
  issuer: str
  identity: str | None
  signed_at: datetime | None
  expires_at: datetime | None
  source_uri: str | None
  verification_method: str
  verification_status: unverified | verified | rejected | unavailable
  policy_id: str
}
```

Verification must bind the attestation subject digest to the catalog checksum, validate the signed envelope, validate the predicate schema, apply issuer and identity policy, enforce time validity, and persist the verification result. A record whose subject digest does not match the imported model is rejected. A supplied attestation must not be treated as verified merely because it is present.

Use an adapter for in-toto DSSE/Cosign verification. Cosign supports signed in-toto attestations and verification with a public key or policy; its documentation also emphasizes fail-closed handling because a signature does not prove that an attacker has not hidden or removed an attestation.[2] The verifier must invoke a pinned, locally installed verifier or a reviewed library with a fixed version range; it must not download executables or trust model-provided commands.

For repository-style distribution, add an optional TUF metadata adapter. TUF should protect the trusted metadata and target digest using explicit root, targets, snapshot, and timestamp roles, with rotation and rollback/freeze checks. The application must still make the model-specific policy decision after TUF verification; TUF is not a substitute for license, runtime, or model compatibility validation.[3]

## 6. Attestation implementation phases

| Phase | Work | Acceptance gate |
|---|---|---|
| A1 | Define trust-store, policy, schema, and diagnostic contracts | Unknown issuer, missing subject, expired signature, malformed predicate, and digest mismatch fail closed |
| A2 | Implement local detached attestation verification | Synthetic signed fixtures verify; tampered payloads, wrong keys, wrong digests, and deleted attestations fail |
| A3 | Add Cosign/in-toto and optional TUF adapters | External verification is opt-in, version-pinned, timeout-bounded, and never executes downloaded code |
| A4 | Integrate with import, validation, activation, and GUI | Required-attestation policy blocks activation; optional policy displays verified/unverified status clearly |
| A5 | Add rotation, revocation, audit, and recovery | Trust-root changes are approval-gated, auditable, reversible, and tested across restart |

## 7. Policy modes

| Mode | Behavior |
|---|---|
| `off` | Preserve attestation metadata but do not require verification; suitable only for development fixtures |
| `optional` | Verify when present; show warnings for missing or unverifiable attestations |
| `required` | Require a verified attestation whose subject digest, issuer, identity, predicate, and policy all match |
| `required_tuf` | Require a valid TUF metadata chain plus a verified target digest and any configured in-toto predicate |

Activation must record the selected policy ID and verification result. Changing the trust policy invalidates prior activation evidence and requires revalidation.

## 8. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Sandbox unavailable on a host | Fail closed for policies requiring isolation; expose `sandbox_unavailable` with installation guidance |
| GPU access weakens isolation | Default to CPU or isolated GPU adapter; require explicit policy approval for vGPU and record the increased attack surface |
| Writable host mappings permit tampering | Map model input read-only; copy outputs through a digest-checked manifest |
| Attestation can be removed or hidden | Required policies fail closed when expected attestations are absent; retain source and verification audit records |
| Trust-key compromise | Use versioned trust roots, rotation, revocation, threshold policies where supported, and TUF-style role separation |
| Verifier supply-chain compromise | Pin verifier versions, verify verifier packages, prohibit runtime downloads, and include negative fixtures in release gates |
| Resource exhaustion | Enforce memory, CPU, disk, PID, timeout, output-size, and concurrent-worker limits before launch |

## 9. Definition of done

The hardening milestone is complete only when both sandbox adapters have negative-boundary tests on their supported platforms, all model execution paths use a selected sandbox policy, required attestation policies fail closed, digest binding is tested, trust-root rotation and revocation are auditable, and the release gate records the platform-specific evidence. Until then, Orville must continue to report process isolation and cryptographic attestation verification as incomplete.

## References

[1]: https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-configure-using-wsb-file "Microsoft Learn — Use and configure Windows Sandbox"
[2]: https://docs.sigstore.dev/cosign/verifying/attestation/ "Sigstore — In-Toto Attestations"
[3]: https://theupdateframework.github.io/specification/latest/ "The Update Framework Specification 1.0.36"
