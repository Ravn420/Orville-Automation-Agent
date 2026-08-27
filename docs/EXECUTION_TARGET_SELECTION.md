# Execution Target Selection

## Purpose

Orville must select an execution target from workload requirements rather than from an assumed framework or the availability of a particular machine. The four supported target classes are **sandbox execution**, **web hosting**, **attached desktop execution**, and **persistent computing**. The decision is made before implementation or deployment and records the target, reasons, rejected alternatives, data boundary, lifecycle expectation, and unresolved environment checks.

> Select the smallest execution target that satisfies the workload's persistence, interface, operating-system, resource, network, and data-residency requirements.

## Target definitions

| Target | Use when | Avoid when | Lifecycle and data boundary |
|---|---|---|---|
| `sandbox` | The task is short-lived, reproducible, non-interactive, credential-free or uses synthetic credentials, and can finish within the ephemeral environment's resource and lifetime limits. | The process must survive hibernation, receive inbound traffic, expose a fixed endpoint, preserve mutable state across sessions, or use OS-level services unavailable in the sandbox. | Disposable workspace; persist only deliberately retained artifacts, sanitized logs, and source changes. |
| `web_hosting` | Users need browser access to a web UI or API and the workload fits the managed web runtime, storage, authentication, network, and timeout limits. Use managed autoscale for request-scoped work and reserved hosting when a continuously running process is supported by the hosting limits. | The workload needs root or Docker control, unsupported runtimes/packages, fixed firewall/IP control, resources beyond the managed limit, or a deployment target explicitly chosen by the user. | Managed HTTPS service; keep secrets server-side and durable state in approved storage. Treat client code as untrusted and never expose credentials. |
| `attached_desktop` | The workload needs the user's Windows GUI, local files, existing hardware, interactive review, data-sensitive local processing, or a native desktop integration. | The machine cannot remain online, the task must be available independently of the user's machine, or the workload requires unattended server availability. | User-controlled machine and explicitly mounted directory; operate only within the bound repository/data boundary and preserve user approval for sensitive actions. |
| `persistent_computing` | The workload needs an always-on worker, scheduled/background execution, Docker, root or OS-level packages, fixed network identity, a reusable environment, heavy compute, or resources beyond managed hosting limits. | A managed web target satisfies the requirements, the work is a short-lived local task, or persistence is only assumed because a server would be convenient. | Persistent host with explicit service supervision, backups, bounded resources, secret manager, health checks, restart policy, and shutdown/recovery procedures. |

Persistence alone does not automatically require a persistent computer: evaluate managed web hosting's reserved process option first when the workload is a web service and fits its limits. Conversely, a desktop machine is not a persistent server merely because it is powerful; it must remain online and be suitable for the required availability.

## Decision procedure

Apply the following sequence to every task or deployment request:

1. **Identify the workload.** Record whether it is one-shot, recurring, event-triggered, webhook-driven, or a persistent service using `docs/WORKLOAD_CLASSIFICATION.md`.
2. **Check interface requirements.** Select `web_hosting` when browser/API access is the primary interface and the managed runtime satisfies the workload. Select `attached_desktop` when a native Windows GUI or local interactive review is required.
3. **Check lifecycle requirements.** Select `sandbox` only when the run can finish within the current ephemeral session. For recurring, webhook, or always-on work, evaluate managed web hosting first, then `persistent_computing` if managed hosting cannot satisfy the requirement.
4. **Check environment requirements.** Select `persistent_computing` for Docker, root, custom system packages, fixed firewall/IP, non-supported runtimes, reusable cross-session state, or resource requirements beyond managed hosting. Do not select it solely because it is already available.
5. **Check data and trust boundaries.** Keep sensitive local data on `attached_desktop` or an approved persistent host when it must not leave the controlled environment. Keep provider credentials server-side or in an approved protected store; never place them in the GUI, client bundle, repository, screenshots, or logs.
6. **Check execution safety.** Require bounded resource limits, approval gates, idempotency, recovery, health checks, and sanitized observability appropriate to the workload. A target decision never authorizes an external side effect.
7. **Record the decision.** Store the selected target, requirement evidence, rejected alternatives, runtime owner, data location, rollback plan, and validation commands with the task or release evidence.

