# Prioritized Backlog

## Purpose and scope

Orville maintains a machine-readable backlog for existing roadmap items that require follow-up. Each record links to the exact roadmap wording and records status, owner, priority, impact, effort, risk, dependencies, acceptance tests, acceptance evidence, artifact references, and any blocker. The backlog is a planning artifact; it does not claim work is complete and does not change `TODO.md` status by itself.

The current catalog is `config/priority-backlog.json`. It contains existing TODO items only. A new backlog record must not be used to create an unapproved task; it must identify an existing roadmap item or be added through an explicit roadmap decision.

## Required fields

| Field | Requirement |
|---|---|
| `id` | Stable, unique identifier for the roadmap item. |
| `todo_text` | Exact or unambiguous reference to the existing TODO item. |
| `status` | One of `planned`, `in_progress`, `blocked`, or `completed`; it must agree with the linked TODO item. | 
| `owner` | Named agent or role accountable for the roadmap item. |
| `priority` | `critical`, `high`, `medium`, `low`, or `deferred`. |
| `impact` | Integer from 1 (low) to 4 (critical). |
| `effort` | Integer from 1 (less than one day) to 4 (more than one week). |
| `risk` | Integer from 1 (low) to 4 (critical). |
| `dependencies` | Explicit prerequisites, approvals, or evidence. |
| `acceptance_test` | Reproducible commands or checks that must pass before completion. |
| `acceptance_evidence` | Concrete validation or review artifacts required before completion. |
| `artifact_reference` | Paths to the documentation, tests, state, or generated evidence supporting the item. |
| `blocker` | Required for blocked items and omitted when no blocker exists. |

## Prioritization method

The default score is `impact + risk - effort`. Higher scores are considered first, but dependencies and blockers override numerical ordering. A critical security or recovery dependency can therefore precede a higher-scoring feature. `deferred` means the item is intentionally not actionable until its stated dependency or approval exists.

Scores are planning signals, not predictions of delivery time or business value. They must be reviewed with the task owner and adjusted when scope, environment, evidence, or risk changes. Do not infer priority from agent identity, personal performance, or unverified assumptions.

## Status and lifecycle

A backlog record may be `planned` when it is actionable but unclaimed, `in_progress` only after the corresponding TODO item is claimed, `blocked` when a named prerequisite or approval prevents safe work, and `completed` only after implementation, focused validation, state updates, and TODO completion. The backlog and `TODO.md` must agree before a milestone is closed.

For each completed item, retain the implementation paths, validation command and result, reviewer or second verification evidence, assumptions, and unresolved risks. For blocked items, preserve the blocker and do not bypass it by broadening permissions, deleting files, using credentials, or changing scope.

## Review cadence

Review the highest-priority actionable items at each milestone and review all records after material architecture, environment, security, dependency, or release changes. Re-score an item when a dependency changes, a failure pattern recurs, a rollback risk increases, or new evidence changes impact or effort. A quarterly roadmap review or equivalent milestone review should reconcile the backlog with `TODO.md`, `STATE.md`, `TASK_GRAPH.md`, and release readiness.

## Validation

Validate the catalog with a JSON parser and a focused schema check. Confirm that every record has the required fields, scores are within range, statuses and priorities use the allowed vocabulary, IDs are unique, owners, dependencies, acceptance tests, acceptance evidence, and artifact references are non-empty, blocked records explain their blocker, and completed records point to retained evidence. This review does not execute tasks, alter the filesystem outside the repository, or access external services.
