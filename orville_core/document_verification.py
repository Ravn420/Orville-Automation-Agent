"""Credential-free verification checks for documents and presentations."""

from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DocumentVerificationPolicy:
    """Checks and expected counts for a document or presentation artifact."""

    expected_count: int | None = None
    require_citations: bool = False
    require_links: bool = False
    require_charts: bool = False
    require_images: bool = False
    require_legibility: bool = True
    min_text_characters: int = 1

    def __post_init__(self) -> None:
        if self.expected_count is not None and self.expected_count < 1:
            raise ValueError("expected_count must be positive")
        if self.min_text_characters < 1:
            raise ValueError("min_text_characters must be positive")


@dataclass(frozen=True)
class DocumentVerificationResult:
    """Stable verification result with machine-readable findings."""

    valid: bool
    format: str
    count: int | None
    findings: tuple[str, ...] = ()
    checked: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "format": self.format, "count": self.count, "findings": list(self.findings), "checked": list(self.checked), "metadata": dict(self.metadata)}


def verify_document(path: str | Path, *, policy: DocumentVerificationPolicy | None = None) -> DocumentVerificationResult:
    """Verify a Markdown, PDF, or PPTX artifact without network access."""
    policy = policy or DocumentVerificationPolicy()
    candidate = Path(path).expanduser().resolve()
    if not candidate.is_file():
        return DocumentVerificationResult(False, candidate.suffix.lower().lstrip(".") or "unknown", None, ("file_not_found",), ())
    extension = candidate.suffix.lower()
    if extension not in {".md", ".markdown", ".pdf", ".pptx"}:
        return DocumentVerificationResult(False, extension.lstrip(".") or "unknown", None, ("format_unsupported",), ("format",))
    if extension in {".md", ".markdown"}:
        text = candidate.read_text(encoding="utf-8")
        count = text.count("\f") + 1
        findings, checked, metadata = _verify_text(text, policy)
    elif extension == ".pptx":
        count = _count_zip_parts(candidate, r"ppt/slides/slide\d+\.xml")
        text = ""
        findings = []
        checked = ["format", "slide_count"]
        metadata = {"bytes": candidate.stat().st_size}
        if policy.require_legibility:
            findings.append("text_legibility_unavailable_without_render")
            checked.append("legibility")
    else:
        count = _pdf_page_count(candidate)
        text = ""
        findings = []
        checked = ["format", "page_count"]
        if policy.require_legibility:
            findings.append("text_legibility_unavailable_without_render")
            checked.append("legibility")
        metadata = {"bytes": candidate.stat().st_size}
    if policy.expected_count is not None and count != policy.expected_count:
        findings.append("count_mismatch")
    return DocumentVerificationResult(not findings, extension.lstrip("."), count, tuple(dict.fromkeys(findings)), tuple(dict.fromkeys(checked)), metadata)


def _verify_text(text: str, policy: DocumentVerificationPolicy) -> tuple[list[str], list[str], dict[str, Any]]:
    findings: list[str] = []
    checked = ["format", "page_or_slide_count", "citations", "links", "charts", "images", "legibility"]
    links = re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)|https?://[^\s)>]+", text)
    images = re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", text)
    citations = re.findall(r"(?<!\w)\[(\d+)\](?!\w)", text)
    headings = re.findall(r"^#{1,6}\s+\S+", text, flags=re.MULTILINE)
    charts = [item for item in images if re.search(r"chart|figure|plot|graph", item[0], re.I)]
    if policy.require_citations and not citations:
        findings.append("citations_missing")
    if policy.require_links and not links:
        findings.append("links_missing")
    if policy.require_images and not images:
        findings.append("images_missing")
    if policy.require_charts and not charts:
        findings.append("charts_missing")
    if policy.require_legibility:
        if len(text.strip()) < policy.min_text_characters:
            findings.append("legibility_text_insufficient")
        if not headings:
            findings.append("legibility_headings_missing")
        if any(len(line) > 240 for line in text.splitlines()):
            findings.append("legibility_line_too_long")
        if any(not alt.strip() for alt, _ in images):
            findings.append("image_alt_text_missing")
    metadata = {"characters": len(text), "headings": len(headings), "citations": len(citations), "links": len(links), "images": len(images), "charts": len(charts)}
    return findings, checked, metadata


def _count_zip_parts(path: Path, pattern: str) -> int:
    compiled = re.compile(pattern)
    with zipfile.ZipFile(path) as archive:
        return sum(1 for name in archive.namelist() if compiled.fullmatch(name))


def _pdf_page_count(path: Path) -> int:
    data = path.read_bytes()
    matches = re.findall(rb"/Type\s*/Page(?!s)\b", data)
    return len(matches)
