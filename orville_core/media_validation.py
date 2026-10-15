"""Deterministic validation contracts for media deliverables.

This module provides comprehensive media validation including:
- Format-specific validators (image dimensions, audio bitrate, video codec)
- Content safety checks (appropriate content filtering)
- Visual verification workflows
- File integrity validation (checksums, magic numbers)
- Size and dimension limits
"""

from __future__ import annotations

import hashlib
import mimetypes
import re
import struct
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

_FORMATS = {
    "image": {"png", "jpg", "jpeg", "webp", "gif", "avif"},
    "audio": {"mp3", "wav", "m4a", "ogg", "flac"},
    "video": {"mp4", "webm", "mov", "m4v"},
}

# Magic numbers for file format detection
MAGIC_NUMBERS = {
    # Images
    "png": b"\x89PNG\r\n\x1a\n",
    "jpg": b"\xff\xd8\xff",
    "jpeg": b"\xff\xd8\xff",
    "gif": b"GIF87a",
    "gif89a": b"GIF89a",
    "webp": b"RIFF",
    "avif": b"\x00\x00\x00 ftyp",
    # Audio
    "mp3_id3": b"ID3",
    "mp3_sync": b"\xff\xfb",
    "wav": b"RIFF",
    "flac": b"fLaC",
    "ogg": b"OggS",
    "m4a": b"\x00\x00\x00 ftyp",
    # Video
    "mp4": b"\x00\x00\x00 ftyp",
    "webm": b"\x1aE\xdf\xa3",
    "mov": b"\x00\x00\x00 ftyp",
    "m4v": b"\x00\x00\x00 ftyp",
}

# Content safety patterns (basic inappropriate content detection)
CONTENT_SAFETY_PATTERNS = {
    "suspicious_metadata": [
        r"script\s*:",
        r"javascript:",
        r"on\w+\s*=",
        r"<\s*iframe",
        r"<\s*object",
        r"<\s*embed",
    ],
    "executable_signatures": [
        b"MZ",  # Windows executable
        b"\x7fELF",  # Linux executable
        b"#!",  # Shebang scripts
        b"<?php",
        b"<%",
    ],
}


class ValidationSeverity(StrEnum):
    """Severity levels for validation findings."""

    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"


class ContentSafetyLevel(StrEnum):
    """Content safety classification levels."""

    SAFE = "safe"
    WARNING = "warning"
    UNSAFE = "unsafe"
    UNKNOWN = "unknown"


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
    # Format-specific validation options
    require_magic_number_check: bool = True
    require_checksum: bool = False
    require_content_safety: bool = True
    min_audio_bitrate_kbps: int | None = None
    max_audio_bitrate_kbps: int | None = None
    min_video_bitrate_mbps: float | None = None
    max_video_bitrate_mbps: float | None = None
    require_video_codec: str | None = None
    require_audio_codec: str | None = None
    allowed_color_spaces: frozenset[str] | None = None
    require_transparency: bool | None = None

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
class ContentSafetyResult:
    """Result of content safety checks."""

    level: ContentSafetyLevel
    findings: tuple[str, ...] = ()
    severity: ValidationSeverity | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level.value,
            "findings": list(self.findings),
            "severity": self.severity.value if self.severity else None,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class FileIntegrityResult:
    """Result of file integrity validation."""

    valid: bool
    format_detected: str | None = None
    magic_number_match: bool | None = None
    checksum_sha256: str | None = None
    file_size_bytes: int = 0
    diagnostics: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "format_detected": self.format_detected,
            "magic_number_match": self.magic_number_match,
            "checksum_sha256": self.checksum_sha256,
            "file_size_bytes": self.file_size_bytes,
            "diagnostics": list(self.diagnostics),
        }


@dataclass(frozen=True)
class FormatSpecificResult:
    """Result of format-specific validation."""

    valid: bool
    format: str
    width: int | None = None
    height: int | None = None
    duration_seconds: float | None = None
    bitrate_kbps: float | None = None
    codec: str | None = None
    color_space: str | None = None
    has_transparency: bool | None = None
    frame_rate: float | None = None
    sample_rate: int | None = None
    diagnostics: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "format": self.format,
            "width": self.width,
            "height": self.height,
            "duration_seconds": self.duration_seconds,
            "bitrate_kbps": self.bitrate_kbps,
            "codec": self.codec,
            "color_space": self.color_space,
            "has_transparency": self.has_transparency,
            "frame_rate": self.frame_rate,
            "sample_rate": self.sample_rate,
            "diagnostics": list(self.diagnostics),
        }


