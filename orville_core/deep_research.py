"""Bounded, source-backed Deep Research workflow for Orville."""
from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Callable, Iterable
from urllib.parse import urlparse


@dataclass(frozen=True)
class ResearchSource:
    url: str
    title: str
    snippet: str = ""
    retrieved_at: str = ""
    verification: str = "discovered"
    content: str = ""

    @property
    def source_id(self) -> str:
        return hashlib.sha256(self.url.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["source_id"] = self.source_id
        value.pop("content", None)
        return value


@dataclass(frozen=True)
class ResearchConfig:
    max_sources: int = 5
    max_excerpt_chars: int = 4000
    timeout_seconds: int = 30
    include_private_files: bool = False
    provider_name: str = "unconfigured"
    report_format: str = "markdown"

    def __post_init__(self) -> None:
        if not 1 <= self.max_sources <= 20:
            raise ValueError("max_sources must be between 1 and 20")
        if not 200 <= self.max_excerpt_chars <= 20_000:
            raise ValueError("max_excerpt_chars must be between 200 and 20000")
        if not 1 <= self.timeout_seconds <= 300:
            raise ValueError("timeout_seconds must be between 1 and 300")
        if self.report_format not in {"markdown", "json"}:
            raise ValueError("unsupported report format")


@dataclass
class ResearchRun:
    query: str
    config: ResearchConfig
    status: str = "created"
    stage: str = "plan"
    sources: list[ResearchSource] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    report: str = ""
    errors: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "status": self.status,
            "stage": self.stage,
            "sources": [source.to_dict() for source in self.sources],
            "findings": list(self.findings),
            "report": self.report,
            "errors": list(self.errors),
            "created_at": self.created_at,
            "privacy": {
                "provider": self.config.provider_name,
                "include_private_files": self.config.include_private_files,
                "query_leaves_local_boundary": self.config.provider_name not in {"local", "unconfigured"},
            },
        }


SearchFn = Callable[[str, int], Iterable[dict[str, str] | ResearchSource]]
FetchFn = Callable[[str, int], str]


class DeepResearchEngine:
    """Run research through explicit bounded stages using injected providers."""

    def __init__(self, search: SearchFn | None = None, fetch: FetchFn | None = None) -> None:
        self.search = search
        self.fetch = fetch

    def run(self, query: str, *, config: ResearchConfig | None = None) -> ResearchRun:
        query = " ".join(query.split()).strip()
        if not query:
            raise ValueError("research query is required")
        run = ResearchRun(query=query, config=config or ResearchConfig())
        if self.search is None:
            run.status = "blocked"
            run.stage = "search"
            run.errors.append("No search provider is configured; configure a provider before running Deep Research.")
            return run

        run.status, run.stage = "running", "search"
        try:
            candidates = list(self.search(query, run.config.max_sources))[: run.config.max_sources]
            for candidate in candidates:
                source = candidate if isinstance(candidate, ResearchSource) else ResearchSource(
                    url=str(candidate.get("url", "")), title=str(candidate.get("title", "")), snippet=str(candidate.get("snippet", ""))
                )
                if not _valid_http_url(source.url):
                    continue
                run.sources.append(source)
        except Exception as exc:  # provider boundary must become a visible run state
            run.status, run.stage = "failed", "search"
            run.errors.append(f"Search provider failed: {type(exc).__name__}")
            return run

        if not run.sources:
            run.status, run.stage = "blocked", "search"
            run.errors.append("Search returned no verified HTTP(S) sources.")
            return run

        if self.fetch is not None:
            run.stage = "fetch"
            fetched: list[ResearchSource] = []
            for source in run.sources:
                try:
                    content = self.fetch(source.url, run.config.max_excerpt_chars)[: run.config.max_excerpt_chars]
                    fetched.append(ResearchSource(source.url, source.title, source.snippet, datetime.now(UTC).isoformat(), "fetched", content))
                except Exception:
                    fetched.append(ResearchSource(source.url, source.title, source.snippet, datetime.now(UTC).isoformat(), "fetch_failed"))
            run.sources = fetched

        run.stage = "synthesize"
        run.findings = [source.content or source.snippet for source in run.sources if source.content or source.snippet]
        run.stage = "verify"
        run.findings = [finding.strip()[: run.config.max_excerpt_chars] for finding in run.findings if finding.strip()]
        run.stage = "report"
        run.report = self._report(run)
        run.status = "completed" if run.findings else "partial"
        return run

    @staticmethod
    def _report(run: ResearchRun) -> str:
        lines = [f"# Deep Research: {run.query}", "", "## Findings"]
        for index, finding in enumerate(run.findings, 1):
            lines.append(f"{index}. {finding}")
        lines.extend(["", "## Sources"])
        for index, source in enumerate(run.sources, 1):
            lines.append(f"[{index}] [{source.title or source.url}]({source.url}) — {source.verification}")
        return "\n".join(lines)


def _valid_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc) and not re.search(r"[\r\n]", value)
