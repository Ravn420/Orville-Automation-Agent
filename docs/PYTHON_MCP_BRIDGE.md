# Python MCP Bridge

## Summary

`orville_core.mcp_server` exposes a local JSON-RPC MCP endpoint on `127.0.0.1:42069`. It forwards authenticated read and approval-gated mutation tools to Orville’s REST API, which defaults to `http://127.0.0.1:8787`.

The bridge is an adapter, not a second orchestration engine. The REST API remains the system of record for project state, authentication, persistence, and business behavior.

## Architecture

```text
MCP connector
    |
    | JSON-RPC HTTP POST /
    v
Python MCP bridge :42069
    |
    | Authorization: Bearer ${ORVILLE_API_TOKEN}
    v
Orville REST API :8787
    |
    v
SQLite/checkpoint/project stores
```

## Exposed tools

The bridge exposes read-only tools by default and supports four mutation tools behind two independent controls: `ORVILLE_MCP_MUTATIONS_ENABLED=1` must be set when the bridge starts, and every mutation call must include `approved: true`. Both controls are required; a missing control produces an MCP error result and no REST request is made.

| MCP tool | REST operation | Access |
|---|---|---|
| `orville_health` | `GET /api/v1/health` | Read-only |
| `orville_state` | `GET /api/v1/state` | Read-only |
| `orville_capabilities` | `GET /api/v1/capabilities` | Read-only |
| `orville_list_projects` | `GET /api/v1/projects` | Read-only |
| `orville_get_project` | `GET /api/v1/projects/{project_id}` | Read-only |
| `orville_list_tasks` | `GET /api/v1/projects/{project_id}/tasks` | Read-only |
| `orville_project_memory` | `GET /api/v1/projects/{project_id}/memory` | Read-only |
| `orville_project_instructions` | `GET /api/v1/projects/{project_id}/instructions` | Read-only |
| `orville_list_connectors` | `GET /api/v1/connectors` | Read-only and redacted by REST API |
| `orville_personal_agent` | `GET /api/v1/personal-agent` | Read-only |
| `orville_create_project` | `POST /api/v1/projects` | Approval-gated mutation |
| `orville_create_task` | `POST /api/v1/projects/{project_id}/tasks` | Approval-gated mutation |
| `orville_save_project_memory` | `POST /api/v1/projects/{project_id}/memory` | Approval-gated mutation |
| `orville_update_personal_agent` | `POST /api/v1/personal-agent` | Approval-gated mutation |

The supported mutation tools are `orville_create_project`, `orville_create_task`, `orville_save_project_memory`, and `orville_update_personal_agent`. Connector invocation, terminal commands, schedules, secrets, destructive operations, and arbitrary REST paths remain unavailable through this bridge. Each exposed mutation maps to an explicit allowlisted REST route and payload.

## Configuration

Set the same REST bearer token used by the API process. Do not place a real token in `.env.example`, source code, logs, MCP connector metadata, or public frontend configuration.

```text
ORVILLE_API_TOKEN=<local-secret>
ORVILLE_REST_URL=http://127.0.0.1:8787
ORVILLE_MCP_HOST=127.0.0.1
ORVILLE_MCP_PORT=42069
ORVILLE_MCP_MUTATIONS_ENABLED=0
```

The REST API itself remains configured through `ORVILLE_API_HOST=127.0.0.1` and `ORVILLE_API_PORT=8787`.

## Local startup

From the repository root, start the REST API first:

```bash
export ORVILLE_API_TOKEN='use-a-local-secret'
export ORVILLE_API_HOST=127.0.0.1
export ORVILLE_API_PORT=8787
python -m orville_core.api
```

In a second terminal, start the MCP bridge:

```bash
export ORVILLE_API_TOKEN='use-the-same-local-secret'
export ORVILLE_REST_URL=http://127.0.0.1:8787
export ORVILLE_MCP_HOST=127.0.0.1
export ORVILLE_MCP_PORT=42069
python -m orville_core.mcp_server
```

The package entrypoint is also available after installation:

```bash
orville-python-mcp
```

The MCP connector should use the exact URL `http://127.0.0.1:42069` with no trailing whitespace. Leave `ORVILLE_MCP_MUTATIONS_ENABLED=0` unless mutation tools are intentionally required; enabling it is not a substitute for per-call `approved: true`.

## Validation

Check the bridge health endpoint:

```bash
curl http://127.0.0.1:42069/health
```

The MCP client can then perform initialization and tool discovery. In the Orville environment, use:

```bash
manus-mcp-cli tool list --server python-fast-api
```

The REST API must already be listening and must accept the configured bearer token before a tool call can return data. If REST is unavailable, MCP initialization and tool listing still work, but tool calls return an MCP error result describing REST unavailability.

## Security boundaries

The bridge binds to loopback by default, forwards only the server-side REST bearer token, applies bounded request and response sizes, URL-encodes resource identifiers, allowlists REST routes and payload fields, and requires both bridge-level mutation enablement and per-call approval for writes. Do not bind it to a non-loopback interface without adding a separate MCP authentication layer, TLS termination, rate limiting, and an explicit deployment review.