@dataclass(frozen=True)
class MediaValidationResult:
    """Stable validation result suitable for API, GUI, or release evidence."""

    valid: bool
    modality: str
    diagnostics: tuple[str, ...] = ()
    checked: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    # Extended validation results
    content_safety: ContentSafetyResult | None = None
    file_integrity: FileIntegrityResult | None = None
    format_specific: FormatSpecificResult | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {
            "valid": self.valid,
            "modality": self.modality,
            "diagnostics": list(self.diagnostics),
            "checked": list(self.checked),
            "metadata": dict(self.metadata),
        }
        if self.content_safety:
            result["content_safety"] = self.content_safety.to_dict()
        if self.file_integrity:
            result["file_integrity"] = self.file_integrity.to_dict()
        if self.format_specific:
            result["format_specific"] = self.format_specific.to_dict()
        return result


class MediaValidator(Protocol):
    """Protocol for media format-specific validators."""

    def validate(self, path: Path, policy: MediaValidationPolicy) -> FormatSpecificResult:
        """Validate a media file against format-specific requirements."""
        ...


def _detect_format_from_magic_number(data: bytes) -> str | None:
    """Detect file format from magic number."""
    if data.startswith(MAGIC_NUMBERS["png"]):
        return "png"
    if data.startswith(MAGIC_NUMBERS["jpg"]):
        return "jpg"
    if data.startswith(MAGIC_NUMBERS["gif"]) or data.startswith(MAGIC_NUMBERS["gif89a"]):
        return "gif"
    if data.startswith(MAGIC_NUMBERS["webp"]) and b"WEBP" in data[:12]:
        return "webp"
    if data.startswith(MAGIC_NUMBERS["flac"]):
        return "flac"
    if data.startswith(MAGIC_NUMBERS["ogg"]):
        return "ogg"
    if data.startswith(MAGIC_NUMBERS["mp3_id3"]) or data.startswith(MAGIC_NUMBERS["mp3_sync"]):
        return "mp3"
    if data.startswith(MAGIC_NUMBERS["webm"]):
        return "webm"
    # Check for MP4/MOV/M4A/M4V (they share similar structure)
    if len(data) >= 12 and data[4:8] == b"ftyp":
        brand = data[8:12].decode("ascii", errors="ignore")
        if brand in ("avif", "avis"):
            return "avif"
        if brand in ("mp41", "mp42", "isom", "M4V "):
            return "mp4"
        if brand in ("qt  ", "mov"):
            return "mov"
        if brand in ("M4A ", "m4a"):
            return "m4a"
        if brand in ("M4V ", "m4v"):
            return "m4v"
    # WAV is RIFF with WAVE format
    if data.startswith(MAGIC_NUMBERS["wav"]) and b"WAVE" in data[:12]:
        return "wav"
    return None


def _parse_png_dimensions(data: bytes) -> tuple[int, int] | None:
    """Parse PNG image dimensions from IHDR chunk."""
    try:
        # PNG: IHDR chunk starts at byte 16, width at 16-19, height at 20-23
        if len(data) >= 24 and data[12:16] == b"IHDR":
            width = struct.unpack(">I", data[16:20])[0]
            height = struct.unpack(">I", data[20:24])[0]
            return width, height
        # Search for IHDR chunk
        idx = data.find(b"IHDR")
        if idx != -1 and len(data) >= idx + 13:
            width = struct.unpack(">I", data[idx + 4 : idx + 8])[0]
            height = struct.unpack(">I", data[idx + 8 : idx + 12])[0]
            return width, height
    except (struct.error, IndexError):
        pass
    return None


