# M14.2 Production Trust-Root Ceremony

`orville_core.trust_root_ceremony` provides a local, approval-gated workflow for production trust-root bootstrap, rotation, and revocation evidence. It does not contact a remote service, create keys, infer operator approval, or promote a root automatically.

## Required evidence

A ceremony requires an operator identifier, change or approval reference, ISO-8601 approval timestamp, a canonical SHA-256 digest obtained independently through the approved out-of-band channel, and a written reason. Bootstrap validates the signed root through `TufRepositoryVerifier`, verifies the pinned digest, and writes the trusted root atomically. Rotation requires an existing root, an increasing root version, verification by the previous and new root policies, and the same independent digest check. Revocation records the current-root digest and reason without deleting the root or silently changing trust state.

The evidence record contains only non-secret metadata: action, status, root version, root digest, previous digest when applicable, operator reference, timestamp, reason, and recording time. It excludes keys, tokens, credentials, private material, model content, and prompts.

## Operator procedure

First review the signed root metadata through the approved out-of-band process. Second, independently compare its canonical SHA-256 digest with the digest supplied in the ceremony approval. Third, review the proposed change and rollback plan. Fourth, run the ceremony with explicit approval and retain the evidence JSON in the protected audit location. Finally, verify the resulting root and evidence from a separate operator session. Production completion requires an approved root ceremony, rotation/revocation drill, access review, and retained audit evidence; the example configuration does not constitute production approval.

The command-line bootstrap helper remains available at `tools/tuf_root_ceremony.py`; the reusable ceremony service is `ProductionTrustRootCeremony`. Use synthetic roots and temporary paths in tests only.
