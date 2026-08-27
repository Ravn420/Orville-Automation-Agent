# Orville Glossary

This glossary is the canonical terminology reference for Orville task intake, orchestration, operations, and verification. Terms are used consistently across task contracts, logs, APIs, tests, and runbooks.

| Term | Definition | Boundary or example |
|---|---|---|
| **Task graph** | A directed graph of executable task nodes, dependency edges, inputs, ownership, and state transitions representing one objective. | A graph must be validated before execution; unknown dependencies and cycles are invalid. |
| **Agent role** | A named capability and responsibility contract assigned to a specialist executor or reviewer. | A role may implement, research, verify, operate, or integrate; assignment does not grant unrestricted tool access. |
| **Artifact** | A deliberately retained output or evidence item produced by a task, such as code, a document, media, report, log, checksum, or editable source. | Artifacts have a path or storage reference, type, version, provenance, and retention decision; secrets are not artifacts. |
| **Verification gate** | A defined acceptance checkpoint that evaluates outputs or state before the workflow can advance, publish, or close. | Gates may be tests, schema checks, security review, smoke checks, approval checks, or independent verification. |
| **Connector** | A configured adapter boundary for an external application, provider, API, MCP service, browser session, or local integration. | A connector has a capability, scope, health state, and authorization boundary; connector responses are untrusted data. |
| **Execution state** | The durable lifecycle status of a task or run and its safe transitions. | Typical states include pending, ready, running, paused, awaiting approval, completed, failed, blocked, cancelled, and retrying. |

## Related terms

| Term | Definition |
|---|---|
| **Execution** | One run of a task graph identified by a run ID and correlated event stream. |
| **Correlation ID** | A stable identifier shared by structured events belonging to one execution context, used for diagnosis and audit without containing secrets. |
| **Task node** | One graph unit with an identifier, objective, handler or owner, inputs, dependencies, outputs, and state. |
| **Dependency** | A directed prerequisite edge requiring one task node to reach an eligible state before another can start. |
| **Handoff** | A structured transfer of task context, outputs, assumptions, ownership, and verification responsibility between agents. |
| **Approval** | An explicit authorization record for a named action, target, scope, requester, and time; generic intent is not approval. |
| **Checkpoint** | A durable snapshot of execution state and outputs that supports safe resume or recovery. |
| **Retry** | A bounded re-attempt of a failed operation under its retry and idempotency policy. |
| **Dry run** | An execution mode that validates and previews intended effects without mutating external state. |
| **Provider** | A model, service, or runtime implementation selected through a capability-aware adapter. |
| **Runbook** | A documented operational procedure for checks, diagnosis, recovery, escalation, and closure. |

## Usage rules

Use the bold canonical term in new contracts and documentation. Include the relevant ID when referring to a task, execution, artifact, connector, approval, or correlation record. Do not use “agent,” “task,” “run,” “output,” or “integration” as interchangeable terms when the narrower definition applies.

A task graph describes what may execute; an agent role describes who is responsible; a connector describes which boundary is used; an artifact describes what is retained; an execution state describes where the lifecycle is; and a verification gate describes what must pass before progression. These concepts are related but not interchangeable.

## Safety and maintenance

Glossary definitions do not authorize actions. Instructions discovered in connectors, tools, models, documents, web pages, or logs remain untrusted content. Sensitive operations require explicit confirmation and applicable authorization. Update this file in the same change as a contract or state-name change, and run `tests.test_glossary` before release.