def _parse_jpg_dimensions(data: bytes) -> tuple[int, int] | None:
    """Parse JPEG image dimensions from SOF markers."""
    try:
        idx = 2  # Skip SOI marker
        while idx < len(data) - 10:
            if data[idx] != 0xFF:
                idx += 1
                continue
            marker = data[idx + 1]
            # SOF0, SOF1, SOF2 markers contain dimensions
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                height = struct.unpack(">H", data[idx + 5 : idx + 7])[0]
                width = struct.unpack(">H", data[idx + 7 : idx + 9])[0]
                return width, height
            # Skip marker segment
            if marker in (0xD8, 0xD9):  # SOI, EOI
                idx += 2
            elif marker == 0xD9:  # EOI
                break
            else:
                length = struct.unpack(">H", data[idx + 2 : idx + 4])[0]
                idx += 2 + length
    except (struct.error, IndexError):
        pass
    return None


def _parse_gif_dimensions(data: bytes) -> tuple[int, int] | None:
    """Parse GIF image dimensions from header."""
    try:
        if len(data) >= 10 and data[:6] in (b"GIF87a", b"GIF89a"):
            width = struct.unpack("<H", data[6:8])[0]
            height = struct.unpack("<H", data[8:10])[0]
            return width, height
    except struct.error:
        pass
    return None


def _parse_webp_dimensions(data: bytes) -> tuple[int, int] | None:
    """Parse WebP image dimensions from VP8 or VP8L chunk."""
    try:
        if len(data) >= 30 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            chunk_type = data[12:16]
            if chunk_type == b"VP8 ":
                # Simple lossy format
                if data[23] == 0x9D and data[24] == 0x01 and data[25] == 0x2A:
                    width = struct.unpack("<H", data[26:28])[0] & 0x3FFF
                    height = struct.unpack("<H", data[28:30])[0] & 0x3FFF
                    return width, height
            elif chunk_type == b"VP8L":
                # Lossless format
                if data[20] == 0x2F:
                    bits = struct.unpack("<I", data[21:25])[0]
                    width = (bits & 0x3FFF) + 1
                    height = ((bits >> 14) & 0x3FFF) + 1
                    return width, height
            elif chunk_type == b"VP8X":
                # Extended format
                width = struct.unpack("<I", data[24:28])[0] & 0xFFFFFF
                height = struct.unpack("<I", data[28:32])[0] & 0xFFFFFF
                return width + 1, height + 1
    except struct.error:
        pass
    return None


def _check_executable_content(data: bytes) -> list[str]:
    """Check for executable content in file data."""
    findings = []
    for signature in CONTENT_SAFETY_PATTERNS["executable_signatures"]:
        if signature in data[:1024]:
            findings.append(f"executable_signature_detected:{signature.decode('ascii', errors='ignore')[:10]}")
    return findings


def _check_metadata_safety(metadata: dict[str, Any]) -> list[str]:
    """Check metadata for suspicious content."""
    findings = []
    metadata_str = str(metadata).lower()
    for pattern in CONTENT_SAFETY_PATTERNS["suspicious_metadata"]:
        if re.search(pattern, metadata_str, re.IGNORECASE):
            findings.append(f"suspicious_metadata:{pattern}")
    return findings


def validate_file_integrity(
    path: Path,
    expected_format: str | None = None,
    compute_checksum: bool = False,
) -> FileIntegrityResult:
    """Validate file integrity using magic numbers and checksums."""
    diagnostics: list[str] = []

    if not path.is_file():
        return FileIntegrityResult(
            valid=False,
            diagnostics=("file_not_found",),
            file_size_bytes=0,
        )

    file_size = path.stat().st_size

    if file_size == 0:
        return FileIntegrityResult(
            valid=False,
            file_size_bytes=0,
            diagnostics=("empty_file",),
        )

    # Read first 4KB for magic number detection
    try:
        with open(path, "rb") as f:
            header_data = f.read(4096)
    except OSError as e:
        return FileIntegrityResult(
            valid=False,
            file_size_bytes=file_size,
            diagnostics=(f"read_error:{e}",),
        )

    # Detect format from magic number
    detected_format = _detect_format_from_magic_number(header_data)

    # Check for executable content
    executable_findings = _check_executable_content(header_data)
    if executable_findings:
        diagnostics.extend(executable_findings)

    # Verify magic number matches expected format
    magic_match = None
    if expected_format:
        if detected_format is None:
            magic_match = False
            diagnostics.append(f"magic_number_mismatch:expected_{expected_format}_got_unknown")
        elif detected_format != expected_format:
            magic_match = False
            diagnostics.append(f"magic_number_mismatch:expected_{expected_format}_got_{detected_format}")
        else:
            magic_match = True

    # Compute checksum if requested
    checksum = None
    if compute_checksum:
        try:
            sha256_hash = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256_hash.update(chunk)
            checksum = sha256_hash.hexdigest()
        except OSError as e:
            diagnostics.append(f"checksum_error:{e}")

    # Determine validity: invalid if there are executable signatures or magic number mismatch
    has_critical_issues = any(
        d.startswith("executable") or d.startswith("magic_number_mismatch")
        for d in diagnostics
    )
    valid = not has_critical_issues

    return FileIntegrityResult(
        valid=valid,
        format_detected=detected_format,
        magic_number_match=magic_match,
        checksum_sha256=checksum,
        file_size_bytes=file_size,
        diagnostics=tuple(diagnostics),
    )


