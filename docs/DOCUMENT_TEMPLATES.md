# Document Templates

## Purpose

These templates define the minimum structure for durable Orville documents. Each document must identify its purpose, audience, owner, status, date, scope, assumptions, evidence, validation, and unresolved risks. Templates are framework-neutral Markdown and remain usable outside Manus.

## Shared document header

Every generated document begins with this metadata block:

```yaml
---
title: "Replace with a descriptive title"
document_type: report | specification | runbook | research
status: draft | in_review | approved | superseded
owner: "Role or named owner"
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
version: "0.1"
audience: "Primary audience"
project_id: "Safe project identifier"
---
```

Do not place credentials, bearer tokens, private keys, cookies, authorization headers, or unredacted personal data in metadata or document bodies. Use safe references for protected records.

## Report template

Use a report for findings, progress, evaluation, incident, or decision-support summaries.

```markdown
# Report title

## Executive summary

State the objective, principal result, decision relevance, and most material limitation.

## Objective and scope

- **Objective:** `REPLACE`
- **In scope:** `REPLACE`
- **Out of scope:** `REPLACE`
- **Audience:** `REPLACE`
- **As-of date:** `YYYY-MM-DD`

## Method and evidence

Describe inputs, method, evidence quality, and validation. Separate retrieved facts from analysis and assumptions.

## Findings

### Finding 1

State the finding, evidence, impact, confidence, and limitation.

## Risks and limitations

Record uncertainty, coverage gaps, dependencies, and unresolved issues.

## Conclusion and next actions

List only bounded, authorized next actions with an owner and review gate.

## References

[1]: https://example.invalid/source "Replace with source title"
```

Reports must not present recommendations as facts. Consequential actions require explicit authorization and must be labeled as proposed actions.

## Specification template

Use a specification for a behavior, interface, architecture, data model, or implementation contract.

```markdown
# Specification title

## Summary

State the problem, intended outcome, and non-goals.

## Requirements

| ID | Requirement | Priority | Acceptance test |
| --- | --- | --- | --- |
| REQ-001 | `REPLACE` | P0/P1/P2 | `REPLACE` |

## Interfaces and data

Define inputs, outputs, schemas, ownership, compatibility, error envelopes, and migration requirements.

## Security and privacy

Define trust boundaries, approval gates, secret references, path containment, access control, and redaction requirements.

## Operational behavior

Define resource bounds, retries, timeouts, restart behavior, observability, and rollback expectations.

## Validation plan

List focused tests, integration tests, static checks, and independent verification evidence.

## Compatibility and rollout

State affected callers, backward-compatibility expectations, rollout steps, and rollback steps.

## Open questions

Record only unresolved decisions that block or constrain implementation.
```

A specification is complete only when every requirement has an acceptance test and the affected interfaces, failure behavior, and migration or rollback expectations are explicit.

## Runbook template

Use a runbook for repeatable operator procedures, incident response, maintenance, validation, deployment, or recovery.

```markdown
# Runbook title

## Purpose and safety boundary

State the objective, authorized scope, prohibited actions, and required approvals.

## Preconditions

List runtime versions, permissions, configuration references, backups, health prerequisites, and safe stopping conditions.

## Procedure

1. **Action:** `REPLACE`
   **Purpose:** `REPLACE`
   **Expected result:** `REPLACE`
   **Failure handling:** `REPLACE`

## Verification

Define health checks, expected artifacts, logs, status transitions, and independent confirmation.

## Rollback and recovery

Define the trigger, preserved data, rollback command or action, verification, and escalation path.

## Evidence and handoff

Record timestamps, safe identifiers, commands, outcomes, warnings, approvals, changed paths, and unresolved risks. Redact secrets.
```

Runbooks must be executable by a qualified operator without relying on hidden context. Destructive, external, production, account, payment, publication, or credential actions require an explicit approval gate before the step.

## Research output template

Use a research output for evidence-backed analysis and source synthesis. The existing `RESEARCH_SYNTHESIS_TEMPLATE.md` remains the detailed research-specific template; this section defines the shared minimum contract.

```markdown
# Research title

## Executive summary

State the question, answer supported by evidence, and material uncertainty.

## Research question and scope

Define the question, inclusion criteria, exclusion criteria, risk tier, audience, and as-of date.

## Methodology and source hierarchy

Record retrieval time, source quality, freshness policy, search strategy, extraction method, corroboration, and independent review.

## Findings by evidence class

### Primary evidence

Use inline numeric citations such as [1].

### Secondary reporting

Separate context and corroboration from primary evidence.

### Analysis and interpretation

Separate inference, comparison, assumptions, and implications from source statements.

### Uncertainty and limitations

Identify stale, missing, inaccessible, contradictory, or biased evidence.

## Conclusion and bounded next actions

State only supported conclusions and authorized follow-up actions.

## References

[1]: https://example.invalid/source "Replace with source title"
```

Research outputs must record publication and access dates where applicable, preserve source scope, distinguish facts from analysis, and include a references section. Private sources use safe identifiers rather than exposed URLs or credentials.

## Review and lifecycle rules

The author performs a completeness pass against the selected template. An independent reviewer verifies acceptance criteria, evidence or command reproducibility, secret safety, and unresolved-risk statements. Status changes from `draft` to `in_review` only after required fields are populated, and to `approved` only after the verification record is retained. Superseded documents link to the replacement and remain immutable except for administrative metadata.

File names use lowercase kebab-case with a stable subject and optional version, for example `provider-operations-runbook.md` or `api-authentication-specification-v1.md`. Do not use `final-final`, secret values, personal identifiers, or timestamps as the only identity. Store source templates under `docs/`; store generated deliverables and sanitized evidence under the approved `artifacts/` or `logs/` paths according to `AGENTS.md`.
