# Manus Connector Catalog and Execution Status

The repository already contains the first safe connector-catalog and execution slice. The catalog file contains **372** catalogued entries with explicit enabled-state metadata; catalog presence does not imply operational support or a stored credential.

| Capability | Existing evidence | Boundary |
|---|---|---|
| Catalog inventory | `orville_core/connector_catalog.json`, `GET /api/v1/connectors` | Catalog-only entries remain unavailable until configured and supported. |
| Safe bridge | `orville_core/connector_bridge.py`, `docs/PYTHON_MCP_BRIDGE.md` | Loopback/bounded transport, no arbitrary command execution, bounded request/response sizes, and redacted audit records. |
| Health | `GET /api/v1/connectors/health` | Read-only health check; unconfigured bridges report `not_configured`. |
| Approved invocation | `POST /api/v1/connectors/{connector_uid}/invoke` and connector-adapter invocation routes | Sensitive operations require explicit approval; credentials remain server-side. |
| Operation discovery | OpenAPI discovery and operation-list routes | Discovered operations are treated as untrusted metadata and remain approval-gated. |
| Regression evidence | `tests/test_connector_bridge.py`, `tests/test_connector_adapters.py` | Local fake bridge and redaction tests cover catalog count, health, blocked invocation, approved invocation, and transfer safety. |

The connector work is therefore in a **verified local implementation** state rather than an empty starting point. The remaining platform-owned item is Windows-native executable rebuild and connector smoke validation; PowerShell, Wine, and PyInstaller are unavailable in the Linux sandbox.