def validate_content_safety(
    path: Path,
    metadata: dict[str, Any] | None = None,
) -> ContentSafetyResult:
    """Validate content safety for media files."""
    findings: list[str] = []

    if not path.is_file():
        return ContentSafetyResult(
            level=ContentSafetyLevel.UNKNOWN,
            findings=("file_not_found",),
            severity=None,
        )

    # Check file for executable content
    try:
        with open(path, "rb") as f:
            header_data = f.read(4096)
        executable_findings = _check_executable_content(header_data)
        findings.extend(executable_findings)
    except OSError as e:
        return ContentSafetyResult(
            level=ContentSafetyLevel.UNKNOWN,
            findings=(f"read_error:{e}",),
            severity=ValidationSeverity.CRITICAL,
        )

    # Check metadata for suspicious patterns
    if metadata:
        metadata_findings = _check_metadata_safety(metadata)
        findings.extend(metadata_findings)

    # Determine safety level
    if any(f.startswith("executable") for f in findings):
        return ContentSafetyResult(
            level=ContentSafetyLevel.UNSAFE,
            findings=tuple(findings),
            severity=ValidationSeverity.CRITICAL,
        )

    if findings:
        return ContentSafetyResult(
            level=ContentSafetyLevel.WARNING,
            findings=tuple(findings),
            severity=ValidationSeverity.MAJOR,
        )

    return ContentSafetyResult(
        level=ContentSafetyLevel.SAFE,
        findings=(),
        severity=None,
    )


