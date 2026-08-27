# Task-Plan View Contract

## Purpose and scope

The task-plan view is the authoritative read-only projection of a generated Orville task graph. It lets an operator understand what will run, why it can run, who owns it, what is blocked, how failure recovery is bounded, and what evidence is required before completion. The view complements the execution monitor: the plan explains structure and readiness; the monitor explains live execution.

The view must remain useful when the graph is large, partially specified, paused, failed, or degraded to local execution. It must never imply that a task ran, passed, or was approved merely because it appears in the generated plan.

## Graph and task information model

| Element | Required information |
|---|---|
| Plan header | Stable plan identifier, objective summary, creation/update time, plan version, graph status, validation status, and current execution mode. |
| Task node | Stable task identifier, title, description, owner agent role, capability requirements, status, retry count/budget, verification state, and artifact references. |
| Dependency edge | Upstream task, downstream task, relationship type, readiness condition, and a clear explanation when the edge prevents execution. |
| Agent assignment | Assigned role, selected model/provider class, capability basis, workspace boundary, and assignment status. Secrets and bearer values are never displayed. |
| Blocker | Blocker category, affected task, reason, owner, required resolution, timestamp, and whether the blocker is local, provider-dependent, infrastructure-dependent, credential-dependent, or approval-gated. |
| Retry state | Attempts used, bounded maximum, last failure class, next eligible time or condition, repair action, and whether retry is safe and idempotent. |
| Verification gate | Gate name, required evidence, verifier role, status, failure reason, exception reference, and approval state. |
| Plan summary | Counts for total, ready, running, blocked, failed, waiting, completed, cancelled, and verification-pending tasks; retry and blocker counts; and the next eligible tasks. |

The graph projection is generated from the durable task and dependency records. It includes a last-refreshed timestamp and a stale-data indicator when the source cannot be refreshed. Missing required fields render as unknown or incomplete and block plan approval rather than being silently inferred.

## Status and visual semantics

| Status | Meaning and required presentation |
|---|---|
| Draft | Plan can still be revised; show validation warnings and no execution claim. |
| Ready | Dependencies and required plan fields pass local validation; show eligible tasks and verification requirements. |
| Waiting | Task is valid but awaits an upstream dependency, schedule, resource, or approval; show the exact condition. |
| Running | Execution has started; show the task and attempt identifier, not a completion claim. |
| Blocked | Execution cannot proceed; show blocker category, owner, and safe next action. |
| Failed | An attempt ended unsuccessfully; show safe failure class, retry state, and preserved evidence reference. |
| Verifying | Work completed provisionally and awaits the independent verification gate. |
| Completed | Required execution and verification evidence passed for the current version. |
| Cancelled | Execution was intentionally stopped; show who/what requested cancellation and retained evidence. |

Every status uses a text label and, where useful, an icon in addition to color. Status changes are announced to assistive technology without stealing focus. Completed and approved are distinct: approval or verification must be visible as its own gate.

## Interaction patterns

| Interaction | Required behavior |
|---|---|
| Select node | Show task details, dependencies, assignment, attempts, blockers, verification gates, and artifact links in a stable details region. Preserve selection through refresh when the node still exists. |
| Filter and search | Filter by status, owner, capability, blocker category, verification state, and retry state. Show active filters and result count; do not alter the plan. |
| Expand dependency path | Highlight upstream prerequisites and downstream impact, with a reset action that returns to the full graph. Cycles or invalid references are surfaced as validation errors. |
| Inspect blocker | Show safe reason, owner, resolution condition, and whether operator approval or external provisioning is required. Do not expose credentials or raw provider errors. |
| Inspect retry | Show bounded attempts and evidence. A retry action is available only when policy allows it and must preserve idempotency and require approval when the operation is consequential. |
| Verification review | Show required evidence, verifier, pass/fail state, exception, and approval boundary. A failed gate blocks completion presentation. |
| Refresh | Refresh the projection without changing durable task state; show stale data or refresh failure explicitly. |
| Narrow layout | Replace the graph with a dependency list or accessible tree when the graph cannot remain legible; preserve all relationships and status information. |

The view is read-only by default. Mutating controls such as approve, retry, cancel, or regenerate are explicit actions, identify their target, show consequences, and use the existing approval and authorization contracts.

## Accessibility, security, and performance

The graph has an equivalent accessible tree or tabular dependency representation. Nodes and edges have meaningful names, keyboard navigation has a predictable order, focus is visible, and the selected node is announced. The view supports compact widths, browser zoom, reduced motion, and text-only status interpretation. Large graphs use bounded rendering, progressive detail, and filtering rather than unbounded DOM or canvas work.

The client receives only safe task metadata and redacted failure classes. It does not receive provider credentials, bearer tokens, cookies, private keys, raw exception strings, or secret-bearing URLs. Authorization is enforced server-side for every plan, task, artifact, approval, retry, cancellation, and log lookup. Path and artifact links remain root-bound and size-limited.

## Acceptance and evidence

A task-plan view is accepted when a fixture graph demonstrates node and edge rendering, dependency readiness, assignment metadata, every status above, blocker categories, bounded retry display, verification-gate display, stale refresh behavior, filtering, keyboard access, accessible fallback, secret redaction, and a large-graph performance bound. Evidence records the fixture version, viewport or device class, graph size, checks performed, failures, reviewer, and exceptions.

Focused repository validation is:

    python -m unittest tests.test_task_plan_view
    python -m compileall -q tests/test_task_plan_view.py

The contract does not claim that the existing GUI has implemented this view; implementation and live visual regression remain subsequent work.

## References

- WCAG 2.2, W3C: https://www.w3.org/TR/WCAG22/
- WAI-ARIA Authoring Practices, W3C: https://www.w3.org/WAI/ARIA/apg/
- Web Content Accessibility Guidelines Understanding, W3C: https://www.w3.org/WAI/WCAG22/Understanding/
