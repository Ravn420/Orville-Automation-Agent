# Orville GUI Wireframes

## Purpose

These low-fidelity wireframes are the required pre-implementation layout checkpoint for the Orville GUI. They establish hierarchy, navigation, content regions, primary actions, responsive behavior, and state coverage without prescribing final visual styling.

## Global shell

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Orville wordmark       Search projects and runs             Help  User menu  │
├───────────────┬──────────────────────────────────────────────┬───────────────┤
│ HOME          │ Breadcrumb: Project / Run / Artifact         │ Context rail  │
│ PROJECTS      │                                              │ selection     │
│ NEW OBJECTIVE │ Main content                                 │ status        │
│ ACTIVITY      │                                              │ next action   │
│ PROVIDERS     │                                              │ evidence      │
│ SETTINGS      │                                              │ controls      │
│ HELP          │                                              │               │
└───────────────┴──────────────────────────────────────────────┴───────────────┘
```

At compact widths, the left navigation collapses into a labelled menu, the context rail moves below the main content, and the primary action remains visible without horizontal scrolling.

## Home and readiness

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Home                                      [New objective]             │
│ Welcome / current workspace                                           │
├───────────────┬───────────────────┬───────────────────────────────────┤
│ Active runs   │ Needs approval    │ Readiness                         │
│ count + link  │ count + link      │ providers / runtime / connectors  │
├────────────────────────────────────┴───────────────────────────────────┤
│ Recent projects                                                        │
│ Project | checkpoint | owner | status | next safe action               │
└──────────────────────────────────────────────────────────────────────┘
```

Empty, loading, offline, blocked, and failed states replace the relevant panel content while retaining the reason and one safe next action.

## New objective

```text
┌──────────────────────────────────────────────────────────────────────┐
│ New objective                                      [Cancel] [Review]  │
├──────────────────────────────────────────────────────────────────────┤
│ Objective textarea                                                    │
│ Deliverables                                                         │
│ Constraints / environment                 Risk level                 │
│ Acceptance criteria                                                   │
│ Assumptions discovered                                                │
│                                                                      │
│ [Save draft]                                      [Review task graph] │
└──────────────────────────────────────────────────────────────────────┘
```

Review is a separate step. It shows task dependencies, owners, capabilities, approval gates, generated paths, and acceptance checks before execution begins.

## Run and verification

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Project / Run-42        Running · updated 12:04:18        [Pause] [Cancel]   │
├───────────────────────────────────────┬──────────────────────────────────────┤
│ Task graph / timeline                 │ Selected task                        │
│ ✓ Intake                              │ Code Synthesis                       │
│ ✓ Research                            │ owner, capability, inputs            │
│ → Code synthesis                      │ status, dependencies, output paths   │
│ ○ Verification                        │ [Open evidence] [View logs]          │
│ ○ Delivery                            │                                      │
├───────────────────────────────────────┴──────────────────────────────────────┤
│ Events | Evidence | Approvals | Artifacts | Verification                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

Verification replaces controls with acceptance criteria, evidence, test results, defect recording, and pass/fail/needs-review actions. Approval and publication actions remain separate from ordinary inspection.

## Artifact and provider surfaces

```text
Artifacts:  [Version] [Preview] [Manifest] [Download] [Compare]
Providers:  provider | model | privacy mode | health | remediation
```

Artifact previews identify source/export relationships, revision, checksum, warnings, and approval state. Provider surfaces show safe metadata only and never expose credentials, prompts, or raw provider errors.

## Wireframe acceptance checks

The implementation must preserve a visible current location, one primary action per surface, a clear summary/evidence/controls split, labelled empty and error states, keyboard order, compact-width stacking, and an approval boundary for external or durable actions. These wireframes must be reviewed before high-fidelity implementation begins.
