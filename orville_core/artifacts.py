"""Root-bound artifact storage, preview, versioning, and retention controls."""
from __future__ import annotations

import hashlib
import json
import mimetypes
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .security import FilesystemPolicy, SecurityViolation
from .provenance import normalize_provenance


@dataclass(frozen=True)
class ArtifactRecord:
    artifact_id: str
    name: str
    relative_path: str
    media_type: str
    size: int
    sha256: str
    created_at: str
    source_records: list[dict[str, Any]] = field(default_factory=list)
    citations: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ArtifactStore:
    """Store root-contained artifacts and retain metadata without exposing raw secrets."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.policy = FilesystemPolicy((self.root,), allow_write=True)
        self._manifest_path = self.root / ".artifact-versions.json"

    def _load_manifest(self) -> dict[str, list[dict[str, Any]]]:
        if not self._manifest_path.is_file():
            return {}
        try:
            value = json.loads(self._manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return value if isinstance(value, dict) else {}

    def _save_manifest(self, manifest: dict[str, list[dict[str, Any]]]) -> None:
        temporary = self._manifest_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        temporary.replace(self._manifest_path)

    def register(self, path: str | Path, *, artifact_id: str | None = None, source_records: list[dict[str, Any]] | None = None, citations: list[dict[str, Any]] | None = None) -> ArtifactRecord:

        resolved = self.policy.resolve(path)
        if not resolved.is_file():
            raise FileNotFoundError(resolved)
        relative = resolved.relative_to(self.root).as_posix()
        if relative == self._manifest_path.name:
            raise SecurityViolation("artifact manifest is not a user artifact")
        digest = hashlib.sha256(resolved.read_bytes()).hexdigest()
        media_type = mimetypes.guess_type(resolved.name)[0] or {".md": "text/markdown", ".json": "application/json", ".py": "text/x-python", ".ts": "text/typescript", ".tsx": "text/typescript"}.get(resolved.suffix.lower(), "application/octet-stream")
        normalized_sources, normalized_citations = normalize_provenance(source_records, citations)
        record = ArtifactRecord(artifact_id or digest[:16], resolved.name, relative, media_type, resolved.stat().st_size, digest, datetime.now(UTC).isoformat(), normalized_sources, normalized_citations)

        manifest = self._load_manifest()
        versions = manifest.setdefault(relative, [])
        if not versions or versions[-1].get("sha256") != record.sha256:
            versions.append(record.to_dict())
            self._save_manifest(manifest)
        return record

    def open(self, relative_path: str):
        candidate = self.policy.resolve(self.root / relative_path)
        if not candidate.is_file() or candidate == self._manifest_path:
            raise FileNotFoundError(candidate)
        return candidate.open("rb")

    def preview(self, relative_path: str, *, max_bytes: int = 12_000) -> dict[str, Any]:
        """Return a bounded text preview; binary artifacts return metadata only."""
        if not 1 <= max_bytes <= 100_000:
            raise ValueError("max_bytes must be between 1 and 100000")
        candidate = self.policy.resolve(self.root / relative_path)
        record = self.register(candidate)
        if record.media_type.startswith("text/") or record.media_type in {"application/json", "application/xml", "application/javascript"}:
            content = candidate.read_text(encoding="utf-8", errors="replace")[:max_bytes]
            return {"artifact": record.to_dict(), "preview": content, "truncated": candidate.stat().st_size > len(content.encode("utf-8"))}
        return {"artifact": record.to_dict(), "preview": None, "truncated": False}

    def versions(self, relative_path: str) -> list[dict[str, Any]]:
        candidate = self.policy.resolve(self.root / relative_path)
        if not candidate.is_file():
            raise FileNotFoundError(candidate)
        self.register(candidate)
        return list(self._load_manifest().get(candidate.relative_to(self.root).as_posix(), []))

    def retention_plan(self, *, max_versions: int = 5) -> dict[str, Any]:
        """Return deletion candidates without deleting anything."""
        if not 1 <= max_versions <= 100:
            raise ValueError("max_versions must be between 1 and 100")
        manifest = self._load_manifest()
        candidates: list[dict[str, Any]] = []
        for relative, versions in manifest.items():
            if len(versions) > max_versions:
                candidates.append({"relative_path": relative, "remove_versions": len(versions) - max_versions, "retained_versions": max_versions})
        return {"max_versions": max_versions, "candidates": candidates, "destructive_action_required": bool(candidates), "status": "plan_only"}

    def list(self) -> list[ArtifactRecord]:
        records: list[ArtifactRecord] = []
        for path in sorted(self.root.rglob("*")):
            if path.is_file() and path != self._manifest_path:
                records.append(self.register(path))
        return records
