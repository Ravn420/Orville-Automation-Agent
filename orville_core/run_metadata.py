"""Structured, privacy-aware per-run execution metadata."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Mapping

from .observability import JsonlTraceRecorder


@dataclass(frozen=True)
class RunMetadata:
    run_id: str
    task_id: str
    provider: str = ""
    model: str = ""
    model_version: str = ""
    prompt_hash: str = ""
    tool_calls: int = 0
    agent_handoffs: int = 0
    retries: int = 0
    approvals: int = 0
    artifacts: tuple[str, ...] = ()
    latency_ms: float = 0.0
    token_usage: Mapping[str, int] = field(default_factory=dict)
    finish_reason: str = ""
    cache_hit: bool = False
    cost_metadata: Mapping[str, Any] = field(default_factory=dict)
    failure_class: str = ""

    def __post_init__(self) -> None:
        if not self.run_id or not self.task_id:
            raise ValueError("run_id and task_id are required")
        for name in ("tool_calls", "agent_handoffs", "retries", "approvals"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must not be negative")
        if self.latency_ms < 0:
            raise ValueError("latency_ms must not be negative")
        if any(not item or "\x00" in item for item in self.artifacts):
            raise ValueError("artifacts must contain non-empty safe identifiers")
        if any(not isinstance(value, int) or value < 0 for value in self.token_usage.values()):
            raise ValueError("token_usage values must be non-negative integers")

    @staticmethod
    def hash_prompt(prompt: str) -> str:
        if not isinstance(prompt, str):
            raise TypeError("prompt must be a string")
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    def to_attributes(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "task_id": self.task_id,
            "provider": self.provider,
            "model": self.model,
            "model_version": self.model_version,
            "prompt_hash": self.prompt_hash,
            "tool_calls": self.tool_calls,
            "agent_handoffs": self.agent_handoffs,
            "retries": self.retries,
            "approvals": self.approvals,
            "artifacts": list(self.artifacts),
            "latency_ms": self.latency_ms,
            "usage_counts": dict(self.token_usage),
            "finish_reason": self.finish_reason,
            "cache_hit": self.cache_hit,
            "cost_metadata": dict(self.cost_metadata),
            "failure_class": self.failure_class,
        }

    def record(self, recorder: JsonlTraceRecorder) -> None:
        recorder.record(self.run_id, "run.metadata", self.to_attributes())