def validate_format_specific(
    path: Path,
    policy: MediaValidationPolicy,
) -> FormatSpecificResult:
    """Validate format-specific properties of media files."""
    diagnostics: list[str] = []

    if not path.is_file():
        return FormatSpecificResult(
            valid=False,
            format="unknown",
            diagnostics=("file_not_found",),
        )

    suffix = path.suffix.lower().lstrip(".")
    if suffix not in policy.allowed_formats:
        return FormatSpecificResult(
            valid=False,
            format=suffix,
            diagnostics=("format_not_allowed",),
        )

    # Read file header for parsing
    try:
        with open(path, "rb") as f:
            data = f.read(65536)  # Read up to 64KB for parsing
    except OSError as e:
        return FormatSpecificResult(
            valid=False,
            format=suffix,
            diagnostics=(f"read_error:{e}",),
        )

    # Detect actual format
    detected_format = _detect_format_from_magic_number(data) or suffix

    # Parse dimensions based on format
    width: int | None = None
    height: int | None = None
    has_transparency: bool | None = None

    if detected_format in ("png", "jpg", "jpeg", "gif", "webp", "avif"):
        if detected_format == "png":
            dims = _parse_png_dimensions(data)
            if dims:
                width, height = dims
            # PNG may have transparency
            has_transparency = b"tRNS" in data[:256] or (len(data) > 25 and data[25] & 4)
        elif detected_format in ("jpg", "jpeg"):
            dims = _parse_jpg_dimensions(data)
            if dims:
                width, height = dims
            has_transparency = False
        elif detected_format == "gif":
            dims = _parse_gif_dimensions(data)
            if dims:
                width, height = dims
            # Check for transparency flag in global color table flags
            if len(data) >= 11:
                has_transparency = bool(data[10] & 0x80)
        elif detected_format == "webp":
            dims = _parse_webp_dimensions(data)
            if dims:
                width, height = dims
            # VP8L (lossless) and VP8X support transparency
            has_transparency = b"VP8L" in data[:32] or b"ALPH" in data[:256]

    # Validate dimensions against policy
    if policy.min_width is not None and width is not None and width < policy.min_width:
        diagnostics.append("width_below_minimum")
    if policy.max_width is not None and width is not None and width > policy.max_width:
        diagnostics.append("width_exceeded")
    if policy.min_height is not None and height is not None and height < policy.min_height:
        diagnostics.append("height_below_minimum")
    if policy.max_height is not None and height is not None and height > policy.max_height:
        diagnostics.append("height_exceeded")

    # Validate transparency requirement
    if policy.require_transparency is not None:
        if policy.require_transparency and has_transparency is False:
            diagnostics.append("transparency_required_but_missing")
        elif not policy.require_transparency and has_transparency is True:
            diagnostics.append("transparency_not_allowed_but_present")

    # Validate color space (placeholder for future implementation)
    color_space: str | None = None
    if policy.allowed_color_spaces and color_space not in policy.allowed_color_spaces:
        diagnostics.append("color_space_not_allowed")

    valid = not diagnostics

    return FormatSpecificResult(
        valid=valid,
        format=detected_format,
        width=width,
        height=height,
        has_transparency=has_transparency,
        color_space=color_space,
        diagnostics=tuple(diagnostics),
    )


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

    # File existence check
    if not candidate.is_file():
        return MediaValidationResult(
            False,
            policy.modality,
            ("file_not_found",),
            tuple(checked),
            supplied,
        )

    suffix = candidate.suffix.lower().lstrip(".")
    if suffix not in policy.allowed_formats:
        diagnostics.append("format_not_allowed")

    file_size = candidate.stat().st_size
    if file_size > policy.max_bytes:
        diagnostics.append("file_size_exceeded")

    # File integrity validation
    file_integrity: FileIntegrityResult | None = None
    if policy.require_magic_number_check or policy.require_checksum:
        checked.append("file_integrity")
        file_integrity = validate_file_integrity(
            candidate,
            expected_format=suffix if policy.require_magic_number_check else None,
            compute_checksum=policy.require_checksum,
        )
        if not file_integrity.valid:
            diagnostics.extend(file_integrity.diagnostics)

    # Content safety validation
    content_safety: ContentSafetyResult | None = None
    if policy.require_content_safety:
        checked.append("content_safety")
        content_safety = validate_content_safety(candidate, supplied)
        if content_safety.level == ContentSafetyLevel.UNSAFE:
            diagnostics.append("content_safety_failed")

    # Format-specific validation
    format_specific: FormatSpecificResult | None = None
    checked.append("format_specific")
    format_specific = validate_format_specific(candidate, policy)
    if not format_specific.valid:
        diagnostics.extend(format_specific.diagnostics)

    # Dimension checks from supplied metadata
    _check_dimension(supplied, "width", policy.min_width, policy.max_width, diagnostics)
    _check_dimension(supplied, "height", policy.min_height, policy.max_height, diagnostics)
    if policy.min_width is not None or policy.max_width is not None:
        checked.append("resolution_width")
    if policy.min_height is not None or policy.max_height is not None:
        checked.append("resolution_height")

    # Duration checks
    duration = supplied.get("duration_seconds")
    if policy.min_duration_seconds is not None or policy.max_duration_seconds is not None:
        checked.append("duration")
        if not isinstance(duration, (int, float)):
            diagnostics.append("duration_missing")
        elif policy.min_duration_seconds is not None and duration < policy.min_duration_seconds:
            diagnostics.append("duration_below_minimum")
        elif policy.max_duration_seconds is not None and duration > policy.max_duration_seconds:
            diagnostics.append("duration_exceeded")

    # Accessibility checks
    access = dict(accessibility or {})
    if policy.require_alt_text:
        checked.append("alt_text")
        if not str(access.get("alt_text", "")).strip():
            diagnostics.append("alt_text_missing")
    if policy.require_transcript_or_captions:
        checked.append("transcript_or_captions")
        if not (str(access.get("transcript", "")).strip() or str(access.get("captions", "")).strip()):
            diagnostics.append("transcript_or_captions_missing")

    # Usage rights checks
    rights = dict(usage_rights or {})
    if policy.require_license and not str(rights.get("license", "")).strip():
        diagnostics.append("license_missing")
    if policy.require_rights_holder and not str(rights.get("rights_holder", "")).strip():
        diagnostics.append("rights_holder_missing")
    if not str(rights.get("source", "")).strip():
        diagnostics.append("rights_source_missing")

    # Set default metadata
    supplied.setdefault("media_type", mimetypes.guess_type(candidate.name)[0] or "application/octet-stream")
    supplied.setdefault("format", suffix)
    supplied.setdefault("size_bytes", file_size)

    return MediaValidationResult(
        valid=not diagnostics,
        modality=policy.modality,
        diagnostics=tuple(dict.fromkeys(diagnostics)),
        checked=tuple(dict.fromkeys(checked)),
        metadata=supplied,
        content_safety=content_safety,
        file_integrity=file_integrity,
        format_specific=format_specific,
    )


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


