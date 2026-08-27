# M13.1 Security Baseline and Platform Matrix

**Status:** Implemented locally; live support is evidence-scoped.
**Last updated:** 2026-08-27
**Owner:** Security Agent / Verification Agent

## Security baseline

Orville must keep model inspection, conversion, loading, and execution outside the API and GUI host process whenever the selected policy requires isolation. Worker plans must bind an immutable model digest, explicit read-only model input, explicit writable output, bounded resources, a disabled network by default, an environment allowlist, a bounded lifetime, and an audit correlation ID.

The host must never pass shell strings, inherited credentials, undeclared mounts, or unrestricted working directories to a worker. Required attestation policies must fail closed when the attestation is missing, malformed, expired, revoked, unverifiable, or bound to a different model digest. Activation evidence must preserve the selected policy ID, verification method, status, digest, issuer or identity, predicate type, timestamps, source URI, and safe diagnostic code.

All unsupported platform capabilities remain explicit `sandbox_unavailable` or infrastructure-dependent states. No local adapter result is treated as production support without platform-specific live evidence.

## Platform support matrix

| Platform/capability | Policy default | Current evidence | Status | Boundary |
|---|---|---|---|---|
| Windows Sandbox process launch | Network disabled, vGPU disabled, bounded memory | Windows 11 host launched Sandbox successfully | Live verified | Requires Windows Sandbox feature and a single active Sandbox worker. |
| Windows host-folder mapping | Model input read-only; output explicitly writable | Corrected quoted `.wsb` invocation produced a host-visible automatic write marker | Live verified | `.wsb` paths containing spaces must be passed to `WindowsSandbox.exe` as one quoted argument. Host source folders must exist before launch. |
| Windows automatic `LogonCommand` | Direct script path inside mapped guest folder | `run_diag_temp.cmd` executed automatically and wrote `automatic_write_probe` | Live verified | Evidence covers startup execution and mapping, not GPU isolation. |
| Windows GPU isolation | vGPU disabled unless explicitly approved | No live GPU exposure test performed | Pending | Requires a separate vGPU-enabled test and device-exposure assertion. |
| Linux bubblewrap | No network, non-root, read-only root, bounded resources | Adapter construction and fail-closed tests only | Infrastructure-dependent | Requires capable Linux/WSL host with `bwrap`; GPU requires exposed device and explicit policy. |
| Trust store and Ed25519 verification | Required policies fail closed | Local unit and negative-boundary tests | Locally verified | Production root bootstrap, rotation ceremony, and external key custody remain pending. |
| Cosign/in-toto | Optional, pinned, timeout-bounded verifier | Adapter and synthetic handling implemented | Locally verified | Live external verifier execution remains environment-dependent. |
| TUF repository chain | Required only for `required_tuf` | Root/timestamp/snapshot/targets integrity tests | Locally verified | Production repository and trust-root ceremony remain pending. |

## Required audit evidence

Every worker lifecycle transition must record a redacted model ID, immutable digest, policy ID, worker ID, platform adapter, start and end timestamps, result status, diagnostic code, bounded resource measurements, and output-manifest digest. The record must not contain private keys, bearer tokens, inherited environment values, or unbounded guest console output.

## M13.1 exit criteria

M13.1 is complete for local implementation when the baseline, platform matrix, trust boundaries, fail-closed behavior, evidence requirements, and unsupported-host rules are documented and referenced by the release gate. Platform-specific tasks remain separately gated by live worker, GPU, and production trust-root evidence.

## Evidence

- `tmp/live-sandbox-test/automatic_mapping_success.txt`
- `tmp/live-sandbox-test/manual_short_path_result.txt`
- `orville_core/sandbox.py`
- `orville_core/sandbox_adapters.py`
- `orville_core/attestations.py`
- `orville_core/tuf_metadata.py`
- `tests/test_security_hardening.py`
