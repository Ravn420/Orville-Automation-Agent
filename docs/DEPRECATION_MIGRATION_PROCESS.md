# Deprecation and Migration Process

This process applies to providers, model formats, public APIs, MCP protocol versions, runtime dependencies, and GUI components. A deprecation is a compatibility decision, not an informal warning: every notice has an owner, a replacement, a support window, and a removal gate.

## Required deprecation record

| Field | Requirement |
|---|---|
| Record ID | Stable identifier such as `DEP-2026-001`. |
| Component and version | Exact provider, format, API, MCP, dependency, or GUI component and affected versions. |
| Owner | Named role responsible for communication, migration support, and removal approval. |
| Reason | Security, compatibility, maintenance, performance, licensing, or product rationale without exposing secrets. |
| Replacement | Supported target and compatibility notes; “none” requires an explicit retirement decision. |
| Announced date | Date the notice becomes visible to users and integrators. |
| Last-supported date | End of normal support and the minimum migration window. |
| Removal target | Earliest release or schema version in which the old path may be removed. |
| Migration guide | Repository-relative guide, command, fixture, or API mapping that can be reproduced locally. |
| Validation | Focused compatibility tests, upgrade/downgrade checks, fixture results, and regression status. |
| Residual risk | Known users, data, or integrations that may still fail after migration. |
| Approval/evidence | Release decision, changelog entry, test evidence, and rollback plan. |

## Lifecycle

The owner first inventories callers, persisted data, configuration, connectors, generated artifacts, and GUI flows. The owner then proposes the replacement and compatibility adapter, records the deprecation with the required fields, adds a warning that identifies the replacement and removal target, and publishes a migration guide in the same change. Notices must not reveal credentials, private endpoints, or user data.

During the support window, both old and new paths are tested where feasible. The migration gate requires a representative fixture, a clean-install or upgrade check, focused tests, a full regression result, and a rollback or downgrade procedure. A removal requires confirmation that the support window elapsed, usage or caller inventory was reviewed, the replacement is available, the release owner approved removal, and the changelog and release notes identify the breaking change. If those conditions are not met, the old path remains supported or the record is explicitly blocked.

## Domain-specific requirements

| Domain | Minimum migration evidence |
|---|---|
| Provider | Endpoint/model mapping, authentication-reference compatibility, rate/error mapping, and a provider-specific fallback test. |
| Model format | Format version, checksum/provenance policy, conversion command, compatibility fixture, and rejection behavior for malformed input. |
| API | Before/after schema, versioning policy, client impact, adapter or codemod, contract tests, and rollback version. |
| MCP version | Protocol capability matrix, handshake behavior, operation allowlist review, state/compatibility checks, and safe fallback. |
| Runtime dependency | Supported Python/OS range, lock or constraint update, clean environment install, security review, and regression run. |
| GUI component | Keyboard/focus/semantics compatibility, visual states, responsive/reflow review, assistive-technology impact, and rollback path. |

## Release and rollback gates

A migration is not complete because the new code imports successfully. The evidence must show the target behavior, preservation or intentional transformation of persisted data, error and permission behavior, and absence of unintended external side effects. Failed validation leaves the record in `blocked` or `migration-required` status and prevents removal. Rollback restores the previous supported version or adapter and preserves user data; it must be tested in a disposable environment before release.

## Repository evidence

Current repository controls include provider/MCP threat-model coverage, compatibility-oriented tests, release workflow guidance, WCAG accessibility criteria, and standalone release documentation. New deprecation records should be added beside the affected component and linked from `STATE.md`, `TASK_GRAPH.md`, `CHANGELOG.md`, and `TODO.md` when they materially change release state.

## References

- [Semantic Versioning 2.0.0](https://semver.org/) — public versioning and compatibility vocabulary.
- [Python Packaging User Guide: Managing application dependencies](https://packaging.python.org/en/latest/discussions/install-requires-vs-requirements/) — dependency declaration and reproducible installation context.
- [Model Context Protocol specification](https://modelcontextprotocol.io/specification/latest) — protocol-version and capability compatibility context.
