# Settings Workspace

## Scope

The settings workspace groups provider and model defaults, privacy routing, storage paths, resource limits, schedules, notifications, and user preferences. Settings are explicit, typed, reviewable, and separated from credentials. A saved setting does not by itself authorize external execution, publication, deployment, or destructive changes.

## Sections and boundaries

| Section | Captured settings | Boundary |
|---|---|---|
| Providers and models | Provider, default model, protected credential reference, capabilities, timeout. | Credential values remain in approved protected storage; UI shows only a safe reference. |
| Privacy routing | Local-only, user-approved cloud, or restricted-per-run class. | Routing class is policy metadata, not permission to transmit. |
| Storage paths | Artifact and temporary directories, retention class. | Paths require containment and writable-location validation. |
| Resource limits | Concurrency, task timeout, memory, file size, and execution quotas. | Limits are bounded and fail closed when invalid. |
| Schedules | Manual, approved interval, or approved cron mode. | Enabling schedules and external effects require explicit authorization. |
| Notifications | Failure, approval, checkpoint, or disabled events. | Notification targets and message contents must not disclose secrets. |
| User preferences | Theme, motion, density, language, and local display options. | Preferences contain no credentials, prompts, provider responses, or personal secrets. |

## Save and reset behavior

The UI validates values before saving, preserves safe user input on validation failure, and reports a safe operation result. Local preview persistence may store only the allowlisted non-secret settings. Reset removes the local settings draft and does not delete artifacts, credentials, projects, or external resources. Backend persistence must apply schema validation, authorization, optimistic concurrency, audit metadata, and path containment before committing.

Settings that affect external routing, schedules, publication, deployment, account access, or durable deletion require a separate confirmation or approval record. A setting change must state its effective scope, current value, proposed value, owner, timestamp, and restart or migration impact where applicable.

## Secret and privacy requirements

The settings UI never renders API keys, bearer tokens, cookies, private keys, or raw authorization headers. Credential fields use protected controls or references and are excluded from local drafts, logs, analytics, screenshots, changelogs, and state files. Endpoint URLs may be visible configuration metadata but are validated against network policy by the local service. Errors show safe operation IDs and remediation, not provider response bodies or secret-bearing URLs.

## Acceptance criteria

The workspace is accepted when every listed section is reachable, fields have labels and bounded types, invalid values are rejected, local drafts persist only allowlisted settings, reset is non-destructive, protected values never appear in the interface or local payload, theme and motion preferences align with the design system, and consequential changes remain approval-gated. Tests use synthetic values only and make no external requests.
