"""Bounded workspace and revision primitives for Orville execution.

The implementation is intentionally provider-neutral. It provides safe local
behavior for development and exposes explicit limitations for stronger
container or VM isolation supplied by a deployment adapter.
"""

from __future__ import annotations

import difflib
import hashlib
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from time import monotonic
from typing import Iterable

from .security import FilesystemPolicy, SecurityViolation


_CONTEXT_EXCLUDED_NAMES = frozenset({".env", ".env.local", ".env.production", ".env.development", "credentials", "credentials.json", "secrets", "secrets.json"})
_CONTEXT_EXCLUDED_SUFFIXES = frozenset({".pem", ".key", ".p12", ".pfx", ".crt"})


def _is_context_excluded(path: Path) -> bool:
    name = path.name.lower()
    return name in _CONTEXT_EXCLUDED_NAMES or name.endswith(tuple(_CONTEXT_EXCLUDED_SUFFIXES)) or "credential" in name or "secret" in name


class WorkspaceError(RuntimeError):
    """Raised for invalid workspace, write, or command operations."""


@dataclass(frozen=True)
class CommandResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False


@dataclass(frozen=True)
class Revision:
    revision_id: str
    parent_revision: str | None
    content_hash: str
    changed_paths: tuple[str, ...]
    created_by: str


