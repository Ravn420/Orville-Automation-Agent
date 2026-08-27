"""Local-first research, data analysis, export, and deployment adapters."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .security import NetworkPolicy, SecurityViolation


@dataclass(frozen=True)
class Source:
    source_id: str
    title: str
    locator: str
    excerpt: str = ""
    retrieved_at: str = ""


@dataclass(frozen=True)
class ResearchNote:
    claim: str
    source_ids: tuple[str, ...]
    confidence: str = "medium"


@dataclass(frozen=True)
class DataProfile:
    path: str
    row_count: int
    columns: tuple[str, ...]
    missing_counts: dict[str, int]
    duplicate_rows: int
    inferred_types: dict[str, str]


@dataclass(frozen=True)
class DeploymentHandoff:
    revision_id: str
    environment: str
    status: str
    required_credentials: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


class ResearchCatalog:
    def __init__(self) -> None:
        self.sources: dict[str, Source] = {}
        self.notes: list[ResearchNote] = []

    def add_source(self, title: str, locator: str, excerpt: str = "") -> Source:
        source_id = "source-" + hashlib.sha256(locator.encode()).hexdigest()[:16]
        source = Source(source_id, title, locator, excerpt)
        self.sources[source_id] = source
        return source

    def add_note(self, claim: str, source_ids: Iterable[str], confidence: str = "medium") -> ResearchNote:
        unknown = set(source_ids) - set(self.sources)
        if unknown:
            raise KeyError(f"unknown sources: {sorted(unknown)}")
        note = ResearchNote(claim, tuple(source_ids), confidence)
        self.notes.append(note)
        return note

    def report(self) -> dict[str, Any]:
        return {"sources": [source.__dict__ for source in self.sources.values()], "notes": [note.__dict__ for note in self.notes]}


class CsvAnalyzer:
    @staticmethod
    def profile(path: str | Path) -> DataProfile:
        file_path = Path(path).expanduser().resolve()
        if not file_path.is_file() or file_path.suffix.lower() != ".csv":
            raise ValueError("profile requires an existing CSV file")
        with file_path.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        columns = tuple(rows[0].keys()) if rows else ()
        missing = {column: sum(1 for row in rows if not row.get(column, "").strip()) for column in columns}
        signatures = [tuple(row.get(column, "") for column in columns) for row in rows]
        duplicates = len(signatures) - len(set(signatures))
        inferred: dict[str, str] = {}
        for column in columns:
            values = [row.get(column, "").strip() for row in rows if row.get(column, "").strip()]
            if values and all(value.isdigit() for value in values):
                inferred[column] = "integer"
            else:
                try:
                    for value in values:
                        float(value)
                    inferred[column] = "number" if values else "empty"
                except ValueError:
                    inferred[column] = "text"
        return DataProfile(str(file_path), len(rows), columns, missing, duplicates, inferred)


class ProjectExporter:
    @staticmethod
    def archive(project_root: str | Path, output_path: str | Path, *, include_hidden: bool = False) -> Path:
        root = Path(project_root).expanduser().resolve()
        destination = Path(output_path).expanduser().resolve()
        if not root.is_dir():
            raise FileNotFoundError(str(root))
        destination.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                relative = path.relative_to(root)
                if not include_hidden and any(part.startswith(".") for part in relative.parts):
                    continue
                if any(part in {"__pycache__", "dist", "build"} for part in relative.parts):
                    continue
                archive.write(path, relative.as_posix())
        return destination


class DeploymentAdapter:
    """Safe handoff adapter; it never deploys without an explicit provider."""

    def prepare(self, revision_id: str, environment: str, *, provider: str | None = None, required_credentials: tuple[str, ...] = ()) -> DeploymentHandoff:
        if provider is None:
            return DeploymentHandoff(revision_id, environment, "blocked", required_credentials, ("No deployment provider configured",))
        return DeploymentHandoff(revision_id, environment, "awaiting_release_approval", required_credentials, ("Provider execution requires explicit release approval",))
