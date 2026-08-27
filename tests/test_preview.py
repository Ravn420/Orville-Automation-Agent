import tempfile
import unittest
from pathlib import Path

from orville_core.preview import PreviewManager


class PreviewTests(unittest.TestCase):
    def test_preview_is_revision_pinned_and_smoke_report_is_structured(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = PreviewManager()
            preview = manager.create("preview-1", "rev-1", directory, route="/dashboard", viewport="mobile")
            context = manager.select_element(element_id="hero-title", route="/dashboard", selector="#hero-title", component="Hero", source_file="src/Hero.tsx", line_start=10, line_end=12, computed_styles={"color": "black"})
            patch = manager.style_patch(context, "color", "white")
            self.assertEqual(patch.previous_value, "black")
            report = manager.smoke_report(preview, steps=["opened", "navigated"])
            self.assertTrue(report.passed)
            self.assertEqual(report.viewport, "mobile")

    def test_unsafe_style_and_invalid_preview_inputs_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = PreviewManager()
            with self.assertRaises(ValueError):
                manager.create("preview", "rev", directory, viewport="phone")
            context = manager.select_element(element_id="x", route="/", selector="#x")
            with self.assertRaises(ValueError):
                manager.style_patch(context, "position", "fixed")
            with self.assertRaises(ValueError):
                manager.style_patch(context, "color", "url(https://example.test)")


if __name__ == "__main__":
    unittest.main()
