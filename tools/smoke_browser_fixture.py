"""End-to-end smoke test for approval-gated browser actions against a local fixture site."""
from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import parse_qs

from orville_core.browser import BrowserSessionManager


class FixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/file.txt":
            body = b"orville approved download\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Disposition", "attachment; filename=fixture.txt")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        body = b'''<!doctype html><html><body>
        <h1>Orville browser fixture</h1>
        <form id="login" method="post"><label>Email<input name="Email" /></label><button type="submit">Submit</button></form>
        </body></html>'''
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        values = parse_qs(self.rfile.read(length).decode())
        body = f"<html><body><h1>submitted</h1><p>{values.get('Email', [''])[0]}</p></body></html>".encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args) -> None:
        return


def main() -> int:
    server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    base = f"http://127.0.0.1:{port}"
    with TemporaryDirectory() as directory:
        manager = BrowserSessionManager(Path(directory) / "sessions.json")
        session = manager.create(["127.0.0.1"])
        assert session.navigate(base, approved=False)["takeover_required"] is True
        session.navigate(base, approved=True)
        assert session.submit_form("form#login", {"Email": "smoke@example.com"}, approved=False)["takeover_required"] is True
        submitted = session.submit_form("form#login", {"Email": "smoke@example.com"}, approved=True)
        assert "submitted" in submitted["text_excerpt"]
        assert session.download(f"{base}/file.txt", approved=False)["takeover_required"] is True
        downloaded = session.download(f"{base}/file.txt", approved=True)
        path = Path(downloaded["download"]["path"])
        assert path.is_file() and path.read_text(encoding="utf-8") == "orville approved download\n"
        events = [item["event"] for item in session.audit]
        required = {"navigation.approval_required", "navigation.approved", "form_submission.approval_required", "form_submission.approved", "download.approval_required", "download.approved"}
        assert required.issubset(events), events
        print(f"BROWSER_SMOKE=PASS PORT={port} DOWNLOAD={path.name} EVENTS={len(events)}")
        session.close()
    server.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
