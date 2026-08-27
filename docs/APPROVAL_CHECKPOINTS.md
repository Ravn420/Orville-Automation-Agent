# Approval Checkpoints for Irreversible and High-Impact Actions

## Scope

Orville requires an explicit approval checkpoint before any irreversible or high-impact action. Covered actions include publish, deploy, delete, overwrite, revoke, account or permission changes, external messages, financial operations, production activation, schedule enablement, and any connector operation whose consequence cannot be safely reversed.

## Checkpoint lifecycle

```text
not_required -> pending -> approved -> executing -> completed
                  |           |
                  +-> rejected +-> expired
                  +-> cancelled
```

A protected workflow step remains blocked until its checkpoint is approved. Missing, expired, malformed, stale, or ambiguous approval fails closed. Dry-run previews show the consequence and preserve the approval requirement; a preview never satisfies approval.

## Required checkpoint record

`ApprovalCheckpoint` is persisted with a deterministic approval ID, run ID, step ID, safe action summary, safe target summary, status, request timestamp, resolution timestamp, approver identifier, and bounded resolution reason. Summaries identify the consequence and exact target/scope without including prompts, credentials, bearer tokens, raw provider responses, or private paths. Duplicate creation for the same run and step returns the same pending record.

## Approval requirements

The approval UI or API must show the action, exact target and scope, consequence preview, reversibility or rollback option, affected artifact or account reference, and expiration. Approval is a deliberate typed acknowledgement by an authorized operator, not an inferred response or a generic workflow success. An approval is single-use for the identified run, step, and checkpoint generation. Rejection, cancellation, and expiration cannot be bypassed by retrying the same unapproved step.

| Condition | Required behavior |
|---|---|
| No checkpoint | Create a pending checkpoint and block execution. |
| Approved checkpoint | Permit only the matching run/step/scope and record the execution transition. |
| Rejected checkpoint | Keep the step blocked and record the rejection reason safely. |
| Expired checkpoint | Require a new checkpoint; never revive the expired approval. |
| Scope or generation mismatch | Fail closed and require review. |
| Duplicate resolution | Preserve the first terminal decision; do not overwrite it. |
| Approval-store failure | Do not execute the protected action; surface a safe recovery state. |

## Ownership and evidence

The orchestration layer owns checkpoint state and execution gating. The presentation layer renders bounded consequences and status. The authorization boundary verifies approver identity and permission. The audit layer records append-only safe metadata. External integrations execute only after the checkpoint and any separate connector policy are satisfied. Completion evidence includes the checkpoint ID, run/step identity, approval status, approver reference, policy version, and safe result summary.

## Recovery and safety

A protected action must be idempotent or have a reviewed compensation path before approval can be accepted. If a worker restarts after approval but before completion, reconciliation checks the checkpoint generation and durable execution evidence before retrying. If execution status is unknown for a non-idempotent action, the step becomes `blocked` for review rather than being repeated. Diagnostics use safe reason codes and never expose secrets.

## Acceptance checks

A conforming implementation creates durable pending checkpoints, requires exact target/scope confirmation, supports single-use approval and rejection/expiration, preserves the first terminal decision, blocks on store or authorization failure, keeps dry-run separate from approval, records safe evidence, and prevents unapproved or ambiguous execution. Focused tests cover durable creation, idempotency, resolution, and fail-closed boundaries. Live identity-provider authorization, external connector execution, and production destructive-action exercises remain deployment-owned gates.
