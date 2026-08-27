"""Bounded local map/reduce research execution with resumable item results."""
from __future__ import annotations
import json
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict, field
from datetime import UTC, datetime
from pathlib import Path
from threading import Event
from typing import Any, Callable, Iterable
from uuid import uuid4


def _now() -> str:
    return datetime.now(UTC).isoformat()

@dataclass(frozen=True)
class ResearchItem:
    item_id: str
    prompt: str
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class ResearchResult:
    item_id: str
    status: str
    output: dict[str, Any] | None = None
    sources: tuple[dict[str, Any], ...] = ()
    error: str | None = None
    attempts: int = 1
    completed_at: str | None = None

@dataclass(frozen=True)
class ResearchSummary:
    job_id: str
    total: int
    completed: int
    failed: int
    cancelled: int
    results: tuple[ResearchResult, ...]

class WideResearchRunner:
    def __init__(self, state_path: str | Path, *, max_workers: int = 5, max_attempts: int = 2) -> None:
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_workers = max(1, min(max_workers, 32))
        self.max_attempts = max(1, min(max_attempts, 5))
        self.cancel_event = Event()

    def cancel(self) -> None:
        self.cancel_event.set()

    def _load(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return {"jobs": {}}
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"research state is invalid: {exc}") from exc

    def _save(self, state: dict[str, Any]) -> None:
        temporary = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        temporary.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, self.state_path)

    def run(self, items: Iterable[ResearchItem], worker: Callable[[ResearchItem], dict[str, Any]], *, job_id: str | None = None) -> ResearchSummary:
        item_list = list(items)
        if not item_list or len(item_list) > 10_000:
            raise ValueError("research job must contain between 1 and 10000 items")
        if len({item.item_id for item in item_list}) != len(item_list):
            raise ValueError("research item ids must be unique")
        state = self._load()
        job_id = job_id or "research-" + uuid4().hex[:12]
        raw_results = state.setdefault("jobs", {}).setdefault(job_id, {}).get("results", {})
        results: dict[str, ResearchResult] = {}
        pending: list[ResearchItem] = []
        for item in item_list:
            previous = raw_results.get(item.item_id)
            if previous and previous.get("status") == "completed":
                results[item.item_id] = self._from_dict(previous)
            else:
                pending.append(item)
        def execute(item: ResearchItem) -> ResearchResult:
            last_error = ""
            for attempt in range(1, self.max_attempts + 1):
                if self.cancel_event.is_set():
                    return ResearchResult(item.item_id, "cancelled", attempts=attempt, error="cancelled")
                try:
                    output = worker(item)
                    if not isinstance(output, dict):
                        raise ValueError("research worker must return an object")
                    sources = output.pop("sources", [])
                    if not isinstance(sources, list):
                        raise ValueError("research sources must be a list")
                    return ResearchResult(item.item_id, "completed", output, tuple(item for item in sources if isinstance(item, dict)), attempts=attempt, completed_at=_now())
                except Exception as exc:  # isolated item failure
                    last_error = str(exc)[:500]
            return ResearchResult(item.item_id, "failed", error=last_error, attempts=self.max_attempts, completed_at=_now())
        with ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="orville-research") as pool:
            futures = {pool.submit(execute, item): item.item_id for item in pending}
            for future in as_completed(futures):
                result = future.result()
                results[result.item_id] = result
                state["jobs"][job_id] = {"job_id": job_id, "updated_at": _now(), "results": {key: asdict(value) for key, value in results.items()}}
                self._save(state)
        ordered = tuple(results[item.item_id] for item in item_list)
        summary = ResearchSummary(job_id, len(ordered), sum(item.status == "completed" for item in ordered), sum(item.status == "failed" for item in ordered), sum(item.status == "cancelled" for item in ordered), ordered)
        state["jobs"][job_id] = {"job_id": job_id, "updated_at": _now(), "summary": asdict(summary), "results": {key: asdict(value) for key, value in results.items()}}
        self._save(state)
        return summary

    @staticmethod
    def _from_dict(data: dict[str, Any]) -> ResearchResult:
        return ResearchResult(data["item_id"], data["status"], data.get("output"), tuple(data.get("sources", [])), data.get("error"), int(data.get("attempts", 1)), data.get("completed_at"))
