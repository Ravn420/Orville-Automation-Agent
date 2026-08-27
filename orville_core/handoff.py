"""Safe repository handoff, conflict detection, and export contracts."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .research_data import ProjectExporter
from .workspace import WorkspaceError, WorkspaceSession


@dataclass(frozen=True)
class FileConflict:
    path: str
    base_checksum: str
    local_checksum: str
    remote_checksum: str
    resolution: str = "unresolved"


@dataclass(frozen=True)
class HandoffPlan:
    base_revision: str | None
    branch_name: str
    changed_paths: tuple[str, ...]
    conflicts: tuple[FileConflict, ...] = ()
    status: str = "ready_for_review"


@dataclass(frozen=True)
class ExportBundle:
    archive_path: str
    environment_template: str
    setup_instructions: str
    included_files: tuple[str, ...]


class RepositoryHandoff:
    def __init__(self, workspace: WorkspaceSession) -> None:
        self.workspace = workspace

    def compare_checksums(self, base: dict[str, str], local: dict[str, str], remote: dict[str, str]) -> tuple[FileConflict, ...]:
        conflicts: list[FileConflict] = []
        for path in sorted(set(base) | set(local) | set(remote)):
            base_checksum = base.get(path, "")
            local_checksum = local.get(path, "")
            remote_checksum = remote.get(path, "")
            local_changed = local_checksum != base_checksum
            remote_changed = remote_checksum != base_checksum
            if local_changed and remote_changed and local_checksum != remote_checksum:
                conflicts.append(FileConflict(path, base_checksum, local_checksum, remote_checksum))
        return tuple(conflicts)

    def prepare(self, branch_name: str, *, base_revision: str | None = None, base_checksums: dict[str, str] | None = None, remote_checksums: dict[str, str] | None = None) -> HandoffPlan:
        local = {path: self.workspace.checksum(self.workspace.root / path) for path in self.workspace.list_files()}
        conflicts = self.compare_checksums(base_checksums or {}, local, remote_checksums or {})
        return HandoffPlan(base_revision or self.workspace.base_revision, branch_name, tuple(local), conflicts, "blocked_by_conflict" if conflicts else "ready_for_review")

    def git_status(self) -> dict[str, Any]:
        try:
            result = subprocess.run(("git", "status", "--short", "--branch"), cwd=self.workspace.root, capture_output=True, text=True, timeout=15, check=False)
        except (OSError, subprocess.SubprocessError) as exc:
            return {"available": False, "status": "unavailable", "message": str(exc)}
        return {"available": result.returncode == 0, "status": result.stdout.strip(), "stderr": result.stderr.strip()}


class BundleExporter:
    def export(self, project_root: str | Path, output_path: str | Path, *, environment_template: str = ".env.example", setup_instructions: str = "See README.md for setup and validation commands.") -> ExportBundle:
        root = Path(project_root).expanduser().resolve()
        archive = ProjectExporter.archive(root, output_path)
        included = tuple(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file() and not any(part.startswith(".") for part in path.relative_to(root).parts))
        return ExportBundle(str(archive), environment_template, setup_instructions, included)
