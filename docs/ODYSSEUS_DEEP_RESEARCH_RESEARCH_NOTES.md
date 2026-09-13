# Odysseus Deep Research Research Notes

**Reviewed:** 2026-09-04

## Sources

1. Odysseus AI, “Deep Research: Search, Sources & Privacy,” https://odysseusai.dev/deep-research
2. Odysseus AI GitHub repository, https://github.com/odysseus-dev/odysseus

## Findings

The public Odysseus documentation describes Deep Research as a **multi-step web-research workflow** rather than a single prompt. Its documented loop depends on search quality, source fetching, model context, memory/document context, and report generation. It recommends beginning with bounded questions and fewer sources, then increasing scope only after one complete loop works reliably.

The source boundary is explicit: a bundled SearXNG service is the default search backend, while optional providers include Brave, Google Programmable Search, Tavily, Serper, and DuckDuckGo. Queries leave the local machine through the chosen search backend, and hosted model providers create an additional privacy boundary. Source quality should be diagnosed separately from model quality.

The workflow should therefore expose research configuration, query planning, source discovery, source reading, intermediate synthesis, final report generation, citations, and privacy status as separate visible stages. Orville should bound source count, excerpt size, context budget, and timeouts, and should preserve source URLs and verification states in project-scoped files.

The public repository describes Deep Research as “multi-step web research with source reading and report generation.” The repository structure also demonstrates explicit separation of core services, scripts, specifications, source, tests, and website resources. This supports implementing Orville’s Deep Research as a dedicated engine and tab rather than embedding it into ordinary chat or the existing run monitor.

## Design consequences for Orville

| Requirement | Orville implementation direction |
|---|---|
| Dedicated research workflow | Add a dedicated Deep Research tab with query, scope, source limit, provider, privacy boundary, and report format controls. |
| Multi-step execution | Model explicit stages: plan, search, shortlist, fetch, extract, synthesize, verify, report. |
| Source-backed output | Persist URL, title, publisher, retrieved time, excerpt digest, verification state, and citation positions. |
| Bounded reliability | Enforce source-count, excerpt-size, context, timeout, retry, and output-size limits. |
| Privacy | Show whether queries, sources, private project files, or hosted models leave the local boundary. |
| Project organization | Store reports, source records, evidence, and exports under `project_files/<project-slug>/`. |
| Failure handling | Preserve partial results and actionable recovery states for provider failure, empty sources, context overflow, and rate limits. |

This is an implementation reference, not a claim that Orville should copy proprietary code or branding. The goal is functional equivalence of the visible workflow and safety boundaries.
