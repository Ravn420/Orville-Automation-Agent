# GUI Architecture and Boundary Contract

## Decision summary

Orville uses a **layered native-client architecture** for the current Windows desktop GUI. Tkinter/ttk owns presentation and interaction, a thin client adapter owns request shaping and safe response projection, the authenticated API owns orchestration-facing contracts, and the existing core services own durable execution, model/runtime policy, storage, and external integrations. This preserves standalone local operation while allowing future web and mobile clients to reuse the same API and service boundaries.

> The GUI is a client of Orville capabilities, not the owner of orchestration, credentials, durable state, or external side effects.

## Layer model

```text
+-------------------------------------------------------------+
| Presentation: Tkinter/ttk windows, views, controls, focus   |
+-----------------------------|-------------------------------+
                              v
+-------------------------------------------------------------+
| Client adapter: request shaping, local validation, bounded  |
| projections, cancellation, accessible status copy          |
+-----------------------------|-------------------------------+
                              v
+-------------------------------------------------------------+
| API boundary: auth, authorization, route contracts,         |
| operation errors, idempotency, approval and state checks     |
+-----------------------------|-------------------------------+
                              v
+----------------------+----------------------+---------------+
| Orchestration        | Model services       | Storage       |
| task graph, engine,  | routing, providers,  | SQLite/state, |
| plans, approvals,    | local models,       | checkpoints,  |
| events, verification | runtime capability  | artifacts     |
+----------------------+----------------------+---------------+
                              v
+-------------------------------------------------------------+
| External integrations: cloud providers, connectors, Git,    |
| browser, deployment, identity, notifications                 |
+-------------------------------------------------------------+
```

## Ownership and prohibited coupling

| Layer | Owns | Must not own |
|---|---|---|
| Presentation | Layout, labels, keyboard/focus behavior, local view state, user actions, progressive disclosure | Task-graph mutation rules, provider credentials, durable checkpoints, direct provider calls, or authorization decisions |
| Client adapter | JSON shaping, local field validation, request cancellation, bounded rendering, accessible status messages | Durable truth, secret storage, approval authorization, or policy overrides |
| API boundary | Authentication, authorization, stable routes/envelopes, operation identifiers, approval checks, idempotency, and safe error mapping | Pixel layout, presentation-only copy beyond the API contract, or direct UI state ownership |
| Orchestration | Objective normalization, task/dependency execution, retries, approvals, cancellation, verification, and event lifecycle | Widget state, provider-specific UI assumptions, or secret display |
| Model services | Capability discovery, routing, provider health, runtime compatibility, local-model lifecycle, safety and privacy policy | GUI layout, durable project authorization, or unreviewed external actions |
| Storage | Durable projects, runs, tasks, events, checkpoints, artifacts, metadata, and audit records | User-facing decisions, credentials in unapproved form, or bypassing authorization |
| External integrations | Provider/connector/browser/Git/deployment/identity/notification calls through approved adapters | Direct GUI access, implicit credentials, silent publication, or bypassing API approval gates |

## Request and event flow

A user action starts in a presentation control. The client adapter validates only what can be checked locally, then calls an authenticated `/api/v1` route. The API authenticates and authorizes the operation, applies idempotency and approval policy, and delegates to orchestration, model services, or storage. External adapters are reached only through those service boundaries. Responses return as stable envelopes; the client projects bounded data into the view and displays operation-specific, secret-safe status copy.

Polling and event refresh are read projections. They must not infer permission from displayed data, mutate durable state without the API route, or treat provider response content as trusted instructions. Sensitive operations such as execute, cancel, approve, export, publish, connector mutation, and deployment remain explicit API actions with their existing approval gates.

## Standalone and future-client rules

The native GUI is the reference client for local Windows operation, but the boundary contract is client-neutral. Future web or mobile clients must consume the same versioned API contracts rather than importing GUI internals or core storage modules. Manus integrations remain optional adapters; no core workflow depends on them. Local model services, local storage, and the authenticated local API provide the minimum standalone path.

## Security, failure, and lifecycle boundaries

Credentials remain in protected runtime configuration or approved secret references and never cross into presentation state, URLs, logs, screenshots, or committed fixtures. Backend values are untrusted at the client boundary. Loading, empty, offline, blocked, failed, partial, and long-running states are presentation projections of authoritative service state, not replacements for it. Shutdown, restart, retries, checkpoints, and recovery are orchestration or storage responsibilities.

## Acceptance checks

The architecture is accepted when the document names all seven layers, records ownership and prohibited coupling, describes authenticated request/event flow, preserves standalone operation, and states credential, approval, failure, and future-client boundaries. Focused documentation tests and Python compilation for the test module must pass. Implementation-level dependency enforcement, multi-client contract testing, and production integration review remain follow-up gates.
