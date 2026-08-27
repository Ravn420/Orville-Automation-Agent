from __future__ import annotations

import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Iterator


class _DeterministicHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _write(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._write(200, {"status": "ok", "service": "deterministic-fixture"})
            return
        if self.path == "/error":
            self._write(503, {"error": "synthetic-unavailable"})
            return
        self._write(404, {"error": "not-found"})

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except json.JSONDecodeError:
            self._write(400, {"error": "invalid-json"})
            return
        if self.path == "/echo":
            self._write(200, {"ok": True, "echo": payload})
            return
        self._write(404, {"error": "not-found"})

    def log_message(self, *_args) -> None:
        return


@contextmanager
def deterministic_mock_service() -> Iterator[str]:
    """Run an isolated local HTTP fixture and yield its base URL."""

    server = HTTPServer(("127.0.0.1", 0), _DeterministicHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
