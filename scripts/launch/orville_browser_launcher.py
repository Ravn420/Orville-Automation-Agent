"""Launch Orville's existing API and exact browser preview as one local GUI app."""
from __future__ import annotations

import http.client
import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

API_PORT = int(os.environ.get("ORVILLE_API_PORT", "8787"))
WEB_PORT = int(os.environ.get("ORVILLE_WEB_PORT", "4173"))


def bundle_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def find_api() -> Path:
    candidates = [bundle_root() / "Orville-API.exe", bundle_root() / "dist_backend" / "Orville-API.exe"]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Orville-API.exe is missing from this release")


def find_web() -> Path:
    candidates = [bundle_root() / "web_preview", bundle_root() / "dist" / "public"]
    for candidate in candidates:
        if (candidate / "index.html").exists():
            return candidate
    raise FileNotFoundError("web preview assets are missing from this release")


def wait_for_api(token: str) -> None:
    deadline = time.time() + 20
    request = urllib.request.Request(
        f"http://127.0.0.1:{API_PORT}/api/v1/health",
        headers={"Authorization": f"Bearer {token}"},
    )
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(request, timeout=1) as response:
                if response.status == 200:
                    return
        except (OSError, urllib.error.URLError):
            time.sleep(0.25)
    raise RuntimeError("Orville API did not become ready on the local port")


def create_project(token: str) -> str:
    body = json.dumps({
        "name": "Local Orville Workspace",
        "description": "Browser launcher workspace",
        "owner_id": "local-operator",
        "environment": "development",
    }).encode()
    request = urllib.request.Request(
        f"http://127.0.0.1:{API_PORT}/api/v1/projects",
        data=body,
        method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        payload = json.loads(response.read().decode())
    project = payload.get("project", payload)
    project_id = project.get("project_id") or project.get("id")
    if not project_id:
        raise RuntimeError("API did not return a project ID")
    return str(project_id)


def main() -> None:
    token = secrets.token_urlsafe(32)
    api_env = os.environ.copy()
    api_env.update({"ORVILLE_API_TOKEN": token, "ORVILLE_HOST": "127.0.0.1", "ORVILLE_PORT": str(API_PORT)})
    api = subprocess.Popen([str(find_api())], cwd=str(bundle_root()), env=api_env)
    server = None
    try:
        wait_for_api(token)
        project_id = create_project(token)
        web_root = find_web()
        class LocalHandler(SimpleHTTPRequestHandler):
            def do_GET(self): self._proxy_or_static("GET")
            def do_POST(self): self._proxy_or_static("POST")
            def do_DELETE(self): self._proxy_or_static("DELETE")
            def do_OPTIONS(self): self._proxy_or_static("OPTIONS")
            def _proxy_or_static(self, method: str):
                if not self.path.startswith("/api/"):
                    if method == "GET": return super().do_GET()
                    self.send_error(405, "method not allowed")
                    return
                body = self.rfile.read(int(self.headers.get("Content-Length", "0"))) if method in {"POST", "DELETE"} else None
                connection = http.client.HTTPConnection("127.0.0.1", API_PORT, timeout=30)
                headers = {"Authorization": f"Bearer {token}", "Accept": self.headers.get("Accept", "application/json"), "Content-Type": self.headers.get("Content-Type", "application/json")}
                connection.request(method, self.path, body=body, headers=headers)
                response = connection.getresponse()
                content_type = response.getheader("Content-Type", "application/json")
                self.send_response(response.status)
                self.send_header("Content-Type", content_type)
                self.send_header("Cache-Control", "no-cache")
                if content_type.startswith("text/event-stream"):
                    self.end_headers()
                    while True:
                        payload = response.read(4096)
                        if not payload: break
                        self.wfile.write(payload)
                        self.wfile.flush()
                else:
                    payload = response.read()
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                connection.close()
            def log_message(self, format, *args): return
        handler = lambda *args, directory=str(web_root), **kwargs: LocalHandler(*args, directory=directory, **kwargs)
        server = ThreadingHTTPServer(("127.0.0.1", WEB_PORT), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{WEB_PORT}/?api=http%3A%2F%2F127.0.0.1%3A{WEB_PORT}&project={project_id}&token={token}"
        print(f"Orville browser GUI: {url}", flush=True)
        print("Close this window to stop Orville.", flush=True)
        webbrowser.open(url)
        while api.poll() is None:
            time.sleep(1)
    except Exception as exc:
        print(f"Orville launcher failed: {exc}", file=sys.stderr, flush=True)
        raise
    finally:
        if server is not None:
            server.shutdown()
            server.server_close()
        if api.poll() is None:
            api.terminate()
            try:
                api.wait(timeout=5)
            except subprocess.TimeoutExpired:
                api.kill()
                api.wait()


if __name__ == "__main__":
    main()
