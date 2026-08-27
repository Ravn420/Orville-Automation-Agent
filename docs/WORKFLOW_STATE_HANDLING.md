# Consistent Workflow-State Handling

## Scope

This contract defines the user-facing state vocabulary for the native desktop execution monitor and verification view. Each state has a concise title, an explanation, and a bounded next action so operators can distinguish absence of data from service failure, blocked work, partial completion, and active long-running work.

## State vocabulary

| State | Meaning | Required recovery or next action |
|---|---|---|
| Loading | A request is in progress. | Wait briefly or refresh. |
| Empty | No run ID, tasks, or events are available. | Start a workflow or enter a different run ID. |
| Offline | The local service could not be reached. | Start the local service and try again. |
| Blocked | Approval or another required condition prevents progress. | Review the reason before continuing. |
| Failed | The operation could not complete. | Review safe details and retry when appropriate. |
| Partial | Some steps completed while others need attention. | Review completed and remaining steps. |
| Long-running | Work remains active beyond an immediate response. | Continue monitoring or use permitted controls. |
| Ready | Data is available for review or permitted action. | Choose the next permitted action. |

## Interaction rules

Loading preserves the existing layout and replaces stale status text with a clear loading message. Empty, offline, blocked, failed, and partial states remain actionable without exposing raw exceptions, credentials, request payloads, or provider response bodies. Long-running work remains distinguishable from failure and exposes the existing monitor controls. State messages use text and recovery instructions rather than color alone.

The monitor and verification view use the same classifier and copy formatter. An unavailable run is treated as offline, a missing run ID or empty task/event collection is treated as empty, approval waits are blocked, active statuses are long-running, mixed task outcomes are partial, and all-failed outcomes are failed.

## Acceptance checks

Focused tests verify all state names, deterministic classification, loading and empty transitions in both views, bounded recovery guidance, and secret-safe wording. Python compilation must pass for the GUI and test module. Live service outage drills and visual/readability review remain environment-dependent checks.
