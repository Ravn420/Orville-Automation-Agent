# Smallest Complete Vertical Slice

The smallest complete validation slice is a user request entering the authenticated Orville API, being normalized into a task, passing provider capability and privacy-policy checks, receiving a redacted pre-execution summary, and either being admitted to the managed relay or routed to a configured local fallback. The slice must preserve task state, return actionable errors, and expose no credentials.

## Slice boundaries

| Stage | Contract | Validation |
|---|---|---|
| Intake | Authenticated objective and task creation | API intake tests |
| Policy | Privacy class, workspace approval, capability admission | routing and cloud-relay tests |
| Execution context | Provider, model, endpoint family, privacy, location, capabilities | pre-execution summary tests |
| Primary route | Managed Blackbox relay with server-only credential boundary | relay adapter tests |
| Recovery route | Local provider fallback for unavailable/expired/rate-limited relay | fallback policy tests |
| State | Checkpoint and redacted output preservation | API/workspace/security tests |

Do not expand the first slice with live provider calls, OAuth/device authentication, payments, browser takeover, or production hosting. Those are separate risks and remain independently gated. The slice is complete only when its focused tests, compilation, static checks, and platform checks pass.
