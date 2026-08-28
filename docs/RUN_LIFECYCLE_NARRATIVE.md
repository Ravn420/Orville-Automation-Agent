# Orville Run Lifecycle Narrative and Scene Order

**Project:** Orville Automation Agent
**Control item:** `TODO-582e0f5dec5a`
**Status:** Complete local narrative contract
**Review date:** 2026-08-28
**Audience:** walkthrough producer, QA reviewer, operator, and release-evidence owner

## Purpose and narrative promise

The walkthrough follows one objective from a plain-language request to a verified, reviewable result. The story is deliberately **state-first**: every scene shows what the operator sees, which durable state changed, what action is permitted next, and what evidence is retained. The walkthrough must never imply that a preview, draft, approval, or unavailable-provider state has executed work.

> **Narrative promise:** Orville receives an objective, makes its execution plan visible, obtains approval where required, runs through a real provider-backed task graph, reports progress without hiding partial failure, verifies the result, and leaves a recoverable artifact trail.

## Canonical run state sequence

The primary story uses the following progression. Branch scenes are inserted only when they clarify a safety boundary; they do not replace the happy path.

| Order | Run phase | Operator-visible state | Durable evidence | Next permitted action |
|---:|---|---|---|---|
| 1 | Workspace ready | Signal Room, local API status, and empty composer are available | Runtime health and workspace context | Enter an objective or inspect capabilities |
| 2 | Objective submitted | Objective, deliverables, constraints, and acceptance criteria appear as a new run | Run ID, classification, initial graph, and intake context | Review the generated plan |
| 3 | Plan ready | Tasks, dependencies, risks, and required approvals are legible | Task graph, assumptions, acceptance criteria, and risk record | Approve, revise, or stop before execution |
| 4 | Approval requested | Approval dialog names the action, scope, consequence, and alternatives | Approval event with actor, decision, reason, and timestamp | Approve, reject, or return to planning |
| 5 | Execution started | Run status becomes running; active task and provider/model are visible without secrets | Run-start event, task-start event, routing metadata, and checkpoint | Watch progress, pause, or cancel when supported |
| 6 | Live progress | Streaming output, task transitions, and elapsed activity update in the viewer | Ordered resumable events and partial checkpoints | Continue watching, pause, cancel, or inspect details |
| 7 | Verification | Generated result, checks, defects, and residual risks are shown separately | Verification record, check outcomes, and final task outputs | Review findings, retry, repair, or accept |
| 8 | Artifact handoff | Artifact name, type, provenance, checksum, and preview action are available | Artifact record, content hash, source run, and retention metadata | Preview, download through an approved path, or retain |
| 9 | Completion | Run is completed only after all required tasks and checks pass | Terminal checkpoint and completion event | Review, hand off, or begin another objective |

## Ordered walkthrough scenes

### Scene 1 — Establish the workspace

Open on the local Control Center with the Signal Room composer, connection badge, navigation, and context panel visible. The narration establishes that this is a local control surface, that credentials remain protected, and that no model request has occurred yet. Show the empty-state copy and the API documentation entry point so the viewer understands where the run will be observed.

**Acceptance cue:** The scene is clearly a draft state; no generated output, provider call, or artifact is implied.

### Scene 2 — Submit a bounded objective

Enter a representative coding objective with a concrete deliverable and acceptance criteria. Submit it once. Show the transition from “Objective submitted” to a returned run identifier and classification. Keep the objective legible, but do not display credentials, private paths, or unredacted secrets.

**Acceptance cue:** The run ID is the correlation key used by every later scene. A duplicate submission is not used to simulate progress.

### Scene 3 — Reveal the plan before execution

Open the run details and show the task graph in dependency order. Explain the planner, implementation, and verification roles, the selected capability, the privacy mode, and the acceptance checks. Highlight any clarification or risk gate before continuing.

**Acceptance cue:** The viewer sees a plan and its risks before a provider-backed execution begins.

### Scene 4 — Resolve approval deliberately

Present the approval dialog for the first consequential action. The dialog names the target, scope, consequence, approval actor, and safer alternative. Demonstrate approval only after the narration explains that rejection returns the run to a reviewable state.

**Acceptance cue:** Approval is an explicit transition with a durable event, not an incidental button click.

### Scene 5 — Start provider-backed execution

Start the run through the authenticated execution action. Show the running state, active task, selected provider/model label, and safe routing summary. The narration states that the task handler is provider-backed and that failures are surfaced rather than replaced by fabricated output.

