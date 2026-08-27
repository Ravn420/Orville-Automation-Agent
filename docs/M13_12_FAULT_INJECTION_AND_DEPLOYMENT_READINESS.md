# M13.12 Fault Injection and Deployment Readiness

**Status:** Test design and deployment checklist
**Date:** 2026-08-27

## M13.12 fault-injection matrix

All scenarios use `SyntheticDeploymentAdapter` or a reviewed provider stub. No production endpoint or credential is permitted. Each scenario must assert the durable controller state, adapter mutations, rollback attempt count, quarantine status, and redacted audit events.

| ID | Injected fault | Expected decision | Expected controller result | Required assertions |
|---|---|---|---|---|
| FI-01 | Samples below policy minimum | Pause | `paused`; no traffic advance | `insufficient_samples`; no rollback mutation; fresh observation required |
| FI-02 | Observation window incomplete | Pause | `paused` | `observation_window_incomplete`; same cohort retained |
| FI-03 | Error rate above threshold | Rollback | `rolled_back` | Traffic reset; known-good target restored; candidate quarantined; one rollback audit event |
| FI-04 | p95 latency above threshold | Pause | `paused` | `p95_latency_exceeded`; no cohort advance |
| FI-05 | p99 latency above threshold | Rollback | `rolled_back` | `p99_latency_exceeded`; rollback bounded by `max_attempts` |
| FI-06 | Saturation above threshold | Pause | `paused` | `saturation_exceeded`; no traffic advance |
| FI-07 | Business-health below minimum | Pause | `paused` | `business_health_below_minimum`; no rollback unless policy escalates |
| FI-08 | Critical security finding | Pause immediately, then rollback policy path | `paused` or `rolled_back` according to policy | Traffic pause precedes rollback; security finding is never treated as healthy |
| FI-09 | Candidate crash or worker exit | Rollback | `rolled_back` | Crash diagnostic; candidate quarantined; rollback target required |
| FI-10 | Health provider unavailable | Pause | `paused` | No success decision; retry requires a fresh bounded window |
| FI-11 | Release/cohort mismatch | Pause or reject | `paused` | `observation_release_mismatch` or stale-window diagnostic; no mutation |
| FI-12 | Duplicate health event | No-op | State unchanged | Same decision ID/idempotency key; no duplicate traffic or rollback mutation |
| FI-13 | Controller restart during observation | Resume | Existing state restored | Same run, cohort, and decision cursor after restart |
| FI-14 | Rollback adapter timeout | Retry | `paused` until attempts exhausted, then `failed` | Attempts never exceed `max_attempts`; no false `completed` state |
| FI-15 | Rollback target unavailable | Fail closed | `failed` | Candidate remains quarantined or blocked; explicit missing-target diagnostic |
| FI-16 | Quarantine operation fails | Fail closed | `failed` | Incident audit record; no release completion |
| FI-17 | Malformed policy | Reject before deployment | No run created | Invalid cohorts, unbounded hold, missing target, or disabled fresh health rejected |
| FI-18 | Secret-bearing adapter metadata | Continue with redaction | State/audit persisted | Tokens, API keys, authorization, and passwords absent from audit payloads |

## Acceptance sequence

The test runner should execute scenarios in this order: policy rejection, clean progression, sparse-data pause, threshold-triggered pause, critical-security pause, rollback success, rollback retry, rollback exhaustion, quarantine failure, duplicate-event idempotency, restart recovery, and audit redaction. A scenario passes only when durable state and externally visible adapter calls agree.

## Production trust-root ceremony

The current ceremony utility is `tools/tuf_root_ceremony.py`. It requires an explicit `--approve` flag and supports initial bootstrap, pinned canonical-root hashing, and approved rotation. The ceremony must be performed by authorized operators outside the application runtime.

### Bootstrap checklist

| Gate | Required evidence |
|---|---|
| Root generation | Root metadata generated in an offline or controlled signing environment; private keys never enter the Orville repository, GUI, logs, or worker environment. |
| Independent review | Two-person review confirms role keys, threshold, expiration, repository identity, and canonical metadata hash. |
| Host binding | The expected SHA-256 is calculated from canonical root JSON and supplied through `--expected-sha256`. |
| Approval | An approval record identifies operator, reviewer, root version, hash, target store, scope, and UTC timestamp. |
| Bootstrap execution | `python tools/tuf_root_ceremony.py --root <root.json> --store <trusted-root.json> --expected-sha256 <hash> --approve` returns `bootstrapped`. |
| Verification | Reload the trusted store and verify root version, role metadata, key IDs, thresholds, expiry, and target repository identity. |
| Recovery copy | Store an encrypted, access-controlled backup and document the recovery owner and restore drill. |

### Rotation and revocation checklist

Rotation requires a new root version, an independent review of old and new key sets, explicit overlap or threshold rules, a rollback plan, and an approval-gated command using `--rotate-from`. Revocation requires evidence of compromise or retirement, a replacement root or key set, validation that the previous key cannot satisfy the active policy, and a tested recovery path. The old root must remain available only as protected audit evidence, never as an automatically trusted fallback.

## Deployment security baseline

M13 deployment must not proceed until the following conditions are met:

1. The M13.7 gate passes with the actual target platform evidence, not synthetic booleans.
2. Required attestation verification is bound to the exact model digest, policy ID, trust-root version, and activation record.
3. Windows Sandbox has live IPC and mapping evidence; Linux requires a live bubblewrap result on the supported deployment host.
4. Model input mappings are read-only, output mappings are explicit, networking is disabled by default, and worker resources are bounded.
5. All secrets are supplied through the deployment secret manager and are absent from controller state, audit records, model metadata, and crash output.
6. Canary policy uses monotonic cohorts, minimum samples, observation holds, fresh health decisions, a known-good rollback target, and bounded rollback attempts.
7. Synthetic fault injection passes the complete matrix, including restart/idempotency and rollback failure.
8. A non-production canary completes successfully and a rollback drill restores the known-good release.
9. Production integration has an operator-approved change record, health telemetry, protected deployment credentials, monitoring, backup, and an exercised recovery owner.

## Current blockers

Production trust-root bootstrap and rotation are not complete. Linux live isolation and GPU isolation remain infrastructure-dependent. The provider-neutral deployment adapter and the complete M13.12 fault-injection runner must be implemented before M13.15 production integration can be considered.
