# Orville Manus-Like Capability Parity Report

## Executive status

Orville is a standalone Windows agentic coding and orchestration platform. It is not a literal clone of Manus: proprietary hosted models, managed cloud computers, first-party connectors, and cloud infrastructure cannot be reproduced without equivalent external services. The implementation target is functional equivalence where local Windows processes, user-configured APIs, open-source libraries, and explicit approvals can provide the same class of workflow.

## Implemented capabilities

| Capability family | Current implementation | Verification status |
|---|---|---|
| Instruction-first task intake | New Task screen creates agentic planning, implementation, and verification graphs | Verified through agentic stream regression |
| Provider-neutral generation | Gemini, Ollama, Blackbox, Stable Horde text, Anthropic, major hosted aliases, and generic OpenAI-compatible/local endpoints | Provider registration and redaction regressions pass |
| Live run visibility | Background execution, streamed model deltas, events, generated-code viewer, artifacts, cancellation, and task approvals | Stream regression and frontend build pass |
| Projects and personal agent | Durable projects, task history, project instructions, project memory, local Windows agent profile, pause/resume status | Shell API regression passes |
| Repository-aware coding | Bounded workspace registration, file indexing, file reads, unified diffs, approved commands, timeouts, and bounded repair authorization | Workspace tests and smoke tests pass |
| Capability discovery | Authenticated `/api/v1/capabilities` route plus Settings capability-status panel | Capability regression passes |
| Research and data foundations | Allowlisted public-web fetch, cited source catalog, research notes, CSV profiling, project ZIP export | Research and security regressions pass |
| Workflow foundations | Durable workflow versions, manual/scheduled/webhook trigger types, idempotency keys, retries, dead-letter status, and interval schedules | Module-level tests pass |
| Security and governance | Bearer authentication, rate limiting, path boundaries, secret redaction, approval gates, audit records, security findings, release gates | Security/readiness tests pass |

## Partial or blocked capabilities

| Capability | Boundary | Required next implementation |
|---|---|---|
| Browser operator | The adapter is explicitly blocked until a browser session and user handoff are configured | Add a safe Playwright/browser-session adapter with visible takeover, domain allowlists, and action audit records |
| Remote Git | Capability contract exists but credentials and repository permissions are not configured | Add Git provider connector, branch/diff/pull-request operations, and write approval |
| Deployment | Local preview and export foundations exist; production deployment is intentionally blocked | Add provider-specific deployment adapters, secret references, release approval, rollback, and health checks |
| Object storage | Adapter contract exists but no storage credentials are configured | Add S3-compatible storage connector with retention and redaction policy |
| Team collaboration | Local membership and project member routes exist | Add shared activity feed, invitations, role UI, and task-level sharing |
| Workflow UI | Backend workflow and schedule primitives exist | Add visual workflow builder, schedule editor, retries, run history, and webhook configuration |
| Rich artifact production | Code, Markdown, CSV profiling, ZIP export, and research records exist | Add document, spreadsheet, presentation, chart, audio, image, and video generation adapters |
| Evaluation and observability | Governance, traces, telemetry, and evaluation helpers exist | Add trace viewer, cost/latency dashboards, evaluation cases, exports, and replay/time-travel |
| Always-on operation | The personal agent remains available while the Windows host and Orville services run | Add Windows service/task-scheduler install, crash recovery, startup diagnostics, and durable queue processing |

## Product boundary

The local Windows executable should expose an explicit capability state for every subsystem: ready, configured, awaiting approval, blocked, degraded, or unavailable. This is preferable to presenting controls that silently fail. The GUI should continue to start at New Task, with the collapsible sidebar providing Personal Agent, Projects, Task history, Settings, Control Room, Agent Workspace, Runs, Artifacts, Project State, API Docs, and Integrations.

## Official references

[1]: https://manus.im/docs/introduction/welcome "Manus Documentation — Welcome"
[2]: https://manus.im/docs/features/projects "Manus Documentation — Projects"
[3]: https://replit.com/products/agent "Replit Agent — official product page"
[4]: https://base44.com/developers "Base44 for Developers — official developer page"
[5]: https://docs.crewai.com/ "CrewAI Documentation — official documentation"
[6]: https://docs.langchain.com/oss/python/langgraph/overview "LangGraph Overview — official documentation"
