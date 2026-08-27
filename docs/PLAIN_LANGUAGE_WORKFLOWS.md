# Plain-language primary workflows

## Purpose

Orville’s primary workflows are written for operators who want to describe an outcome, not configure an agent framework, construct a task graph, or learn a provider API. Technical details remain available in specialist views, but they are not prerequisites for starting or reviewing work.

## Primary workflow

| User-facing step | Plain-language action | Technical detail kept behind the surface |
|---|---|---|
| 1. Describe | “Tell Orville what you need, in your own words.” | Objective intake and task classification. |
| 2. Prepare | “Orville prepares a plan and asks before sensitive actions.” | Task graph, dependencies, clarification gates, and approvals. |
| 3. Work | “Orville carries out the work and shows progress.” | Agent assignments, provider routing, handlers, tools, retries, and checkpoints. |
| 4. Review | “Review the result, evidence, and any remaining risks.” | Verification handlers, citations, artifact lineage, visual checks, and residual-risk records. |

## Vocabulary

| Technical term | User-facing wording | Where the technical term may appear |
|---|---|---|
| Agent | Worker or specialist | Execution details and event history. |
| Task graph | Plan | Task-plan detail view. |
| Provider/model | Where the work runs | Model Manager. |
| API endpoint | Connection address | Advanced provider setup. |
| Checkpoint | Saved progress | Execution Monitor details. |
| Verification gate | Review check | Verification & Review view. |

## Interaction rules

The home workspace leads with one question, one primary action, and optional attachment/details controls. Overview opens a “How Orville works” explanation. Active tasks opens the execution monitor. Model Manager is available when users need to choose where work runs, and Verification opens the evidence review. Technical terms are not required in the composer, and advanced configuration remains discoverable through dedicated views rather than mixed into the first-run path.

The plain-language path must preserve the existing safety behavior: sensitive actions still require approval, credentials remain outside user-facing output, failures use safe operation-aware messages, and the backend remains authoritative for policy enforcement. Copy describes the workflow without promising a provider, agent, or API result that has not been verified.

## Acceptance checks

A first-time operator can submit a goal without knowing agent, graph, provider, or API terminology; can identify where to follow progress; can find model/provider configuration when needed; can review evidence and risks; and can understand why an approval is requested. Keyboard access, readable status text, responsive layout, and safe error feedback remain governed by the visual design and accessibility criteria.
