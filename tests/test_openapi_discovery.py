from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

from orville_core.openapi_discovery import discover_openapi


def test_openapi_discovery_normalizes_operations_and_risk():
    document = {
        "openapi": "3.0.0",
        "paths": {
            "/records": {"get": {"operationId": "records.list", "summary": "List records", "parameters": [{"name": "cursor", "in": "query"}]}},
            "/records/{record_id}": {"delete": {"operationId": "records.delete", "summary": "Delete record"}},
            "https://evil.invalid": {"get": {"operationId": "evil"}},
        },
    }

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = json.dumps(document).encode()
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
        operations = discover_openapi(f"http://127.0.0.1:{server.server_port}", {}, allowed_hosts={"127.0.0.1"}, allow_private=True)
        assert [item.operation_id for item in operations] == ["records.list", "records.delete"]
        assert operations[0].pagination["parameter_names"] == ["cursor"]
        assert operations[1].risk_class == "critical"
    finally:
        server.shutdown()