@dataclass
class WorkspaceSession:
    workspace_id: str
    root: Path
    base_revision: str | None = None
    allowed_commands: frozenset[str] = frozenset({"python", "python3", "pytest", "git", "npm", "pnpm", "yarn"})
    max_output_bytes: int = 1_000_000
    _revisions: dict[str, Path] = field(default_factory=dict, repr=False)
    _revision_metadata: dict[str, Revision] = field(default_factory=dict, repr=False)

    @classmethod
    def create(cls, source_root: str | Path, *, workspace_parent: str | Path | None = None, workspace_id: str = "workspace", base_revision: str | None = None) -> "WorkspaceSession":
        source = Path(source_root).expanduser().resolve()
        if not source.is_dir():
            raise WorkspaceError(f"source root is not a directory: {source}")
        parent = Path(workspace_parent or tempfile.gettempdir()).expanduser().resolve()
        parent.mkdir(parents=True, exist_ok=True)
        destination = Path(tempfile.mkdtemp(prefix=f"orville-{workspace_id}-", dir=parent))
        shutil.copytree(source, destination, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".git", ".orville", "__pycache__", "*.pyc", ".env", ".env.*", "*.pem", "*.key", "*.p12", "*.pfx", "*.crt", "credentials*", "secrets*"))
        return cls(workspace_id=workspace_id, root=destination, base_revision=base_revision)

    def policy(self) -> FilesystemPolicy:
        return FilesystemPolicy((self.root,), allow_write=True)

    def resolve(self, relative_path: str | Path, *, write: bool = False) -> Path:
        candidate = self.policy().resolve(self.root / relative_path, write=write)
        if candidate == self.root and write:
            raise SecurityViolation("workspace root cannot be overwritten")
        return candidate

    @staticmethod
    def checksum(path: Path) -> str:
        if not path.exists():
            return ""
        if not path.is_file():
            raise WorkspaceError(f"checksum target is not a file: {path}")
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    def read_file(self, relative_path: str | Path, *, max_bytes: int = 2_000_000) -> str:
        path = self.resolve(relative_path)
        if not path.is_file():
            raise FileNotFoundError(str(relative_path))
        return path.read_text(encoding="utf-8")[:max_bytes]

    def write_file(self, relative_path: str | Path, content: str, *, expected_checksum: str | None = None) -> str:
        path = self.resolve(relative_path, write=True)
        current_checksum = self.checksum(path)
        if expected_checksum is not None and expected_checksum != current_checksum:
            raise WorkspaceError(f"stale write rejected for {relative_path}: expected {expected_checksum}, found {current_checksum}")
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.orville-tmp")
        temporary.write_text(content, encoding="utf-8")
        os.replace(temporary, path)
        return self.checksum(path)

    def list_files(self) -> list[str]:
        return sorted(str(path.relative_to(self.root)).replace("\\", "/") for path in self.root.rglob("*") if path.is_file() and not _is_context_excluded(path))

    def index_files(self, *, query: str = "", max_files: int = 500, max_bytes: int = 2_000_000) -> list[dict[str, object]]:
        """Return bounded repository metadata without reading file contents."""
        normalized_query = query.strip().lower()
        rows: list[dict[str, object]] = []
        ignored = {".git", ".orville", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
        for path in self.root.rglob("*"):
            if not path.is_file() or _is_context_excluded(path) or any(part in ignored for part in path.parts):
                continue
            relative = str(path.relative_to(self.root)).replace("\\", "/")
            if normalized_query and normalized_query not in relative.lower():
                continue
            stat = path.stat()
            rows.append({"path": relative, "size": stat.st_size, "modified": stat.st_mtime, "checksum": self.checksum(path), "readable": stat.st_size <= max_bytes})
            if len(rows) >= max_files:
                break
        return sorted(rows, key=lambda item: str(item["path"]))

    def context_manifest(self, *, privacy_class: str = "local_only", approved_remote: bool = False) -> dict[str, object]:
        """Return context metadata only after privacy policy and approval checks."""
        if privacy_class not in {"local_only", "cloud_approved", "restricted"}:
            raise WorkspaceError("unsupported privacy class")
        if privacy_class != "local_only" and not approved_remote:
            raise SecurityViolation("remote workspace context requires explicit user approval")
        return {
            "privacy_class": privacy_class,
            "execution_location": "local" if privacy_class == "local_only" else "remote",
            "approved_remote": approved_remote,
            "files": self.index_files(),
        }

    def unified_diff(self, relative_path: str | Path, proposed_content: str, *, expected_checksum: str | None = None) -> dict[str, object]:
        """Generate a reviewable diff without writing the proposed content."""
        path = self.resolve(relative_path)
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        checksum = self.checksum(path)
        if expected_checksum is not None and expected_checksum != checksum:
            raise WorkspaceError(f"stale diff rejected for {relative_path}: expected {expected_checksum}, found {checksum}")
        relative = str(Path(relative_path)).replace("\\", "/")
        diff = "".join(difflib.unified_diff(current.splitlines(keepends=True), proposed_content.splitlines(keepends=True), fromfile=f"a/{relative}", tofile=f"b/{relative}"))
        return {"path": relative, "current_checksum": checksum, "changed": current != proposed_content, "diff": diff}

    def run(self, command: Iterable[str], *, timeout_seconds: float = 60.0, env: dict[str, str] | None = None) -> CommandResult:
        argv = tuple(str(item) for item in command)
        if not argv:
            raise WorkspaceError("command must not be empty")
        executable = Path(argv[0]).name.lower()
        if executable not in {item.lower() for item in self.allowed_commands}:
            raise SecurityViolation(f"command is not allowlisted: {argv[0]}")
        if timeout_seconds <= 0 or timeout_seconds > 900:
            raise WorkspaceError("timeout must be between 0 and 900 seconds")
        started = monotonic()
        safe_env = {"PATH": os.environ.get("PATH", ""), "LANG": "C.UTF-8"}
        if env:
            safe_env.update({str(key): str(value) for key, value in env.items() if key.upper() not in {"API_KEY", "TOKEN", "SECRET", "PASSWORD", "AUTHORIZATION"}})
        try:
            completed = subprocess.run(argv, cwd=self.root, env=safe_env, shell=False, capture_output=True, text=True, timeout=timeout_seconds, check=False)
            stdout, stderr = completed.stdout, completed.stderr
            timed_out = False
            returncode = completed.returncode
        except subprocess.TimeoutExpired as exc:
            stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
            timed_out = True
            returncode = -9
        duration = monotonic() - started
        return CommandResult(argv, returncode, stdout[: self.max_output_bytes], stderr[: self.max_output_bytes], duration, timed_out)

    def create_revision(self, *, created_by: str = "system", parent_revision: str | None = None) -> Revision:
        files = self.list_files()
        digest = hashlib.sha256()
        for relative in files:
            digest.update(relative.encode("utf-8"))
            digest.update(self.checksum(self.root / relative).encode("ascii"))
        revision_id = f"rev-{digest.hexdigest()[:16]}"
        snapshot_root = self.root.parent / f".{revision_id}"
        if snapshot_root.exists():
            shutil.rmtree(snapshot_root)
        shutil.copytree(self.root, snapshot_root, ignore=shutil.ignore_patterns(".git", ".orville", "__pycache__", "*.pyc"))
        revision = Revision(revision_id, parent_revision if parent_revision is not None else self.base_revision, digest.hexdigest(), tuple(files), created_by)
        self._revisions[revision_id] = snapshot_root
        self._revision_metadata[revision_id] = revision
        self.base_revision = revision_id
        return revision

    def rollback(self, revision_id: str) -> Revision:
        snapshot = self._revisions.get(revision_id)
        if snapshot is None or not snapshot.is_dir():
            raise WorkspaceError(f"revision is not available in this workspace: {revision_id}")
        for child in self.root.iterdir():
            if child.name not in {".git"}:
                shutil.rmtree(child) if child.is_dir() else child.unlink()
        shutil.copytree(snapshot, self.root, dirs_exist_ok=True)
        revision = self._revision_metadata[revision_id]
        self.base_revision = revision_id
        return revision

    def cleanup(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)
        for snapshot in self._revisions.values():
            shutil.rmtree(snapshot, ignore_errors=True)
