# Connector Operations

## Inventory policy

Connector configuration is inspected before declaring a connector unavailable. The status record must distinguish enabled, disabled, degraded, unavailable, and unknown states without exposing credentials.

## Current observations

The configured connector named `fly dev` is enabled in the current session configuration, but capability discovery failed because its OAuth transport attempted to connect to `http://127.0.0.1:8080/sse` and the local endpoint refused the connection. It is therefore operationally unavailable in this environment until its endpoint or authentication configuration is repaired.

No connector named `python-fast-api` was present in the inspected session configuration. Orville should not create or enable a replacement without an explicit requirement and user approval. The documented replacement path is to run a local FastAPI MCP server at a user-supplied endpoint, register it through the connector configuration flow, then discover tools and execute one harmless capability call.

## Repair procedure

1. Inspect connector configuration and endpoint before editing.
2. Confirm the official server URL or local process command.
3. Validate authentication and transport without printing secret values.
4. Re-run tool discovery.
5. Execute one harmless read-only capability call.
6. Record the result as enabled, degraded, or unavailable.

Do not retry a failing connector indefinitely, invent an endpoint, copy credentials from another connector, or mutate connector configuration without an explicit project requirement and user approval.

## Capability audit contract

`orville_core.connector_capability.ConnectorCapabilityAudit` accepts only a concrete project connector list and selects one enabled `read` operation per connector. Dry-run verification is the default and performs no external call. Invocation mode is available for an explicitly approved, credentialed test environment and rejects connectors that declare no harmless read-only operation. The current `PROJECT.md` does not declare any connector IDs as required, so no external capability call was made during the local validation run; fixture invocation and sensitive-operation rejection are covered by `tests/test_connector_capability.py`.
