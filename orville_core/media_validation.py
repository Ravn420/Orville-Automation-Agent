"""Deterministic validation contracts for media deliverables."""

from __future__ import annotations

import mimetypes
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


_FORMATS = {
    "image": {"png", "jpg", "jpeg", "webp", "gif", "avif"},
    "audio": {"mp3", "wav", "m4a", "ogg", "flac"},
    "video": {"mp4", "webm", "mov", "m4v"},
}


@dataclass(frozen=True)
class MediaValidationPolicy:
    """Acceptance limits and required metadata for one media modality."""

    modality: str
    allowed_formats: frozenset[str] = frozenset()
    min_width: int | None = None
    max_width: int | None = None
    min_height: int | None = None
    max_height: int | None = None
    min_duration_seconds: float | None = None
    max_duration_seconds: float | None = None
    require_alt_text: bool = False
    require_transcript_or_captions: bool = False
    require_license: bool = True
    require_rights_holder: bool = True
    max_bytes: int = 250 * 1024 * 1024

    def __post_init__(self) -> None:
        modality = self.modality.strip().lower()
        if modality not in _FORMATS:
            raise ValueError(f"unsupported media modality: {self.modality}")
        object.__setattr__(self, "modality", modality)
        if not self.allowed_formats:
            object.__setattr__(self, "allowed_formats", frozenset(_FORMATS[modality]))
        if self.max_bytes < 1:
            raise ValueError("max_bytes must be positive")
        for name in ("min_width", "max_width", "min_height", "max_height"):
            value = getattr(self, name)
            if value is not None and value < 1:
                raise ValueError(f"{name} must be positive")
        for name in ("min_duration_seconds", "max_duration_seconds"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must not be negative")


@dataclass(frozen=True)
class MediaValidationResult:
    """Stable validation result suitable for API, GUI, or release evidence."""

    valid: bool
    modality: str
    diagnostics: tuple[str, ...] = ()
    checked: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "modality": self.modality, "diagnostics": list(self.diagnostics), "checked": list(self.checked), "metadata": dict(self.metadata)}


def validate_media(
    path: str | Path,
    *,
    policy: MediaValidationPolicy,
    metadata: dict[str, Any] | None = None,
    accessibility: dict[str, Any] | None = None,
    usage_rights: dict[str, Any] | None = None,
) -> MediaValidationResult:
    """Validate a media file and its declared metadata without external services."""
    candidate = Path(path).expanduser().resolve()
    diagnostics: list[str] = []
    checked: list[str] = ["format", "file_size", "usage_rights"]
    supplied = dict(metadata or {})
    if not candidate.is_file():
        return MediaValidationResult(False, policy.modality, ("file_not_found",), tuple(checked), supplied)
    suffix = candidate.suffix.lower().lstrip(".")
    if suffix not in policy.allowed_formats:
        diagnostics.append("format_not_allowed")
    if candidate.stat().st_size > policy.max_bytes:
        diagnostics.append("file_size_exceeded")
    _check_dimension(supplied, "width", policy.min_width, policy.max_width, diagnostics)
    _check_dimension(supplied, "height", policy.min_height, policy.max_height, diagnostics)
    if policy.min_width is not None or policy.max_width is not None:
        checked.append("resolution_width")
    if policy.min_height is not None or policy.max_height is not None:
        checked.append("resolution_height")
    duration = supplied.get("duration_seconds")
    if policy.min_duration_seconds is not None or policy.max_duration_seconds is not None:
        checked.append("duration")
        if not isinstance(duration, (int, float)):
            diagnostics.append("duration_missing")
        elif policy.min_duration_seconds is not None and duration < policy.min_duration_seconds:
            diagnostics.append("duration_below_minimum")
        elif policy.max_duration_seconds is not None and duration > policy.max_duration_seconds:
            diagnostics.append("duration_exceeded")
    access = dict(accessibility or {})
    if policy.require_alt_text:
        checked.append("alt_text")
        if not str(access.get("alt_text", "")).strip():
            diagnostics.append("alt_text_missing")
    if policy.require_transcript_or_captions:
        checked.append("transcript_or_captions")
        if not (str(access.get("transcript", "")).strip() or str(access.get("captions", "")).strip()):
            diagnostics.append("transcript_or_captions_missing")
    rights = dict(usage_rights or {})
    if policy.require_license and not str(rights.get("license", "")).strip():
        diagnostics.append("license_missing")
    if policy.require_rights_holder and not str(rights.get("rights_holder", "")).strip():
        diagnostics.append("rights_holder_missing")
    if not str(rights.get("source", "")).strip():
        diagnostics.append("rights_source_missing")
    metadata.setdefault("media_type", mimetypes.guess_type(candidate.name)[0] or "application/octet-stream")
    metadata.setdefault("format", suffix)
    metadata.setdefault("size_bytes", candidate.stat().st_size)
    return MediaValidationResult(not diagnostics, policy.modality, tuple(dict.fromkeys(diagnostics)), tuple(dict.fromkeys(checked)), metadata)


def _check_dimension(metadata: dict[str, Any], name: str, minimum: int | None, maximum: int | None, diagnostics: list[str]) -> None:
    if minimum is None and maximum is None:
        return
    value = metadata.get(name)
    if not isinstance(value, int) or isinstance(value, bool):
        diagnostics.append(f"{name}_missing")
        return
    if minimum is not None and value < minimum:
        diagnostics.append(f"{name}_below_minimum")
    if maximum is not None and value > maximum:
        diagnostics.append(f"{name}_exceeded")
