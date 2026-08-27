# Orville Feature Matrix

**Purpose:** Compare Orville's current implementation with capabilities publicly described by Replit Agent, Base44, Cursor Cloud Agents, CrewAI, and LangGraph. This matrix is an implementation plan, not a claim that Orville is identical to any product.

## Current status

| Capability family | Comparable product signal | Orville status | Next implementation boundary |
|---|---|---|---|
| Instruction-first natural-language task intake | Replit Agent and comparable coding agents begin from a natural-language request | Implemented | Add reusable task templates and brief history |
| Explicit planning before execution | Cursor guidance, CrewAI task orchestration, LangGraph graph runtime | Implemented in agentic code flow | Add editable plan preview and approval before execution |
| Multi-agent role delegation | CrewAI crews and role-based agents | Implemented in code-generation graph | Add visible agent registry, role configuration, and handoff inspection |
| Persistent graph state and resumability | LangGraph durable execution and persistence | Implemented for local checkpoints | Add replay/time-travel view and conflict-safe resume |
| Streaming execution visibility | Replit interactive agent experience and LangGraph streaming | Implemented | Add per-agent channels, token/latency telemetry, and reconnect controls |
| Generated code and artifact management | Replit app workspace and Cursor artifacts | Implemented partially | Add parsed files, diff view, download, and guarded write-to-workspace |
| Repository/project context | Coding agents inspect an existing codebase | Intake text only | Add folder selection, indexed file tree, ignore rules, and context budget display |
| Terminal and test execution | Replit Agent self-tests; coding agents use tools | Backend primitives documented, GUI not complete | Add allowlisted terminal runner, output stream, timeout, and approval gate |
| Reflection and self-repair loop | Replit Agent tests and fixes its work; agent frameworks use verification loops | Verification task exists | Add test-run tool, failure feedback handoff, bounded repair iterations |
| Human approval and checkpoints | LangGraph human-in-the-loop; agent coding review flows | API primitives exist | Add plan approval, file-write approval, and destructive-action confirmation UI |
| Database, authentication, and realtime app services | Base44 built-in backend, auth, realtime, integrations | Not a default Orville service | Keep as optional project adapters; do not conflate orchestration with hosted BaaS |
| Third-party integrations and secrets | Replit integrations and Base44 connectors | Provider integrations implemented | Add connector registry, OAuth boundary, secret references, and health diagnostics |
| Automations and scheduled workflows | Replit agents/automations, Base44 workflows, CrewAI flows | Backend modules exist, product UI incomplete | Add workflow builder, cron/interval schedules, retries, idempotency, and run history |
| Collaboration and project members | Base44/GitHub workflow and team-oriented agent platforms | Backend member routes exist, GUI incomplete | Add members, roles, shared run history, and activity feed |
| Observability and evaluation | LangSmith/CrewAI observability and Replit testing | Modules and event stream exist | Add traces, metrics, cost/latency summaries, evaluation cases, and export |
| Capability discovery | Manus-style runtime/tool availability visibility | Implemented through `/api/v1/capabilities` and Settings status panel | Add live refresh, per-provider telemetry, and capability-specific setup actions |
| Public-web research | Manus research and browser-assisted information gathering | Bounded allowlisted fetch plus cited research catalog implemented | Add HTML extraction, browser-session adapter, and source-quality evaluation |
| CSV data profiling | Manus data analysis workflows | Implemented through `/api/v1/data/profile` using local CSV analyzer | Add visualizations, larger-file streaming, and exportable analysis artifacts |
| Deployment and hosting | Replit deployment; Base44 hosting/custom domains | Windows/local packaging priority | Add local service packaging checks, export bundle, and optional deployment adapters |
| Standalone Windows executable | User requirement, not a direct competitor feature | Packaging assets exist, final integrated build pending | Bundle GUI, API, launcher, config validation, and first-run diagnostics |

## Source-backed findings

Replit's official Agent page describes natural-language app building, web-aware refinement, secure integrations, self-testing and repair, and building agents or automations.[1] Base44's official developer page describes a backend with database, authentication, realtime sync, integrations, server-side functions, and hosting, plus deployment from an IDE or AI agent.[2] Cursor's official cloud-agent documentation describes remote/background agent workflows and artifacts.[3] CrewAI documents role-based agents, crews, memory, guardrails, knowledge, and observability.[4] LangGraph documents durable execution, streaming, persistence, and human-in-the-loop controls.[5]

## Implementation priority

The highest-value missing slice for Orville's stated purpose is **repository-aware code completion**: select or describe a project, inspect safe file context, show an editable plan, run bounded tools and tests, stream agent output, present diffs, request approval, and persist verified artifacts. Database/auth/realtime hosting features should remain optional adapters because they are product-backend capabilities rather than prerequisites for Orville's orchestration engine.

## References

[1]: https://replit.com/products/agent "Replit Agent — official product page"
[2]: https://base44.com/developers "Base44 for Developers — official developer page"
[3]: https://cursor.com/docs/cloud-agent "Cursor Cloud Agents — official documentation"
[4]: https://docs.crewai.com/ "CrewAI Documentation — official documentation"
[5]: https://docs.langchain.com/oss/python/langgraph/overview "LangGraph Overview — official documentation"