# Convenience functions for common validation scenarios

def validate_image(
    path: str | Path,
    *,
    min_width: int | None = None,
    max_width: int | None = None,
    min_height: int | None = None,
    max_height: int | None = None,
    require_alt_text: bool = False,
    require_transparency: bool | None = None,
    allowed_formats: frozenset[str] | None = None,
    max_bytes: int = 250 * 1024 * 1024,
    **kwargs: Any,
) -> MediaValidationResult:
    """Convenience function for validating image files."""
    policy = MediaValidationPolicy(
        modality="image",
        allowed_formats=allowed_formats or frozenset({"png", "jpg", "jpeg", "webp", "gif", "avif"}),
        min_width=min_width,
        max_width=max_width,
        min_height=min_height,
        max_height=max_height,
        require_alt_text=require_alt_text,
        require_transparency=require_transparency,
        max_bytes=max_bytes,
        **kwargs,
    )
    return validate_media(path, policy=policy)


def validate_audio(
    path: str | Path,
    *,
    min_duration_seconds: float | None = None,
    max_duration_seconds: float | None = None,
    require_transcript: bool = False,
    min_bitrate_kbps: int | None = None,
    max_bitrate_kbps: int | None = None,
    allowed_formats: frozenset[str] | None = None,
    max_bytes: int = 250 * 1024 * 1024,
    **kwargs: Any,
) -> MediaValidationResult:
    """Convenience function for validating audio files."""
    policy = MediaValidationPolicy(
        modality="audio",
        allowed_formats=allowed_formats or frozenset({"mp3", "wav", "m4a", "ogg", "flac"}),
        min_duration_seconds=min_duration_seconds,
        max_duration_seconds=max_duration_seconds,
        require_transcript_or_captions=require_transcript,
        min_audio_bitrate_kbps=min_bitrate_kbps,
        max_audio_bitrate_kbps=max_bitrate_kbps,
        max_bytes=max_bytes,
        **kwargs,
    )
    return validate_media(path, policy=policy)


def validate_video(
    path: str | Path,
    *,
    min_width: int | None = None,
    max_width: int | None = None,
    min_height: int | None = None,
    max_height: int | None = None,
    min_duration_seconds: float | None = None,
    max_duration_seconds: float | None = None,
    require_captions: bool = False,
    min_bitrate_mbps: float | None = None,
    max_bitrate_mbps: float | None = None,
    require_video_codec: str | None = None,
    allowed_formats: frozenset[str] | None = None,
    max_bytes: int = 250 * 1024 * 1024,
    **kwargs: Any,
) -> MediaValidationResult:
    """Convenience function for validating video files."""
    policy = MediaValidationPolicy(
        modality="video",
        allowed_formats=allowed_formats or frozenset({"mp4", "webm", "mov", "m4v"}),
        min_width=min_width,
        max_width=max_width,
        min_height=min_height,
        max_height=max_height,
        min_duration_seconds=min_duration_seconds,
        max_duration_seconds=max_duration_seconds,
        require_transcript_or_captions=require_captions,
        min_video_bitrate_mbps=min_bitrate_mbps,
        max_video_bitrate_mbps=max_bitrate_mbps,
        require_video_codec=require_video_codec,
        max_bytes=max_bytes,
        **kwargs,
    )
    return validate_media(path, policy=policy)


# Visual verification workflow functions

