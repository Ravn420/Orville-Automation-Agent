"""Durable provenance records for generated media and their source assets."""

from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
import shutil
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from .security import FilesystemPolicy, SecretRedactor


_MAX_ASSET_BYTES = 250 * 1024 * 1024


@dataclass(frozen=True)
class MediaAsset:
    """A checksum-addressed copy or output retained by the provenance store."""

    asset_id: str
    role: str
    name: str
    relative_path: str
    media_type: str
    size: int
    sha256: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MediaTransformation:
    """One deterministic or provider-backed transformation in media history."""

    operation: str
    parameters: dict[str, Any] = field(default_factory=dict)
    output_asset_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["output_asset_ids"] = list(self.output_asset_ids)
        return value


@dataclass(frozen=True)
class MediaHistoryRecord:
    """A redacted prompt plus asset and transformation lineage."""

    history_id: str
    prompt: str
    prompt_sha256: str
    source_asset_ids: tuple[str, ...]
    generated_asset_ids: tuple[str, ...]
    transformations: tuple[MediaTransformation, ...]
    created_at: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["source_asset_ids"] = list(self.source_asset_ids)
        value["generated_asset_ids"] = list(self.generated_asset_ids)
        value["transformations"] = [item.to_dict() for item in self.transformations]
        return value


class MediaProvenanceStore:
    """Persist media lineage under a bounded, repository-owned directory.

    Source and generated files are copied into the store; the caller's original
    files are never modified. Prompt text is redacted before persistence while a
    SHA-256 digest preserves reproducibility checks without retaining secrets.
    """

    def __init__(self, root: str | Path, *, max_asset_bytes: int = _MAX_ASSET_BYTES) -> None:
        self.root = Path(root).expanduser().resolve()
        self.assets_root = self.root / "assets"
        self.history_path = self.root / "history.json"
        self.assets_root.mkdir(parents=True, exist_ok=True)
        self.policy = FilesystemPolicy((self.root,), allow_write=True)
        if max_asset_bytes < 1:
            raise ValueError("max_asset_bytes must be positive")
        self.max_asset_bytes = max_asset_bytes

    def ingest_asset(self, path: str | Path, *, role: str, asset_id: str | None = None) -> MediaAsset:
        """Copy an asset into the store and return checksum-addressed metadata."""
        source = Path(path).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(source)
        size = source.stat().st_size
        if size > self.max_asset_bytes:
            raise ValueError(f"asset exceeds maximum size of {self.max_asset_bytes} bytes")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        safe_role = self._safe_component(role, "source")
        safe_name = self._safe_component(source.name, "asset")
        target = self.assets_root / safe_role / f"{digest[:16]}-{safe_name}"
        self.policy.resolve(target, write=True)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copy2(source, target)
        media_type = mimetypes.guess_type(source.name)[0] or "application/octet-stream"
        return MediaAsset(asset_id or digest[:16], role, source.name, target.relative_to(self.root).as_posix(), media_type, size, digest, datetime.now(UTC).isoformat())

    def record(
        self,
        *,
        prompt: str,
        source_assets: Iterable[MediaAsset],
        generated_assets: Iterable[MediaAsset],
        transformations: Iterable[MediaTransformation] = (),
        metadata: dict[str, Any] | None = None,
        history_id: str | None = None,
    ) -> MediaHistoryRecord:
        """Append a redacted prompt and complete media lineage atomically."""
        source = tuple(source_assets)
        generated = tuple(generated_assets)
        safe_prompt = str(SecretRedactor.redact(prompt))
        record = MediaHistoryRecord(
            history_id or f"media-{uuid4().hex[:16]}",
            safe_prompt,
            hashlib.sha256(str(prompt).encode("utf-8")).hexdigest(),
            tuple(asset.asset_id for asset in source),
            tuple(asset.asset_id for asset in generated),
            tuple(transformations),
            datetime.now(UTC).isoformat(),
            SecretRedactor.redact(dict(metadata or {})),
        )
        records = self.list_history()
        records.append(record)
        temporary = self.history_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps([item.to_dict() for item in records], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(temporary, self.history_path)
        return record

    def list_history(self) -> list[MediaHistoryRecord]:
        """Load all preserved records, returning an empty history when absent."""
        if not self.history_path.exists():
            return []
        payload = json.loads(self.history_path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError("media history must be a JSON list")
        return [self._from_dict(item) for item in payload]

    def asset_path(self, asset: MediaAsset) -> Path:
        """Resolve a retained asset through the repository-boundary policy."""
        path = self.policy.resolve(self.root / asset.relative_path)
        if not path.is_file():
            raise FileNotFoundError(path)
        return path

    @staticmethod
    def _safe_component(value: str, fallback: str) -> str:
        component = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value)).strip("._-")
        return component[:120] or fallback

    @staticmethod
    def _from_dict(value: dict[str, Any]) -> MediaHistoryRecord:
        if not isinstance(value, dict):
            raise ValueError("media history record must be an object")
        transformations = tuple(MediaTransformation(item["operation"], dict(item.get("parameters", {})), tuple(item.get("output_asset_ids", []))) for item in value.get("transformations", []))
        return MediaHistoryRecord(value["history_id"], value["prompt"], value["prompt_sha256"], tuple(value.get("source_asset_ids", [])), tuple(value.get("generated_asset_ids", [])), transformations, value["created_at"], dict(value.get("metadata", {})))
