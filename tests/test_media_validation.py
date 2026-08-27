"""Focused tests for deterministic media acceptance checks."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from orville_core.media_validation import MediaValidationPolicy, validate_media


class MediaValidationTests(unittest.TestCase):
    """Verify positive and negative media acceptance criteria."""

    def test_documentation_covers_required_check_domains(self) -> None:
        document = (Path(__file__).resolve().parents[1] / "docs" / "MEDIA_VALIDATION_CHECKS.md").read_text(encoding="utf-8")
        for term in ("Format", "Resolution", "Duration", "Accessibility", "Usage rights", "diagnostic codes"):
            self.assertIn(term, document)
        self.assertIn("does not decode media", document)

    def test_image_passes_all_declared_checks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cover.png"
            path.write_bytes(b"image")
            result = validate_media(
                path,
                policy=MediaValidationPolicy("image", min_width=320, min_height=180, require_alt_text=True),
                metadata={"width": 640, "height": 360},
                accessibility={"alt_text": "A signal room"},
                usage_rights={"license": "CC BY 4.0", "rights_holder": "Orville", "source": "local"},
            )
            self.assertTrue(result.valid)
            self.assertEqual(result.diagnostics, ())
            self.assertIn("resolution_width", result.checked)

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
            self.assertEqual(
                result.diagnostics,
                ("format_not_allowed", "duration_exceeded", "transcript_or_captions_missing", "license_missing", "rights_holder_missing", "rights_source_missing"),
            )

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
            path.write_bytes(b"12345")
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


if __name__ == "__main__":
    unittest.main()
