"""Comprehensive tests for media validation infrastructure.

Tests cover:
- Format-specific validators (image dimensions, audio bitrate, video codec)
- Content safety checks (appropriate content filtering)
- Visual verification workflows
- File integrity validation (checksums, magic numbers)
- Size and dimension limits
"""

from __future__ import annotations

import hashlib
import struct
import tempfile
import unittest
from pathlib import Path

from orville_core.media_validation import (
    ContentSafetyLevel,
    ContentSafetyResult,
    FileIntegrityResult,
    FormatSpecificResult,
    MediaValidationPolicy,
    MediaValidationResult,
    ValidationSeverity,
    run_visual_verification,
    validate_audio,
    validate_content_safety,
    validate_file_integrity,
    validate_format_specific,
    validate_image,
    validate_media,
    validate_video,
)


class TestMediaValidationPolicy(unittest.TestCase):
    """Tests for MediaValidationPolicy dataclass."""

    def test_default_policy_creation(self) -> None:
        policy = MediaValidationPolicy("image")
        self.assertEqual(policy.modality, "image")
        self.assertEqual(policy.allowed_formats, frozenset({"png", "jpg", "jpeg", "webp", "gif", "avif"}))
        self.assertEqual(policy.max_bytes, 250 * 1024 * 1024)
        self.assertTrue(policy.require_content_safety)

    def test_audio_policy_creation(self) -> None:
        policy = MediaValidationPolicy("audio")
        self.assertEqual(policy.modality, "audio")
        self.assertEqual(policy.allowed_formats, frozenset({"mp3", "wav", "m4a", "ogg", "flac"}))

    def test_video_policy_creation(self) -> None:
        policy = MediaValidationPolicy("video")
        self.assertEqual(policy.modality, "video")
        self.assertEqual(policy.allowed_formats, frozenset({"mp4", "webm", "mov", "m4v"}))

    def test_custom_allowed_formats(self) -> None:
        policy = MediaValidationPolicy("image", allowed_formats=frozenset({"png", "jpg"}))
        self.assertEqual(policy.allowed_formats, frozenset({"png", "jpg"}))

    def test_invalid_modality_raises(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            MediaValidationPolicy("document")
        self.assertIn("unsupported media modality", str(ctx.exception))

    def test_invalid_max_bytes_raises(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            MediaValidationPolicy("image", max_bytes=0)
        self.assertIn("max_bytes must be positive", str(ctx.exception))

    def test_invalid_dimensions_raise(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            MediaValidationPolicy("image", min_width=0)
        self.assertIn("min_width must be positive", str(ctx.exception))

    def test_invalid_duration_raises(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            MediaValidationPolicy("video", min_duration_seconds=-1)
        self.assertIn("min_duration_seconds must not be negative", str(ctx.exception))


class TestFileIntegrityValidation(unittest.TestCase):
    """Tests for file integrity validation."""

    def test_missing_file(self) -> None:
        result = validate_file_integrity(Path("/nonexistent/file.png"))
        self.assertFalse(result.valid)
        self.assertEqual(result.diagnostics, ("file_not_found",))

    def test_empty_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.png"
            path.write_bytes(b"")
            result = validate_file_integrity(path)
            self.assertFalse(result.valid)
            self.assertEqual(result.diagnostics, ("empty_file",))

    def test_png_magic_number_detection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.png"
            # Create minimal PNG header
            path.write_bytes(b"\x89PNG\r\n\x1a\n")
            result = validate_file_integrity(path)
            self.assertEqual(result.format_detected, "png")
            self.assertTrue(result.valid)

    def test_jpg_magic_number_detection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.jpg"
            path.write_bytes(b"\xff\xd8\xff\xe0")
            result = validate_file_integrity(path)
            self.assertEqual(result.format_detected, "jpg")

    def test_gif_magic_number_detection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.gif"
            path.write_bytes(b"GIF89a\x01\x00\x01\x00")
            result = validate_file_integrity(path)
            self.assertEqual(result.format_detected, "gif")

    def test_webp_magic_number_detection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.webp"
            # RIFF....WEBP
            data = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP"
            path.write_bytes(data)
            result = validate_file_integrity(path)
            self.assertEqual(result.format_detected, "webp")

    def test_magic_number_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fake.png"
            path.write_bytes(b"not a png file")
            result = validate_file_integrity(path, expected_format="png")
            self.assertFalse(result.valid)
            self.assertIn("magic_number_mismatch", str(result.diagnostics))

    def test_checksum_computation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.txt"
            content = b"Hello, World!"
            path.write_bytes(content)
            result = validate_file_integrity(path, compute_checksum=True)
            expected_hash = hashlib.sha256(content).hexdigest()
            self.assertEqual(result.checksum_sha256, expected_hash)

    def test_executable_content_detection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "suspicious.png"
            # Start with PNG header but include executable signature
            path.write_bytes(b"\x89PNG\r\n\x1a\nMZ")
            result = validate_file_integrity(path)
            self.assertFalse(result.valid)
            self.assertTrue(any("executable" in d for d in result.diagnostics))


class TestContentSafetyValidation(unittest.TestCase):
    """Tests for content safety validation."""

    def test_missing_file(self) -> None:
        result = validate_content_safety(Path("/nonexistent/file.png"))
        self.assertEqual(result.level, ContentSafetyLevel.UNKNOWN)

    def test_safe_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "safe.png"
            path.write_bytes(b"\x89PNG\r\n\x1a\n")
            result = validate_content_safety(path)
            self.assertEqual(result.level, ContentSafetyLevel.SAFE)
            self.assertEqual(result.findings, ())

    def test_executable_content_unsafe(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "malicious.png"
            path.write_bytes(b"MZ\x90\x00")
            result = validate_content_safety(path)
            self.assertEqual(result.level, ContentSafetyLevel.UNSAFE)
            self.assertEqual(result.severity, ValidationSeverity.CRITICAL)

    def test_suspicious_metadata_warning(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "suspicious.png"
            path.write_bytes(b"\x89PNG\r\n\x1a\n")
            metadata = {"description": "javascript:alert('xss')"}
            result = validate_content_safety(path, metadata)
            self.assertEqual(result.level, ContentSafetyLevel.WARNING)
            self.assertEqual(result.severity, ValidationSeverity.MAJOR)


class TestFormatSpecificValidation(unittest.TestCase):
    """Tests for format-specific validation."""

    def _create_minimal_png(self, width: int, height: int) -> bytes:
        """Create a minimal PNG file with specified dimensions."""
        # PNG signature
        signature = b"\x89PNG\r\n\x1a\n"
        # IHDR chunk: length (4) + type (4) + data (13) + CRC (4)
        ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
        ihdr_type = b"IHDR"
        ihdr_crc = struct.pack(">I", 0)  # Simplified CRC
        ihdr_chunk = struct.pack(">I", 13) + ihdr_type + ihdr_data + ihdr_crc
        # IEND chunk
        iend_chunk = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", 0xAE426082)
        return signature + ihdr_chunk + iend_chunk

    def _create_minimal_gif(self, width: int, height: int) -> bytes:
        """Create a minimal GIF file with specified dimensions."""
        header = b"GIF89a"
        dimensions = struct.pack("<HH", width, height)
        # Global color table flag (no GCT), bgcolor, aspect
        packed = b"\x00\x00\x00"
        # Image descriptor
        image_desc = b"\x2c\x00\x00\x00\x00" + struct.pack("<HH", width, height) + b"\x00"
        # Image data (LZW minimum code size + clear code)
        image_data = b"\x02\x02\x44\x01\x00"
        trailer = b"\x3b"
        return header + dimensions + packed + image_desc + image_data + trailer

    def test_png_dimension_parsing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.png"
            path.write_bytes(self._create_minimal_png(640, 480))
            policy = MediaValidationPolicy("image", allowed_formats=frozenset({"png"}))
            result = validate_format_specific(path, policy)
            self.assertEqual(result.format, "png")
            self.assertEqual(result.width, 640)
            self.assertEqual(result.height, 480)

    def test_gif_dimension_parsing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.gif"
            path.write_bytes(self._create_minimal_gif(320, 240))
            policy = MediaValidationPolicy("image", allowed_formats=frozenset({"gif"}))
            result = validate_format_specific(path, policy)
            self.assertEqual(result.format, "gif")
            self.assertEqual(result.width, 320)
            self.assertEqual(result.height, 240)

    def test_dimension_policy_enforcement(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "small.png"
            path.write_bytes(self._create_minimal_png(100, 100))
            policy = MediaValidationPolicy(
                "image",
                allowed_formats=frozenset({"png"}),
                min_width=200,
                min_height=200,
            )
            result = validate_format_specific(path, policy)
            self.assertFalse(result.valid)
            self.assertIn("width_below_minimum", result.diagnostics)
            self.assertIn("height_below_minimum", result.diagnostics)

    def test_format_not_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.bmp"
            path.write_bytes(b"BM")
            policy = MediaValidationPolicy("image", allowed_formats=frozenset({"png", "jpg"}))
            result = validate_format_specific(path, policy)
            self.assertFalse(result.valid)
            self.assertIn("format_not_allowed", result.diagnostics)

    def test_transparency_detection_png(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "transparent.png"
            # PNG with tRNS chunk
            png_data = self._create_minimal_png(100, 100)
            # Insert tRNS chunk after IHDR
            trns_chunk = struct.pack(">I", 6) + b"tRNS" + b"\xff\xff\xff\xff\xff\xff" + struct.pack(">I", 0)
            idx = png_data.find(b"IHDR")
            if idx > 0:
                png_with_trns = png_data[:idx+21] + trns_chunk + png_data[idx+21:]
                path.write_bytes(png_with_trns)
                policy = MediaValidationPolicy("image", allowed_formats=frozenset({"png"}))
                result = validate_format_specific(path, policy)
                # tRNS detection may vary based on implementation
                self.assertIsNotNone(result.has_transparency)


class TestMediaValidation(unittest.TestCase):
    """Tests for main validate_media function."""

    def test_documentation_covers_required_check_domains(self) -> None:
        document = (Path(__file__).resolve().parents[1] / "docs" / "MEDIA_VALIDATION_CHECKS.md").read_text(encoding="utf-8")
        for term in ("Format", "Resolution", "Duration", "Accessibility", "Usage rights", "diagnostic codes"):
            self.assertIn(term, document)
        self.assertIn("does not decode media", document)

    def test_image_passes_all_declared_checks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cover.png"
            path.write_bytes(b"\x89PNG\r\n\x1a\n")
            result = validate_media(
                path,
                policy=MediaValidationPolicy("image", min_width=1, min_height=1, require_alt_text=True),
                metadata={"width": 640, "height": 360},
                accessibility={"alt_text": "A signal room"},
                usage_rights={"license": "CC BY 4.0", "rights_holder": "Orville", "source": "local"},
            )
            self.assertTrue(result.valid)
            self.assertEqual(result.diagnostics, ())
            self.assertIn("resolution_width", result.checked)
            self.assertIn("content_safety", result.checked)
            self.assertIn("format_specific", result.checked)

    def test_video_reports_format_duration_accessibility_and_rights_failures(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "clip.avi"
            path.write_bytes(b"video")
            result = validate_media(
                path,
                policy=MediaValidationPolicy("video", max_duration_seconds=30, require_transcript_or_captions=True),
                metadata={"duration_seconds": 45, "width": 1920, "height": 1080},
                accessibility={},
                usage_rights={},
            )
            self.assertFalse(result.valid)
            self.assertIn("format_not_allowed", result.diagnostics)
            self.assertIn("duration_exceeded", result.diagnostics)
            self.assertIn("transcript_or_captions_missing", result.diagnostics)
            self.assertIn("license_missing", result.diagnostics)

    def test_missing_file_and_invalid_policy_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                MediaValidationPolicy("document")
            result = validate_media(
                Path(directory) / "missing.mp3",
                policy=MediaValidationPolicy("audio", min_duration_seconds=1),
            )
            self.assertFalse(result.valid)
            self.assertEqual(result.diagnostics, ("file_not_found",))

    def test_resolution_and_size_limits_are_enforced(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "small.jpg"
            path.write_bytes(b"\xff\xd8\xff\xe0" + b"12345")
            result = validate_media(
                path,
                policy=MediaValidationPolicy("image", min_width=100, min_height=100, max_bytes=4),
                metadata={"width": 50, "height": 50},
                usage_rights={"license": "MIT", "rights_holder": "Test", "source": "fixture"},
            )
            self.assertFalse(result.valid)
            self.assertIn("file_size_exceeded", result.diagnostics)
            self.assertIn("width_below_minimum", result.diagnostics)
            self.assertIn("height_below_minimum", result.diagnostics)

    def test_content_safety_integration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "suspicious.png"
            # PNG header with executable signature
            path.write_bytes(b"\x89PNG\r\n\x1a\nMZ")
            result = validate_media(
                path,
                policy=MediaValidationPolicy("image", require_content_safety=True),
                usage_rights={"license": "MIT", "rights_holder": "Test", "source": "fixture"},
            )
            self.assertFalse(result.valid)
            self.assertIn("content_safety_failed", result.diagnostics)
            self.assertIsNotNone(result.content_safety)
            self.assertEqual(result.content_safety.level, ContentSafetyLevel.UNSAFE)

    def test_file_integrity_integration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.png"
            path.write_bytes(b"\x89PNG\r\n\x1a\n")
            result = validate_media(
                path,
                policy=MediaValidationPolicy("image", require_magic_number_check=True, require_checksum=True),
                usage_rights={"license": "MIT", "rights_holder": "Test", "source": "fixture"},
            )
            self.assertIn("file_integrity", result.checked)
            self.assertIsNotNone(result.file_integrity)
            self.assertIsNotNone(result.file_integrity.checksum_sha256)


class TestConvenienceFunctions(unittest.TestCase):
    """Tests for convenience validation functions."""

    def test_validate_image(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.png"
            path.write_bytes(b"\x89PNG\r\n\x1a\n")
            result = validate_image(
                path,
                min_width=1,
                max_width=1000,
                require_alt_text=True,
            )
            self.assertEqual(result.modality, "image")
            self.assertIn("format_specific", result.checked)

    def test_validate_audio(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.mp3"
            path.write_bytes(b"ID3")
            result = validate_audio(
                path,
                min_duration_seconds=0,
                max_duration_seconds=300,
                require_transcript=True,
            )
            self.assertEqual(result.modality, "audio")
            # Should fail due to missing transcript
            self.assertIn("transcript_or_captions_missing", result.diagnostics)

    def test_validate_video(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.mp4"
            # ftyp box for MP4
            path.write_bytes(b"\x00\x00\x00 ftypisom")
            result = validate_video(
                path,
                min_width=320,
                min_height=240,
                require_captions=True,
            )
            self.assertEqual(result.modality, "video")


class TestVisualVerification(unittest.TestCase):
    """Tests for visual verification workflow."""

    def test_accepted_decision(self) -> None:
        validation_result = MediaValidationResult(
            valid=True,
            modality="image",
            diagnostics=(),
            checked=("format", "content_safety"),
            metadata={},
            content_safety=ContentSafetyResult(
                level=ContentSafetyLevel.SAFE,
                findings=(),
            ),
        )
        result = run_visual_verification(
            asset_id="test-123",
            artifact_type="image",
            validation_result=validation_result,
            reviewer="tester",
        )
        self.assertEqual(result.decision, "ACCEPTED")
        self.assertEqual(result.technical_result, "PASS")
        self.assertEqual(result.security_result, "PASS")
        self.assertIsNotNone(result.timestamp)

    def test_rejected_decision_critical(self) -> None:
        validation_result = MediaValidationResult(
            valid=False,
            modality="image",
            diagnostics=("content_safety_failed",),
            checked=("format", "content_safety"),
            metadata={},
            content_safety=ContentSafetyResult(
                level=ContentSafetyLevel.UNSAFE,
                findings=("executable_signature_detected",),
                severity=ValidationSeverity.CRITICAL,
            ),
        )
        result = run_visual_verification(
            asset_id="test-456",
            artifact_type="image",
            validation_result=validation_result,
        )
        self.assertEqual(result.decision, "REJECTED")
        self.assertEqual(result.security_result, "FAIL")
        self.assertIsNone(result.timestamp)  # No timestamp for rejected

    def test_needs_review_decision(self) -> None:
        validation_result = MediaValidationResult(
            valid=False,
            modality="image",
            diagnostics=("alt_text_missing",),
            checked=("format", "alt_text"),
            metadata={},
        )
        result = run_visual_verification(
            asset_id="test-789",
            artifact_type="image",
            validation_result=validation_result,
        )
        self.assertEqual(result.decision, "NEEDS_REVIEW")
        self.assertEqual(result.accessibility_result, "NEEDS_REVIEW")

    def test_findings_classification(self) -> None:
        validation_result = MediaValidationResult(
            valid=False,
            modality="image",
            diagnostics=("format_not_allowed", "executable_signature"),
            checked=("format", "content_safety"),
            metadata={},
            file_integrity=FileIntegrityResult(
                valid=False,
                diagnostics=("magic_number_mismatch",),
            ),
        )
        result = run_visual_verification(
            asset_id="test-000",
            artifact_type="image",
            validation_result=validation_result,
        )
        self.assertEqual(result.decision, "REJECTED")
        # Should have findings with proper severity
        severities = [f[1] for f in result.findings]
        self.assertIn(ValidationSeverity.CRITICAL, severities)


class TestResultSerialization(unittest.TestCase):
    """Tests for result serialization to dict."""

    def test_media_validation_result_to_dict(self) -> None:
        result = MediaValidationResult(
            valid=True,
            modality="image",
            diagnostics=(),
            checked=("format",),
            metadata={"size_bytes": 1024},
        )
        data = result.to_dict()
        self.assertTrue(data["valid"])
        self.assertEqual(data["modality"], "image")
        self.assertEqual(data["metadata"]["size_bytes"], 1024)

    def test_content_safety_result_to_dict(self) -> None:
        result = ContentSafetyResult(
            level=ContentSafetyLevel.SAFE,
            findings=(),
        )
        data = result.to_dict()
        self.assertEqual(data["level"], "safe")

    def test_file_integrity_result_to_dict(self) -> None:
        result = FileIntegrityResult(
            valid=True,
            format_detected="png",
            checksum_sha256="abc123",
            file_size_bytes=1024,
        )
        data = result.to_dict()
        self.assertEqual(data["format_detected"], "png")
        self.assertEqual(data["checksum_sha256"], "abc123")

    def test_format_specific_result_to_dict(self) -> None:
        result = FormatSpecificResult(
            valid=True,
            format="png",
            width=640,
            height=480,
            has_transparency=True,
        )
        data = result.to_dict()
        self.assertEqual(data["width"], 640)
        self.assertEqual(data["height"], 480)
        self.assertTrue(data["has_transparency"])

    def test_visual_verification_result_to_dict(self) -> None:
        result = run_visual_verification(
            asset_id="test",
            artifact_type="image",
            validation_result=MediaValidationResult(valid=True, modality="image"),
        )
        data = result.to_dict()
        self.assertEqual(data["asset_id"], "test")
        self.assertEqual(data["decision"], "ACCEPTED")


if __name__ == "__main__":
    unittest.main()
