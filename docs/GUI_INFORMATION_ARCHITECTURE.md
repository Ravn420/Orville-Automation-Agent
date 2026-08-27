# GUI Information Architecture and User Journeys

## Purpose

This document defines the target users, primary workflows, navigation model, information architecture, and user journeys for Orville’s GUI. The model supports standalone local operation first, keeps provider and connector boundaries visible, and does not authorize external side effects.

## Target users

| User | Goal | Primary needs | Risk boundary |
| --- | --- | --- | --- |
| **Builder** | Turn a software objective into a runnable project. | Objective intake, assumptions, task graph, generated files, tests, preview, and handoff. | Cannot publish, deploy, or alter external systems without approval. |
| **Operator** | Configure runtimes and keep executions healthy. | Provider/model inventory, readiness, logs, schedules, recovery, and safe diagnostics. | Secrets are referenced, never displayed; destructive recovery requires approval. |
| **Reviewer** | Verify outputs against acceptance criteria. | Evidence, diffs, citations, test results, approvals, risks, and artifact history. | Review decisions are distinct from implementation ownership. |
| **Project owner** | Control scope, access, and delivery decisions. | Project settings, members, permissions, approvals, retention, export, and rollback. | Account, publication, and deployment changes require explicit authorization. |

The interface must provide a usable path for a first-time Builder without requiring command-line knowledge while retaining detailed evidence and diagnostics for Operators and Reviewers.

## Primary workflows

### 1. Configure and check readiness

The user opens **Settings → Providers and runtimes**, reviews detected capabilities and blocked dependencies, supplies configuration through approved secret references or environment variables, and runs a safe health check. The GUI shows status, scope, and remediation without exposing credentials or prompts. A readiness summary links to the affected project or task.

### 2. Create and execute an objective

The Builder selects **New objective**, enters the objective, deliverables, constraints, environment, risk level, and acceptance criteria, then reviews assumptions and the generated task graph. The user confirms the plan before execution. The execution view shows ordered tasks, owners, dependencies, approvals, progress, failures, and resumable state. The user can inspect a task without losing the overall run context.

### 3. Review and verify an output

The Reviewer opens **Projects → task → verification**, compares the artifact with acceptance criteria, inspects evidence and test results, records a verification decision, and returns actionable defects or approves the checkpoint. The UI clearly separates generated content, source evidence, analysis, assumptions, and recommendations.

### 4. Preview and deliver an artifact

The Builder or Reviewer opens **Projects → artifacts**, selects a versioned artifact, launches a local preview or export inspection, reviews the manifest and risks, and downloads or hands off the accepted files. Publish, public visibility, deployment, and external sharing are separate actions behind explicit approval gates.

### 5. Recover a failed or interrupted run

The Operator opens **Activity → run**, identifies the failed or interrupted checkpoint, reads the bounded error and remediation, reviews dependent-task impact, and chooses resume, retry, cancel, or rollback when authorized. The interface preserves prior evidence and makes state transitions auditable.

## Navigation model

The primary navigation is stable and task-oriented:

| Navigation item | Scope | Default landing content |
| --- | --- | --- |
| **Home** | Cross-project overview. | Recent objectives, blocked approvals, failed checks, and active runs. |
| **Projects** | Project and artifact workspace. | Projects list, current checkpoint, tasks, artifacts, preview, verification, and delivery. |
| **New objective** | Objective intake. | Structured intake form and assumption review. |
| **Activity** | Execution history. | Runs, events, approvals, failures, and resumable checkpoints. |
| **Providers** | Models, runtimes, connectors, and readiness. | Capability inventory, health, privacy mode, and safe remediation. |
| **Settings** | User and project configuration. | Workspace, members, notifications, retention, and non-secret configuration. |
| **Help** | Contextual guidance. | Local documentation, command references, and limitations. |

A contextual rail may show the selected task, artifact, source, or approval without changing the primary route. Breadcrumbs identify `project → task/run → artifact/verification` and support return to the prior context. Destructive or external actions are never hidden behind navigation labels.

## Information architecture

The core object hierarchy is:

```text
Workspace
└── Project
    ├── Objective
    │   └── Run
    │       ├── Task graph and events
    │       ├── Approvals and verification
    │       └── Artifacts and checkpoints
    ├── Providers, runtimes, and connector references
    └── Members, permissions, settings, and retention
```

Each detail view uses a consistent three-part layout: **summary** (status, owner, current checkpoint, and next action), **evidence** (events, files, citations, tests, and verification), and **controls** (safe local actions first, approval-gated external actions clearly separated). Status labels use text and icons in addition to color and expose timestamps and safe identifiers.

The object model must preserve stable URLs or route state for project, run, task, artifact, and verification records. Empty states explain what is missing and provide the next permitted action. Loading, blocked, failed, stale, and unavailable states are explicit rather than represented as empty content.

## User journeys and acceptance criteria

| Journey | Entry | Success state | Required checks |
| --- | --- | --- | --- |
| First objective | Home → New objective | A reviewed task graph is ready or a clear blocker is shown. | Required fields, assumptions, risk, and acceptance criteria are visible before execution. |
| Active execution | Project → Run | User can follow progress and inspect any task. | Dependency order, owner, status, events, approval gates, and cancellation/resume state remain coherent. |
| Verification | Run → Verification | A reviewer records pass, fail, or needs-review with evidence. | Acceptance criteria and defects are linked to the artifact and checkpoint. |
| Artifact preview | Project → Artifacts → Version | User can inspect a local preview and retrieve the correct version. | Revision ID, checksum, source/export relationship, preview status, and warnings are visible. |
| Provider issue | Providers → Readiness | User understands the limitation and local remediation. | No secret values, prompts, or external side effects appear in diagnostics. |
| Interrupted run | Activity → Run | User resumes, retries, cancels, or escalates safely. | Durable checkpoint, failure reason, dependent impact, and action approval are recorded. |

## Cross-cutting interaction rules

The GUI must preserve context during refreshes, show the last-updated time for asynchronous state, prevent duplicate submissions with idempotent action state, and provide keyboard-accessible focus and labeled controls. User-visible errors include a safe operation identifier and remediation; raw exceptions and credential-bearing responses remain hidden. Privacy mode, provider location, approval state, and publication scope are visible before a consequential action.

The first release prioritizes objective intake, execution monitoring, verification, artifact preview, and readiness. Collaboration, hosted access, live browser control, and provider-specific deployment remain separate capabilities and must appear as unavailable or gated when not configured.
