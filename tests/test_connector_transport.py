import json
from pathlib import Path
from urllib.error import HTTPError

from orville_core.connector_adapters import GenericHttpAdapter, OperationSpec


def test_pagination_metadata_is_normalized(monkeypatch):
    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, limit): return json.dumps({"items": [1], "next_cursor": "abc", "has_more": True, "total": 4}).encode()
    monkeypatch.setattr("orville_core.connector_adapters._open_connector_request", lambda request, timeout: Response())
    adapter = GenericHttpAdapter("https://api.example.com", {}, allowed_hosts={"api.example.com"})
    operation = OperationSpec("list", "List", pagination={"cursor_param": "cursor", "item_path": "items"})
    result = adapter(operation, {"limit": 10})
    assert result.success is True
    assert result.data["items"] == [1]
    assert result.meta["pagination"]["next"] == "abc"
    assert result.meta["pagination"]["has_more"] is True


def test_retryable_http_error_retries_then_succeeds(monkeypatch):
    calls = {"count": 0}
    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, limit): return b'{"ok": true}'
    def fake_urlopen(request, timeout):
        calls["count"] += 1
        if calls["count"] == 1:
            raise HTTPError(request.full_url, 503, "temporary", {}, None)
        return Response()
    monkeypatch.setattr("orville_core.connector_adapters._open_connector_request", fake_urlopen)
    monkeypatch.setattr("orville_core.connector_adapters.time.sleep", lambda _: None)
    adapter = GenericHttpAdapter("https://api.example.com", {}, allowed_hosts={"api.example.com"}, max_retries=2)
    result = adapter(OperationSpec("health", "Health"), {})
    assert result.success is True
    assert result.meta["attempt"] == 2
    assert calls["count"] == 2


def test_non_retryable_error_returns_bounded_failure(monkeypatch):
    def fake_urlopen(request, timeout):
        raise HTTPError(request.full_url, 401, "unauthorized", {}, None)
    monkeypatch.setattr("orville_core.connector_adapters._open_connector_request", fake_urlopen)
    adapter = GenericHttpAdapter("https://api.example.com", {}, allowed_hosts={"api.example.com"}, max_retries=3)
    result = adapter(OperationSpec("health", "Health"), {})
    assert result.success is False
    assert result.status_code == 401
    assert result.meta["attempt"] == 1


def test_upload_is_rooted_and_transmits_bytes(monkeypatch, tmp_path):
    from orville_core.connector_adapters import FileTransferPolicy
    upload = tmp_path / "upload.txt"
    upload.write_text("payload", encoding="utf-8")
    seen = {}
    class Response:
        status = 201
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, limit): return b'{"uploaded": true}'
    def fake_urlopen(request, timeout):
        seen["body"] = request.data
        seen["content_type"] = request.headers.get("Content-type")
        return Response()
    monkeypatch.setattr("orville_core.connector_adapters._open_connector_request", fake_urlopen)
    adapter = GenericHttpAdapter("https://api.example.com", {}, allowed_hosts={"api.example.com"}, file_policy=FileTransferPolicy(tmp_path))
    operation = OperationSpec("upload", "Upload", method="POST", path="/upload", risk_class="sensitive", transfer={"direction": "upload"})
    result = adapter(operation, {"file_path": str(upload)})
    assert result.success is True
    assert seen["body"] == b"payload"
    assert seen["content_type"] == "text/plain"


def test_download_is_atomic_and_contained(monkeypatch, tmp_path):
    from orville_core.connector_adapters import FileTransferPolicy
    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, limit): return b"downloaded"
    monkeypatch.setattr("orville_core.connector_adapters._open_connector_request", lambda request, timeout: Response())
    adapter = GenericHttpAdapter("https://api.example.com", {}, allowed_hosts={"api.example.com"}, file_policy=FileTransferPolicy(tmp_path))
    destination = tmp_path / "result.bin"
    operation = OperationSpec("download", "Download", transfer={"direction": "download"})
    result = adapter(operation, {"download_path": str(destination)})
    assert result.success is True
    assert destination.read_bytes() == b"downloaded"
    assert not (tmp_path / "result.bin.part").exists()


def test_transfer_policy_rejects_escape_and_oversize(tmp_path):
    from orville_core.connector_adapters import ConnectorAdapterError, FileTransferPolicy
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("x", encoding="utf-8")
    policy = FileTransferPolicy(tmp_path, max_bytes=1)
    try:
        policy.read_upload(outside)
        assert False, "expected path containment failure"
    except ConnectorAdapterError as exc:
        assert "outside" in str(exc)
    oversized = tmp_path / "large.bin"
    oversized.write_bytes(b"xx")
    try:
        policy.read_upload(oversized)
        assert False, "expected size failure"
    except ConnectorAdapterError as exc:
        assert "size" in str(exc)


def test_provider_default_headers_are_non_secret_and_provider_specific():
    from orville_core.connector_adapters import provider_default_headers
    github = provider_default_headers("github")
    assert github["User-Agent"].startswith("Orville-")
    assert github["Accept"] == "application/vnd.github+json"
    assert github["X-GitHub-Api-Version"] == "2022-11-28"
    assert "Authorization" not in github
    assert provider_default_headers("google-gmail")["Accept"] == "application/json"