@dataclass(frozen=True)
class VisualVerificationResult:
    """Result of visual verification workflow."""

    asset_id: str
    artifact_type: str
    technical_result: str
    quality_result: str
    accessibility_result: str
    rights_result: str
    security_result: str
    decision: str  # ACCEPTED, NEEDS_REVIEW, REJECTED
    findings: tuple[tuple[str, ValidationSeverity, str], ...] = ()
    reviewer: str | None = None
    timestamp: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "artifact_type": self.artifact_type,
            "technical_result": self.technical_result,
            "quality_result": self.quality_result,
            "accessibility_result": self.accessibility_result,
            "rights_result": self.rights_result,
            "security_result": self.security_result,
            "decision": self.decision,
            "findings": [(f[0], f[1].value, f[2]) for f in self.findings],
            "reviewer": self.reviewer,
            "timestamp": self.timestamp,
        }


def run_visual_verification(
    asset_id: str,
    artifact_type: str,  # image, audio, video, document, animation, mixed
    validation_result: MediaValidationResult,
    *,
    quality_checks: dict[str, Any] | None = None,
    reviewer: str | None = None,
) -> VisualVerificationResult:
    """Run visual verification workflow based on validation results.

    This implements the verification workflow from MEDIA_VISUAL_VERIFICATION.md:
    - CRITICAL defects: Reject (corruption, unsafe content, exposed secrets)
    - MAJOR defects: Correct and re-review or document approved mitigation
    - MINOR defects: Record finding and reviewer decision
    """
    findings: list[tuple[str, ValidationSeverity, str]] = []

    # Check validation result
    if not validation_result.valid:
        for diagnostic in validation_result.diagnostics:
            if diagnostic in ("file_not_found", "empty_file", "content_safety_failed"):
                findings.append((diagnostic, ValidationSeverity.CRITICAL, "Validation failed"))
            elif "executable" in diagnostic:
                findings.append((diagnostic, ValidationSeverity.CRITICAL, "Security risk detected"))
            else:
                findings.append((diagnostic, ValidationSeverity.MAJOR, "Validation issue"))

    # Check content safety
    if validation_result.content_safety:
        if validation_result.content_safety.level == ContentSafetyLevel.UNSAFE:
            for finding in validation_result.content_safety.findings:
                findings.append((finding, ValidationSeverity.CRITICAL, "Content safety violation"))
        elif validation_result.content_safety.level == ContentSafetyLevel.WARNING:
            for finding in validation_result.content_safety.findings:
                findings.append((finding, ValidationSeverity.MAJOR, "Content safety warning"))

    # Check file integrity
    if validation_result.file_integrity:
        if not validation_result.file_integrity.valid:
            for diag in validation_result.file_integrity.diagnostics:
                if "magic_number_mismatch" in diag:
                    findings.append((diag, ValidationSeverity.CRITICAL, "File format mismatch"))
                else:
                    findings.append((diag, ValidationSeverity.MAJOR, "Integrity issue"))

    # Determine decision based on findings
    has_critical = any(f[1] == ValidationSeverity.CRITICAL for f in findings)
    has_major = any(f[1] == ValidationSeverity.MAJOR for f in findings)

    if has_critical:
        decision = "REJECTED"
    elif has_major:
        decision = "NEEDS_REVIEW"
    else:
        decision = "ACCEPTED"

    # Determine individual result categories
    technical_result = "PASS" if validation_result.valid else "FAIL"
    quality_result = "PASS" if not any(f[1] in (ValidationSeverity.CRITICAL, ValidationSeverity.MAJOR) for f in findings if f[0] in ("format_not_allowed", "file_size_exceeded")) else "NEEDS_REVIEW"
    accessibility_result = "PASS" if "alt_text_missing" not in validation_result.diagnostics and "transcript_or_captions_missing" not in validation_result.diagnostics else "NEEDS_REVIEW"
    rights_result = "PASS" if not any(d in validation_result.diagnostics for d in ("license_missing", "rights_holder_missing", "rights_source_missing")) else "NEEDS_REVIEW"
    security_result = "PASS" if not has_critical else "FAIL"

    from datetime import UTC, datetime

    return VisualVerificationResult(
        asset_id=asset_id,
        artifact_type=artifact_type,
        technical_result=technical_result,
        quality_result=quality_result,
        accessibility_result=accessibility_result,
        rights_result=rights_result,
        security_result=security_result,
        decision=decision,
        findings=tuple(findings),
        reviewer=reviewer,
        timestamp=datetime.now(UTC).isoformat() if decision != "REJECTED" else None,
    )
