from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        return

    def _write(self, payload):
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/health":
            self._write({"ok": True, "status": "ready"})
            return
        self.send_error(404)

    def do_POST(self):
        if self.path != "/invoke":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")
        self._write({"ok": True, "data": {"connector_uid": payload.get("connector_uid"), "operation": payload.get("operation"), "arguments": payload.get("arguments")}})


ThreadingHTTPServer(("127.0.0.1", 9999), Handler).serve_forever()