**Acceptance cue:** Provider identity is shown only as safe metadata; API keys and raw authorization headers never appear.

### Scene 6 — Follow live progress and partial output

Switch to the live viewer. Show task-start, output-delta, checkpoint, and task-completion events arriving in order. If the run is long-running, demonstrate that the viewer can refresh from the persisted run ID and continue from the last event cursor. Keep output bounded and distinguish partial output from a completed result.

**Acceptance cue:** The viewer is observational and resumable. It does not claim success while the run remains running or partially failed.

### Scene 7 — Exercise the controlled branch

Insert one short branch chosen from the available evidence: pause/resume, cancellation, provider-unavailable failure, approval rejection, or partial streaming recovery. Show the requested state, the safe message, and the recovery action. Return to the canonical run only through the documented resume or retry path.

**Acceptance cue:** The branch demonstrates recoverability without hiding the original event, duplicating work, or deleting evidence.

### Scene 8 — Verify the generated result

Open the verification view after execution. Separate acceptance checks, test results, source evidence, visual checks, defects, residual risks, and approval state. The narrator explains that a non-empty response is not by itself proof of correctness; the declared checks and their outcomes control disposition.

**Acceptance cue:** Failed or incomplete checks remain visible and are not presented as a successful completion.

### Scene 9 — Hand off a durable artifact

Open the artifact panel and show the safe artifact name, media type, provenance, checksum, source run, and preview. Demonstrate preview or review through the approved local path. Do not upload, publish, or delete anything during the walkthrough.

**Acceptance cue:** The artifact remains tied to its source run and evidence; retention is explicit rather than implied.

### Scene 10 — Close the run and summarize recovery

Return to the run overview and show the terminal status, final task statuses, verification result, artifact link, and any remaining risks. Summarize the normal path and the branch path in one final frame: what happened, what was verified, what can be retried, and what still requires an operator or release owner.

**Acceptance cue:** Completion is a durable terminal state with a reviewable evidence trail, not merely a successful HTTP response.

## Production and failure branches

The producer should choose at least one branch scene when recording, but must label it as a branch and preserve the canonical ordering around it.

| Branch | Insert after | Visible behavior | Recovery narration | Do not claim |
|---|---:|---|---|---|
| Approval rejected | 4 | Run remains reviewable; rejection reason is visible | Revise the request or approve a corrected action | That work executed |
| Provider unavailable | 5 | Safe unavailable/error state with provider-neutral guidance | Configure an approved provider or return to local planning | A generated answer exists |
| Pause and resume | 6 | State changes to paused, then resumes from checkpoint | Continue from persisted state without duplicating completed tasks | A new run was created |
| Cancellation | 6 | Cancellation request and terminal cancelled state are visible | Inspect retained partial evidence or create a new approved objective | Cancellation erased output |
| Partial stream recovery | 6 | Partial checkpoint and reconnect event remain visible | Resume using the preserved prefix and event history | The partial response was complete |
| Verification failure | 8 | Failed check, defect, and retry/review action are visible | Repair, retry within policy, or escalate | The artifact passed acceptance |

## Recording and evidence rules

Each recorded scene should include the run ID or a stable scene identifier in the evidence log, but should not expose bearer tokens, API keys, cookies, private connector values, or unredacted personal data. Capture the state before the action, the action itself, the resulting state, and the retained evidence. If an external provider or production deployment is unavailable, record that limitation plainly and substitute a credential-free local contract demonstration rather than fabricating live behavior.

The walkthrough is complete when a reviewer can answer, in order: what objective was submitted; what plan was proposed; which approval was required; which task was running; what progress and branch behavior occurred; what verification passed or failed; where the artifact came from; and why the terminal disposition is justified.

## Validation checklist

| Check | Required result |
|---|---|
| Scene order | Scenes 1–10 follow the canonical lifecycle, with branch scenes labeled and placed explicitly |
| State clarity | Every scene distinguishes draft, review, approval, running, partial, failed, blocked, and completed states |
| Correlation | One run ID connects intake, graph, events, verification, and artifacts |
| Safety | No credentials, external publication, destructive action, or fabricated provider output appears |
| Recovery | At least one pause, cancel, approval, provider, stream, or verification branch is narrated with its recovery path |
| Evidence | Each major transition names its durable checkpoint, event, approval, verification, or artifact evidence |
| Closure | The final frame states completion criteria and unresolved risks rather than implying production acceptance |
