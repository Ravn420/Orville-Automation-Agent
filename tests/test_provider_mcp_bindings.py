from unittest.mock import patch

import pytest

from orville_core.connector_bridge import ConnectorBridge, ConnectorBridgeError
from orville_core.connector_connections import ConnectorConnectionStore, _portable_fernet
from orville_core.provider_mcp_security import InvocationSecurityContext


def test_connector_credentials_bind_to_owner_and_task(tmp_path, monkeypatch):
    from cryptography.fernet import Fernet

    monkeypatch.setenv("ORVILLE_CONNECTOR_MASTER_KEY", Fernet.generate_key().decode())
    store = ConnectorConnectionStore(tmp_path / "connections.json")
    store.connect_manual(
        uid="github",
        display_name="GitHub",
        auth_type="bearer",
        credential_header="Authorization",
        base_url="https://api.github.com",
        credential="secret-token-value",
        scopes=["repo:read"],
        owner_id="user-1",
        task_id="task-1",
    )
    _, credential = store.credential("github", owner_id="user-1", task_id="task-1", required_scopes={"repo:read"})
    assert credential == "secret-token-value"
    with pytest.raises(Exception, match="owner"):
        store.credential("github", owner_id="user-2", task_id="task-1")
    with pytest.raises(Exception, match="task"):
        store.credential("github", owner_id="user-1", task_id="task-2")
    with pytest.raises(Exception, match="scopes"):
        store.credential("github", owner_id="user-1", task_id="task-1", required_scopes={"repo:write"})


def test_bridge_security_context_blocks_wrong_provider_and_dry_run():
    bridge = ConnectorBridge("https://bridge.example.test", "bridge-token")
    dry_context = InvocationSecurityContext(provider_id="github", task_id="task-1", user_id="user-1", allowed_tools=frozenset({"issues.create"}), dry_run=True, approved=True, approval_reference="approval-1")
    with pytest.raises(ConnectorBridgeError, match="dry-run"):
        bridge.invoke("github", "issues.create", {}, security_context=dry_context)

    wrong_provider = InvocationSecurityContext(provider_id="slack", task_id="task-1", user_id="user-1", allowed_tools=frozenset({"issues.create"}), dry_run=False, approved=True, approval_reference="approval-1")
    with pytest.raises(ConnectorBridgeError, match="provider"):
        bridge.invoke("github", "issues.create", {}, security_context=wrong_provider)


def test_bridge_context_forwards_only_safe_context_metadata():
    bridge = ConnectorBridge("https://bridge.example.test", "bridge-token")
    context = InvocationSecurityContext(provider_id="github", task_id="task-1", user_id="user-1", credential_reference="cred-ref-1", scopes=frozenset({"repo:read"}), allowed_tools=frozenset({"issues.list"}), dry_run=False, approved=True, approval_reference="approval-1")
    with patch.object(ConnectorBridge, "_request", return_value={"ok": True}) as request:
        assert bridge.invoke("github", "issues.list", {"repo": "orville"}, security_context=context) == {"ok": True}
        payload = request.call_args.args[2]
        assert payload["security_context"]["credential_reference"] == "cred-ref-1"
        assert "token" not in str(payload).lower()
