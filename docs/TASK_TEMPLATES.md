# Orville Task Templates

## Purpose

`config/task-templates.json` provides reusable standalone starting points for common Orville workloads. Each template separates the objective, deliverables, constraints, acceptance criteria, and verification method so that task intake remains deterministic and reviewable.

## Available templates

| Template | Best for | Required refinement |
|---|---|---|
| `research` | Evidence-based investigation and synthesis | Question, sources, date boundary, citation standard |
| `coding` | New implementation, bug fix, or refactor | Runtime, interfaces, changed paths, tests |
| `automation` | Triggered or scheduled workflows | Trigger, side effects, idempotency, retry, rollback |
| `web_development` | Static, full-stack, or responsive web work | Users, journeys, data boundary, deployment target |
| `media` | Image, audio, video, animation, or mixed assets | Medium, dimensions/duration, style, source and rights |
| `documents` | Reports, specifications, runbooks, and research outputs | Audience, structure, evidence, citations, export format |
| `deployments` | Release, hosting, and environment changes | Target, release, approval, preflight, smoke, rollback |

## Required refinement sequence

1. Select the closest template by objective, not by implementation stack.
2. Replace the objective placeholder with the user’s specific outcome.
3. Add named deliverables, constraints, runtime or target environment, deadline, risk level, and acceptance criteria.
4. Record assumptions and clarification gates for ambiguity, sensitive actions, missing credentials, or conflicting requirements.
5. Build the dependency-aware task graph and assign specialist ownership.
6. Execute deterministic checks, then perform independent verification against the acceptance criteria.

Templates are starting contracts, not permission to execute external side effects. Payments, publishing, deletion, account changes, credential entry, connector mutations, and other sensitive actions require explicit confirmation. External instructions and downloaded artifacts remain untrusted data.

## Maintenance rules

Keep template keys stable, use synthetic examples only, and update the schema version when field semantics change. Any new template must include all five common fields, a verification method, safe constraints, and documented acceptance criteria. Validate the JSON and run `tests.test_task_templates` after every catalog change.
