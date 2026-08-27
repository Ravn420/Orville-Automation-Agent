# Supported Deployment Targets and Environment Variables

## Scope

This document defines the deployment targets currently supported by Orville’s standalone runtime. It distinguishes targets with local evidence from deployment environments that remain provider- or infrastructure-owned. It does not provision infrastructure, store credentials, or authorize production promotion.

## Supported target matrix

| Target | Runtime shape | Data location | Required configuration | Readiness status |
|---|---|---|---|---|
| Local Python process | Python 3.10+ process running the API or deterministic CLI | Configured local/portable data directory; default database path is `.orville/orville.db` | `ORVILLE_API_TOKEN`; set `ORVILLE_ALLOWED_ORIGINS` explicitly when a client is used | Supported standalone target |
| Windows installed release | Packaged `Orville-Signal-Room.exe` with local FastAPI control plane and WebView2 when available; system-browser fallback is supported | `%LOCALAPPDATA%\\Orville\\data` | `ORVILLE_API_TOKEN` for authenticated API access; launcher selects free loopback ports and records them in `runtime-state.json` | Supported packaged target; release evidence retained |
| Windows portable release | Same packaged control plane beside the portable executable | Portable directory beside the executable | `ORVILLE_PORTABLE=1` and `ORVILLE_API_TOKEN`; keep mutable state beside the portable release | Supported portable target; release evidence retained |
| Docker Compose small-team topology | Private `api` service behind Caddy `proxy`, with persistent `orville-data` and `caddy-data` volumes | Named Compose volumes | `ORVILLE_API_TOKEN`; production `ORVILLE_ALLOWED_ORIGINS`, `ORVILLE_DB_PATH`, and any deployment-specific host/proxy values must be explicit | Supported documented topology; live promotion remains deployment-owned |
| Disposable container check | One local container for an API smoke check | Ephemeral container filesystem unless a volume is supplied | `ORVILLE_API_TOKEN` through `--env-file` or an approved secret injection method | Supported validation target, not a production topology |

Orville does **not** claim a managed cloud, Kubernetes, serverless, or public multi-replica deployment as a supported target in this repository. A production deployment may use an equivalent approved platform only after its operator supplies platform-specific networking, secret management, monitoring, backup, rollback, and non-root execution controls.

## Runtime environment variables

`ORVILLE_API_TOKEN` is the only mandatory process variable for an authenticated API process. It must be a non-placeholder secret and must never be committed, printed, placed in frontend assets, or written to unredacted logs.

| Variable | Required | Default | Accepted values or purpose |
|---|---:|---|---|
| `ORVILLE_API_TOKEN` | Yes for API | None | High-entropy non-placeholder bearer token. |
| `ORVILLE_API_HOST` | No | `127.0.0.1` | `127.0.0.1`, `localhost`, or `0.0.0.0`; bind only to an intended interface. |
| `ORVILLE_API_PORT` | No | `8787` | Integer from 1 through 65535. Packaged Windows launchers may select a free local port and persist it in runtime state. |
| `ORVILLE_STORAGE` | No | `sqlite` | `sqlite` or `json`. |
| `ORVILLE_DB_PATH` | No | `.orville/orville.db` | A path in the configured runtime-data boundary. |
| `ORVILLE_ALLOWED_ORIGINS` | No | `http://localhost:3000` | Comma-separated non-empty client-origin allowlist; set explicitly for deployed clients. |
| `ORVILLE_REQUESTS_PER_MINUTE` | No | `120` | Positive integer rate limit. |

## Optional integration variables

The following variables enable optional local bridges or provider integrations. They are not required for the standalone local target.

| Variable family | Purpose | Secret boundary |
|---|---|---|
| `ORVILLE_REST_URL`, `ORVILLE_MCP_HOST`, `ORVILLE_MCP_PORT`, `ORVILLE_MCP_MUTATIONS_ENABLED` | Local REST-to-MCP bridge configuration | Mutations remain disabled by default and require per-call approval. |
| `OLLAMA_BASE_URL`, `OLLAMA_MODEL` | User-managed local Ollama endpoint and model selection | Keep endpoints local unless explicitly approved; no API key is inferred. |
| `GEMINI_API_KEY` | Optional user-supplied Gemini provider credential | Store only in the process environment or approved protected secret store. |
| `ORVILLE_STABLE_HORDE_API_KEY`, `ORVILLE_STABLE_HORDE_MODEL`, `ORVILLE_STABLE_HORDE_BASE_URL` | Optional Stable Horde integration | Never commit the API key; live provider use is separately authorized. |
| `ORVILLE_BLACKBOX_RELAY_URL`, `ORVILLE_BLACKBOX_RELAY_ALLOWED_HOSTS`, `ORVILLE_BLACKBOX_RELAY_MODEL`, `ORVILLE_BLACKBOX_RELAY_ENABLED`, `ORVILLE_BLACKBOX_RELAY_PLAN`, `ORVILLE_RELAY_SUBJECT` | Optional managed Blackbox relay client settings | The Blackbox credential belongs only on the relay server and is not a client variable. |
| `ORVILLE_PORTABLE` | Selects portable packaged-release data behavior | Use `1` only for a portable release; it is not a substitute for the API token. |

## Configuration rules by target

Local development may rely on safe defaults for host, port, storage, database path, origins, and request rate, but it still requires a non-placeholder API token when the API is started. Installed Windows releases should use the launcher-managed data directory and loopback binding. Portable releases must set `ORVILLE_PORTABLE=1` and preserve the adjacent mutable-data directory. Compose deployments must keep the API private behind the proxy, use persistent volumes, inject secrets through the deployment secret manager, and avoid scaling SQLite-backed API processes beyond one replica.

Before any production promotion, operators must validate the effective non-secret configuration, create and verify a database backup, run compilation and regression checks, verify authenticated health and smoke workflows, and retain sanitized release evidence. A failed check stops promotion; it does not authorize automatic rollback or destructive recovery.

## Standalone validation

```bash
python -m pytest tests/test_deployment_targets.py -q
python -m py_compile tests/test_deployment_targets.py
```

The tests verify that the target matrix names only supported repository targets, that every runtime variable is represented in `.env.example`, that the API token is documented as required and secret-safe, and that unsupported production claims are explicitly excluded.
