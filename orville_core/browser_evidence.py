"""Safe browser evidence projection for runs, artifacts, and lifecycle audits."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


_SENSITIVE = ("password", "token", "secret", "cookie", "authorization", "bearer", "prompt")


def _safe_detail(value: object) -> str:
    text = str(value)[:500]
    lowered = text.lower()
    if any(marker in lowered for marker in _SENSITIVE):
        return "[redacted browser detail]"
    return text


@dataclass(frozen=True)
class BrowserRunEvidence:
    run_id: str
    session_id: str
    session_status: str
    current_url: str | None
    artifact_ids: tuple[str, ...]
    events: tuple[Mapping[str, str], ...]

    def to_dict(self) -> dict[str, Any]:
        return {"run_id": self.run_id, "session_id": self.session_id, "session_status": self.session_status, "current_url": self.current_url, "artifact_ids": list(self.artifact_ids), "events": [dict(event) for event in self.events]}


def build_browser_evidence(run_id: str, session: Mapping[str, Any], *, artifact_ids: list[str] | tuple[str, ...] = ()) -> BrowserRunEvidence:
    if not run_id.strip():
        raise ValueError("run_id is required")
    events: list[Mapping[str, str]] = []
    for raw in list(session.get("audit") or [])[-100:]:
        if isinstance(raw, Mapping):
            events.append({"at": _safe_detail(raw.get("at", "")), "event": _safe_detail(raw.get("event", "")), "detail": _safe_detail(raw.get("detail", ""))})
    return BrowserRunEvidence(run_id.strip(), str(session.get("session_id", "")), str(session.get("status", "unknown")), session.get("current_url") if isinstance(session.get("current_url"), str) else None, tuple(str(item) for item in artifact_ids[:100]), tuple(events))
