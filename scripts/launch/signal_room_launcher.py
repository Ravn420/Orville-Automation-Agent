from __future__ import annotations

import ctypes
import json
import os
import secrets
import shutil
import socket
import sys
import threading
import time
import webbrowser
if os.name == "nt":
    import msvcrt
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote


def application_root() -> Path:
    bundled = getattr(sys, "_MEIPASS", None)
    return Path(bundled) if bundled else Path(__file__).resolve().parent


def legacy_data_root() -> Path | None:
    if not getattr(sys, "frozen", False) or os.getenv("ORVILLE_PORTABLE", "0").lower() in {"1", "true", "yes"}:
        return None
    return Path(sys.executable).resolve().parent / "data"


def data_root() -> Path:
    """Use writable user data while retaining an explicit portable mode."""
    if os.getenv("ORVILLE_PORTABLE", "0").lower() in {"1", "true", "yes"}:
        root = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    else:
        local_app_data = os.getenv("LOCALAPPDATA")
        root = Path(local_app_data) / "Orville" if local_app_data else (Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent)
    path = root / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def migrate_legacy_data(destination: Path) -> None:
    """Copy legacy dist\\data state once; never delete the original release data."""
    source = legacy_data_root()
    if source is None or source == destination or not source.exists() or (destination / ".migration-v1-complete").exists():
        return
    for name in (".env.production", "orville-models.json", "hub-downloads.json", "browser-sessions.json", "agent-profile.json", "connector-connections.json", "runtime-state.json"):
        source_path, destination_path = source / name, destination / name
        if source_path.is_file() and not destination_path.exists():
            shutil.copy2(source_path, destination_path)
    for name in (".orville", "artifacts", "models"):
        source_path, destination_path = source / name, destination / name
        if source_path.is_dir():
            shutil.copytree(source_path, destination_path, dirs_exist_ok=True)
    (destination / ".migration-v1-complete").write_text(f"Migrated from {source}\\n", encoding="utf-8")


class SingleInstanceLock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._owned = False
        self._handle = None

    def acquire(self) -> bool:
        if os.name == "nt":
            try:
                handle = self.path.open("a+", encoding="ascii")
                handle.seek(0)
                if handle.tell() == 0:
                    handle.write("0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                handle.seek(0)
                handle.truncate()
                handle.write(str(os.getpid()))
                handle.flush()
                self._handle = handle
                self._owned = True
                return True
            except (OSError, IOError):
                if self._handle is not None:
                    self._handle.close()
                    self._handle = None
                return False
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w", encoding="ascii", newline="\n") as handle:
                handle.write(str(os.getpid()))
            self._owned = True
            return True
        except FileExistsError:
            return False

    def release(self) -> None:
        if not self._owned:
            return
        if os.name == "nt" and self._handle is not None:
            try:
                self._handle.seek(0)
                msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)
            except (OSError, IOError):
                pass
            self._handle.close()
            self._handle = None
        try:
            self.path.unlink()
        except OSError:
            pass
        self._owned = False


def choose_port(preferred: int, host: str = "127.0.0.1") -> int:
    """Use the configured port when free, otherwise select an ephemeral port."""
    if 1 <= preferred <= 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind((host, preferred))
                return preferred
            except OSError:
                pass
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind((host, 0))
        return int(probe.getsockname()[1])


def load_or_create_token(root: Path) -> str:
    env_path = root / ".env.production"
    values: dict[str, str] = {}
    if env_path.exists():
        for raw in env_path.read_text(encoding="utf-8-sig").splitlines():
            line = raw.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    token = os.getenv("ORVILLE_API_TOKEN") or values.get("ORVILLE_API_TOKEN") or secrets.token_urlsafe(32)
    values["ORVILLE_API_TOKEN"] = token
    values.setdefault("ORVILLE_API_HOST", "127.0.0.1")
    values.setdefault("ORVILLE_API_PORT", "8787")
    values.setdefault("ORVILLE_FRONTEND_PORT", "3000")
    values.setdefault("ORVILLE_NATIVE_WINDOW", "1")
    values.setdefault("ORVILLE_ALLOWED_ORIGINS", "http://127.0.0.1:3000,http://localhost:3000")
    env_path.write_text("\n".join(f"{key}={value}" for key, value in values.items()) + "\n", encoding="utf-8")
    for key, value in values.items():
        os.environ.setdefault(key, value)
    return token


class SignalRoomHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory: str, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)

    def send_error(self, code, message=None, explain=None):  # noqa: N802
        if code == 404:
            self.path = "/index.html"
            return super().do_GET()
        return super().send_error(code, message, explain)

    def log_message(self, format: str, *args) -> None:
        return


def start_frontend(root: Path, port: int) -> ThreadingHTTPServer:
    handler = lambda *args, **kwargs: SignalRoomHandler(*args, directory=str(root), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=server.serve_forever, name="signal-room-static", daemon=True).start()
    return server


def focus_existing_window() -> None:
    if os.name != "nt":
        return
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, "Orville — Signal Room")
        if hwnd:
            user32.ShowWindow(hwnd, 9)
            user32.SetForegroundWindow(hwnd)
    except Exception:
        pass


def write_runtime_state(root: Path, **values: object) -> None:
    path = root / "runtime-state.json"
    try:
        previous = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, json.JSONDecodeError):
        previous = {}
    previous.update(values)
    path.write_text(json.dumps(previous, indent=2), encoding="utf-8")


def open_signal_room(url: str) -> None:
    """Use WebView2/pywebview when available; fall back to the system browser."""
    if os.getenv("ORVILLE_NATIVE_WINDOW", "1").lower() not in {"0", "false", "no"}:
        try:
            import webview
            webview.create_window("Orville — Signal Room", url, width=1440, height=920, min_size=(1024, 680), text_select=True)
            webview.start(gui="edgechromium")
            return
        except Exception as exc:  # pragma: no cover - depends on host WebView2
            write_runtime_state(data_root(), native_window_error=f"{type(exc).__name__}: {exc}")
    webbrowser.open(url, new=2)


def main() -> int:
    root = data_root()
    migrate_legacy_data(root)
    instance_lock = SingleInstanceLock(root / "orville.lock")
    if not instance_lock.acquire():
        focus_existing_window()
        write_runtime_state(root, status="already_running", checked_at=time.time())
        return 0
    static_server = None
    api_server = None
    try:
        token = load_or_create_token(root)
        host = os.getenv("ORVILLE_API_HOST", "127.0.0.1")
        api_port = choose_port(int(os.getenv("ORVILLE_API_PORT", "8787")), host)
        frontend_port = choose_port(int(os.getenv("ORVILLE_FRONTEND_PORT", "3000")))
        os.environ["ORVILLE_API_PORT"] = str(api_port)
        os.environ["ORVILLE_FRONTEND_PORT"] = str(frontend_port)
        os.environ["ORVILLE_API_TOKEN"] = token
        os.environ["ORVILLE_ALLOWED_ORIGINS"] = f"http://127.0.0.1:{frontend_port},http://localhost:{frontend_port}"
        browser_runtime = root / "ms-playwright"
        if browser_runtime.exists():
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browser_runtime)
        os.chdir(root)

        from orville_core.api import create_app
        from orville_core.migrations import migrate_data_root
        import uvicorn

        migrate_data_root(root)
        app = create_app(checkpoint_dir=root / ".orville" / "checkpoints", database_path=root / ".orville" / "orville.db", storage="sqlite", api_token=token, allowed_origins=[f"http://127.0.0.1:{frontend_port}", f"http://localhost:{frontend_port}"])
        api_config = uvicorn.Config(app, host=host, port=api_port, log_config=None, access_log=False)
        api_server = uvicorn.Server(api_config)
        threading.Thread(target=api_server.run, name="orville-api", daemon=True).start()

        frontend = application_root() / "webui"
        if not (frontend / "index.html").is_file():
            raise FileNotFoundError(f"bundled Signal Room frontend is missing: {frontend}")
        static_server = start_frontend(frontend, frontend_port)
        runtime_url = f"http://127.0.0.1:{frontend_port}/?api={quote(f'http://127.0.0.1:{api_port}', safe=':/')}&token={quote(token)}"
        write_runtime_state(root, status="running", api_port=api_port, frontend_port=frontend_port, pid=os.getpid(), url=runtime_url, started_at=time.time())
        time.sleep(1.2)
        open_signal_room(runtime_url)
        while True:
            time.sleep(1)
            if api_server.should_exit:
                break
    except KeyboardInterrupt:
        return 0
    finally:
        write_runtime_state(root, status="stopped", stopped_at=time.time())
        if api_server is not None:
            api_server.should_exit = True
        if static_server is not None:
            static_server.shutdown()
        instance_lock.release()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - release diagnostics
        try:
            error_path = data_root() / "launcher-error.log"
            error_path.write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
        finally:
            raise