## Decision matrix

| Requirement signal | Preferred target | Required evidence |
|---|---|---|
| Short-lived deterministic test or artifact generation | `sandbox` | Bounded runtime, no required inbound traffic, retained output path |
| Browser-accessible site or API within managed limits | `web_hosting` | Runtime fit, server-side secret plan, storage and access-control plan |
| Native Windows GUI, local files, or interactive user approval | `attached_desktop` | Bound directory, Windows dependencies, online-session expectation |
| Recurring or webhook-driven service that fits managed web hosting | `web_hosting` | Trigger, timeout, concurrency, durable-state, and retry fit |
| Recurring/background worker requiring Docker, fixed IP, root, or unsupported runtime | `persistent_computing` | Host ownership, secret manager, backup, monitoring, restart, and shutdown plan |
| Large or long-running computation beyond managed limits | `persistent_computing` | Resource budget, queueing, checkpoint, cancellation, and recovery plan |
| Sensitive data that must remain on a local machine | `attached_desktop` | Data-residency boundary, local storage path, offline/degraded behavior |

## Target-specific operating contracts

### Sandbox execution

Use a fresh workspace, deterministic inputs, bounded time and disk, and synthetic credentials or local endpoints only. Do not promise background execution, fixed network reachability, durable mutable state, or recovery after hibernation. Move only sanitized, deliberately retained evidence into `artifacts/` or `logs/`.

### Web hosting

Use managed hosting for browser/API delivery when its compute, timeout, storage, and runtime constraints satisfy the workload. Keep request handlers bounded and idempotent, use approved server-side secret handling, configure access control and TLS, and persist state outside ephemeral process memory. Webhook and recurring workflows require replay protection, durable idempotency, health checks, and a documented failure path.

### Attached desktop execution

Use the connected Windows machine for the native GUI, local model/runtime access, user-owned files, and workflows requiring interactive review. Bind the exact repository or data directory, follow its `AGENTS.md`, avoid broad filesystem access, and state that the machine must remain online for active execution. Do not turn a user's desktop into an unattended production service without an explicit deployment decision.

### Persistent computing

Use a persistent host for workers, schedulers, queues, Dockerized services, fixed network endpoints, or heavy workloads that must survive sandbox hibernation and desktop disconnects. Define service ownership, process supervision, backups, secret injection, firewall policy, health endpoints, resource ceilings, logs, restart behavior, and rollback before deployment. If a managed web target can satisfy the requirement, prefer it over self-managed infrastructure.

## Change and escalation rules

Re-evaluate the target when the workload gains a new trigger, exceeds resource or timeout limits, requires a fixed endpoint, handles a new data class, adds Docker or OS-level dependencies, or changes from interactive to unattended operation. A target mismatch is a planning blocker, not a reason to silently widen permissions or move secrets.

If no target satisfies the requirements, leave the task blocked with the missing capability, evidence needed, affected data boundary, and safe alternatives. Do not purchase infrastructure, enable connectors, publish content, or deploy a service as an implicit workaround.

## Validation checklist

- [ ] Workload class is recorded before target selection.
- [ ] Target requirements and rejected alternatives are explicit.
- [ ] Persistence, interface, operating-system, network, resource, and data-residency constraints are checked.
- [ ] Secrets and external side effects have an approved boundary.
- [ ] Resource limits, idempotency, health, recovery, and rollback controls are assigned.
- [ ] The selected target has a reproducible run/build/deploy command set.
- [ ] Validation is separated into credential-free local checks and environment-specific release checks.
- [ ] Target changes trigger a documented re-evaluation.

## Related documents

- `docs/WORKLOAD_CLASSIFICATION.md`
- `docs/GUI_STANDALONE_OPERATIONS.md`
- `docs/DELIVERY_RUNBOOK.md`
- `docs/RELEASE_GATES.md`
- `docs/GUI_ARCHITECTURE_BOUNDARIES.md`
