"""Project-scoped file storage built on the existing root-bound artifact policy."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .artifacts import ArtifactRecord, ArtifactStore


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def project_slug(project_name: str) -> str:
    """Return a stable, filesystem-safe project folder name."""
    value = _SLUG_RE.sub("-", project_name.strip().lower()).strip("-")
    if not value:
        raise ValueError("project name must contain at least one alphanumeric character")
    return value[:80]


class ProjectFilesStore:
    """Keep generated files and source records isolated by project."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def project_root(self, project_name: str) -> Path:
        folder = self.root / project_slug(project_name)
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def store(self, project_name: str, source: str | Path, *, relative_name: str | None = None, artifact_id: str | None = None) -> ArtifactRecord:
        source_path = Path(source).expanduser().resolve()
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        target_name = Path(relative_name or source_path.name)
        if target_name.is_absolute() or ".." in target_name.parts:
            raise ValueError("relative_name must remain inside the project folder")
        target = self.project_root(project_name) / target_name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source_path.read_bytes())
        return ArtifactStore(self.project_root(project_name)).register(target, artifact_id=artifact_id)

    def register_existing(self, project_name: str, relative_path: str) -> ArtifactRecord:
        store = ArtifactStore(self.project_root(project_name))
        return store.register(self.project_root(project_name) / relative_path)

    def list_project(self, project_name: str) -> list[ArtifactRecord]:
        return ArtifactStore(self.project_root(project_name)).list()

    def preview(self, project_name: str, relative_path: str, *, max_bytes: int = 12_000) -> dict[str, Any]:
        return ArtifactStore(self.project_root(project_name)).preview(relative_path, max_bytes=max_bytes)

    def project_manifest(self, project_name: str) -> dict[str, Any]:
        records = self.list_project(project_name)
        return {
            "project": project_name,
            "project_slug": project_slug(project_name),
            "root": self.project_root(project_name).as_posix(),
            "files": [record.to_dict() for record in records],
        }
