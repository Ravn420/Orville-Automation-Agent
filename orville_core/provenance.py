"""Secret-safe source records and citations attachable to runs and artifacts."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import urlparse


@dataclass(frozen=True)
class SourceRecord:
    """Identify a source without retaining credentials or raw sensitive payloads."""

    source_id: str
    uri: str
    title: str = ""
    retrieved_at: str = ""
    locator: str = ""

    def __post_init__(self) -> None:
        if not self.source_id.strip() or not self.uri.strip():
            raise ValueError("source_id and uri must not be blank")
        parsed = urlparse(self.uri)
        if parsed.scheme not in {"http", "https", "file"} or parsed.username or parsed.password or parsed.query:
            raise ValueError("source uri must be credential-free and query-free")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Citation:
    """Point from an output to a source record and bounded locator text."""

    citation_id: str
    source_id: str
    locator: str = ""
    note: str = ""

    def __post_init__(self) -> None:
        if not self.citation_id.strip() or not self.source_id.strip():
            raise ValueError("citation_id and source_id must not be blank")
        if len(self.locator) > 500 or len(self.note) > 1_000:
            raise ValueError("citation locator and note are bounded")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_provenance(records: list[dict[str, Any]] | None, citations: list[dict[str, Any]] | None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Validate and normalize JSON-compatible provenance lists."""
    source_records = [SourceRecord(**record).to_dict() for record in (records or [])]
    known = {record["source_id"] for record in source_records}
    normalized_citations = [Citation(**citation).to_dict() for citation in (citations or [])]
    if any(citation["source_id"] not in known for citation in normalized_citations):
        raise ValueError("citation references an unknown source_id")
    return source_records, normalized_citations


__all__ = ["Citation", "SourceRecord", "normalize_provenance"]
