# Least-Privilege Permissions

## Scope

Orville applies a task-scoped, default-deny permission policy to connectors, repositories, files, and remote systems. A grant is an allowlist, not a discovery mechanism: an empty grant denies access, and a caller must request only the resources and actions required for one workflow step.

## Boundary matrix

| Resource | Grant boundary | Default | Write or side-effect rule |
|---|---|---|---|
| Connector | Connector ID mapped to an explicit set of scopes | No connector is available | Missing connector or scope fails closed; connector mutation still requires its separate approval gate. |
| Repository | Explicit repository IDs | No repository is available | Reads and writes are separate; repository writes are denied unless the task grant enables them. |
| File | Explicit path roots resolved through `FilesystemPolicy` | No path root is available | Traversal and outside-root paths fail; writes require a separate file-write grant. |
| Remote system | Explicit normalized host set plus action set | No host or action is available | Both host and action must be allowlisted; private-network access remains governed by `NetworkPolicy`. |

The implementation is `orville_core.security.LeastPrivilegePolicy`. Its `check_connector`, `check_repository`, `resolve_file`, and `check_remote` methods are intended to run immediately before the protected operation. Policies should be created per task or run and must not be replaced with a broad administrator grant for convenience.

## Separation of concerns

Least privilege limits what a task may request; it does not authorize a sensitive action by itself. Payment, publishing, deletion, account changes, credential use, connector mutation, deployment, and other high-impact actions require their existing explicit approval and policy checks. A request is permitted only when both the least-privilege grant and the relevant approval boundary pass.

Repository and file permissions are distinct. A task may be allowed to read a repository identifier while receiving no filesystem root, or may receive a temporary workspace root without access to another repository. Remote host allowlisting does not grant arbitrary HTTP methods or operations; the action name must also be allowlisted.

## Safe configuration examples

```python
from pathlib import Path
from orville_core.security import LeastPrivilegePolicy

policy = LeastPrivilegePolicy(
    connector_scopes={"issue-tracker": frozenset({"issues:read"})},
    repository_ids=frozenset({"orville-local"}),
    file_roots=(Path("/workspace/task-17"),),
    remote_hosts=frozenset({"api.example.test"}),
    remote_actions=frozenset({"health"}),
)
```

This example does not contain credentials and grants no writes. Use a separate, narrower policy for a step that needs a controlled write, then retain the approval reference and validation evidence without recording credential values.

## Verification requirements

Focused tests must prove default denial, scope minimization, repository read/write separation, path containment, remote host and action allowlisting, host normalization, and secret-free diagnostics. Live connector, repository, file, and remote-system execution remains environment-specific and must use approved credentials, targets, and side-effect approvals.
