"""Bounded, provenance-aware source citations for runs and artifacts."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any
from urllib.parse import urlparse


@dataclass(frozen=True)
class SourceCitation:
    citation_id: str
    source_url: str
    title: str
    quote: str
    extracted_value: str
    verification_status: str
    source_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {"citation_id": self.citation_id, "source_url": self.source_url, "title": self.title, "quote": self.quote, "extracted_value": self.extracted_value, "verification_status": self.verification_status, "source_hash": self.source_hash}


def create_source_citation(citation_id: str, source_url: str, *, title: str = "", quote: str = "", extracted_value: str = "", verification_status: str = "unverified") -> SourceCitation:
    parsed = urlparse(source_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("source_url must be an absolute http(s) URL")
    if verification_status not in {"unverified", "verified", "disputed", "blocked"}:
        raise ValueError("invalid citation verification status")
    if not citation_id.strip():
        raise ValueError("citation_id is required")
    bounded_quote = quote[:4000]
    bounded_value = extracted_value[:2000]
    digest = sha256(f"{source_url}|{title[:500]}|{bounded_quote}".encode("utf-8")).hexdigest()
    return SourceCitation(citation_id.strip(), source_url[:2000], title[:500], bounded_quote, bounded_value, verification_status, digest)


def attach_citations(target: dict[str, Any], citations: list[SourceCitation], *, target_type: str) -> dict[str, Any]:
    if target_type not in {"run", "artifact"}:
        raise ValueError("target_type must be run or artifact")
    result = dict(target)
    result["source_citations"] = [citation.to_dict() for citation in citations[:100]]
    result["citation_target_type"] = target_type
    return result
