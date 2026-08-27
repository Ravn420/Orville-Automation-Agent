"""Detect untrusted instructions and block execution based solely on them.

External documents, pages, tool results, model outputs, and downloaded artifacts
are data by default. This module provides a small deterministic policy boundary:
content may be inspected, but it cannot authorize a tool call unless a trusted
requester explicitly endorses the exact action.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import re


class ContentOrigin(StrEnum):
    USER = "user"
    SYSTEM = "system"
    EXTERNAL = "external"
    TOOL_RESULT = "tool_result"
    MODEL_OUTPUT = "model_output"
    DOWNLOADED_ARTIFACT = "downloaded_artifact"


class UntrustedContentError(PermissionError):
    """Raised when untrusted content is treated as an execution authority."""


_INSTRUCTION_PATTERNS = (
    re.compile(r"(?i)\b(ignore|disregard|override)\b.{0,80}\b(previous|prior|system|safety|instructions?)\b"),
    re.compile(r"(?i)\b(run|execute|invoke|call)\b.{0,80}\b(command|tool|script|function)\b"),
    re.compile(r"(?i)\b(send|post|publish|delete|purchase|pay)\b.{0,80}\b(now|immediately|without|no)\b"),
)


@dataclass(frozen=True)
class ContentAssessment:
    """Bounded, secret-free assessment of content that may contain instructions."""

    origin: ContentOrigin
    instruction_like: bool
    indicators: tuple[str, ...]


def assess_content(content: object, *, origin: ContentOrigin, max_length: int = 12_000) -> ContentAssessment:
    """Classify instruction-like text without executing, fetching, or interpreting it."""
    if not isinstance(content, str):
        raise TypeError("content must be text")
    if not 1 <= max_length <= 100_000:
        raise ValueError("max_length must be between 1 and 100000")
    bounded = content[:max_length]
    indicators = tuple(str(index) for index, pattern in enumerate(_INSTRUCTION_PATTERNS, start=1) if pattern.search(bounded))
    return ContentAssessment(origin, bool(indicators), indicators)


def authorize_tool_execution(
    assessment: ContentAssessment,
    *,
    action: str,
    explicitly_endorsed: bool = False,
    requester: ContentOrigin = ContentOrigin.USER,
) -> None:
    """Allow execution only for a separately endorsed action, never external text alone."""
    if not isinstance(action, str) or not action.strip():
        raise ValueError("action is required")
    if assessment.origin not in {ContentOrigin.USER, ContentOrigin.SYSTEM}:
        raise UntrustedContentError("external content cannot authorize tool execution")
    if requester not in {ContentOrigin.USER, ContentOrigin.SYSTEM} or not explicitly_endorsed:
        raise UntrustedContentError("explicit trusted endorsement is required before tool execution")
