"""Local preview runtime for static project revisions."""

from __future__ import annotations

import socket
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PreviewProcess:
    preview_id: str
    revision_id: str
    root: str
    host: str
    port: int
    status: str
    pid: int | None = None


class PreviewRuntime:
    def __init__(self) -> None:
        self._processes: dict[str, subprocess.Popen[str]] = {}
        self._records: dict[str, PreviewProcess] = {}

    @staticmethod
    def _free_port(host: str = "127.0.0.1") -> int:
        with socket.socket() as sock:
            sock.bind((host, 0))
            return int(sock.getsockname()[1])

    def start(self, preview_id: str, revision_id: str, root: str | Path, *, host: str = "127.0.0.1", port: int | None = None) -> PreviewProcess:
        root_path = Path(root).expanduser().resolve()
        if not root_path.is_dir():
            raise FileNotFoundError(str(root_path))
        if preview_id in self._processes and self._processes[preview_id].poll() is None:
            return self._records[preview_id]
        selected_port = port or self._free_port(host)
        process = subprocess.Popen((sys.executable, "-m", "http.server", str(selected_port), "--bind", host), cwd=root_path, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, start_new_session=True)
        record = PreviewProcess(preview_id, revision_id, str(root_path), host, selected_port, "running", process.pid)
        self._processes[preview_id] = process
        self._records[preview_id] = record
        return record

    def status(self, preview_id: str) -> PreviewProcess:
        if preview_id not in self._records:
            raise KeyError(f"preview not found: {preview_id}")
        process = self._processes[preview_id]
        record = self._records[preview_id]
        if process.poll() is not None and record.status == "running":
            record = PreviewProcess(record.preview_id, record.revision_id, record.root, record.host, record.port, "stopped", record.pid)
            self._records[preview_id] = record
        return record

    def stop(self, preview_id: str) -> PreviewProcess:
        record = self.status(preview_id)
        process = self._processes[preview_id]
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        stopped = PreviewProcess(record.preview_id, record.revision_id, record.root, record.host, record.port, "stopped", record.pid)
        self._records[preview_id] = stopped
        return stopped

    def stop_all(self) -> None:
        for preview_id in tuple(self._processes):
            self.stop(preview_id)
