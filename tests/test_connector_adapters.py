from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pytest

from orville_core.connector_adapters import ConnectorAdapterRegistry, ConnectorManifest, GenericHttpAdapter, OperationSpec, priority_manifests


def test_priority_manifests_are_explicitly_supported_and_risk_classified():
    registry = ConnectorAdapterRegistry()
    for manifest in priority_manifests():
        registry.register(manifest)
    assert len(registry.list(supported_only=True)) >= 8
    assert any(item.risk_class == "critical" for item in registry.operations("google-gmail"))


def test_sensitive_operation_requires_approval():
    registry = ConnectorAdapterRegistry()
    manifest = ConnectorManifest("fixture", "Fixture", "api_key", "https://example.invalid", (OperationSpec("write", "Write", "POST", "/write", "sensitive"),), True)
    registry.register(manifest, lambda operation, arguments: None)
    with pytest.raises(PermissionError, match="explicit approval"):
        registry.invoke("fixture", "write", {}, approved=False)


def test_generic_adapter_redacts_response_and_supports_fixture_server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = json.dumps({"token": "do-not-leak", "ok": True}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        def log_message(self, *_args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    Thread(target=server.serve_forever, daemon=True).start()
    try:
        adapter = GenericHttpAdapter(f"http://127.0.0.1:{server.server_port}", {}, allowed_hosts={"127.0.0.1"}, allow_private=True)
        result = adapter(OperationSpec("read", "Read"), {})
        assert result.success is True
        assert result.data["ok"] is True
        assert result.data["token"] != "do-not-leak"
    finally:
        server.shutdown()


def test_transfer_contract_upload_enforces_root_and_mime(tmp_path):
    from orville_core.connector_adapters import ConnectorTransferRequest, FileTransferPolicy

    source = tmp_path / "payload.txt"
    source.write_text("safe", encoding="utf-8")
    policy = FileTransferPolicy(tmp_path, max_bytes=10, allowed_mime_types={"text/plain"})
    path, body, mime = policy.prepare(ConnectorTransferRequest("upload", str(source)))
    assert path == source.resolve()
    assert body == b"safe"
    assert mime == "text/plain"
    escape = tmp_path.parent / "escape.txt"
    escape.write_text("escape", encoding="utf-8")
    with pytest.raises(Exception, match="outside"):
        policy.prepare(ConnectorTransferRequest("upload", str(escape)))


def test_transfer_contract_rejects_size_and_mime_violations(tmp_path):
    from orville_core.connector_adapters import ConnectorAdapterError, ConnectorTransferRequest, FileTransferPolicy

    source = tmp_path / "payload.txt"
    source.write_bytes(b"01234567890")
    policy = FileTransferPolicy(tmp_path, max_bytes=10, allowed_mime_types={"text/plain"})
    with pytest.raises(ConnectorAdapterError, match="size"):
        policy.prepare(ConnectorTransferRequest("upload", str(source), "text/plain"))
    small = tmp_path / "payload.bin"
    small.write_bytes(b"ok")
    with pytest.raises(ConnectorAdapterError, match="MIME"):
        policy.prepare(ConnectorTransferRequest("upload", str(small), "application/octet-stream"))


def test_transfer_contract_download_uses_contained_destination_and_partial_protocol(tmp_path):
    from orville_core.connector_adapters import ConnectorTransferRequest, FileTransferPolicy

    destination = tmp_path / "nested" / "result.json"
    policy = FileTransferPolicy(tmp_path)
    path, body, mime = policy.prepare(ConnectorTransferRequest("download", str(destination)))
    assert path == destination.resolve()
    assert body is None
    assert mime is None
    assert not destination.with_name("result.json.part").exists()
    with pytest.raises(ValueError, match="direction"):
        policy.prepare(ConnectorTransferRequest("sync", str(destination)))
