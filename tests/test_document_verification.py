"""Focused tests for document and presentation verification."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from orville_core.document_verification import DocumentVerificationPolicy, verify_document


class DocumentVerificationTests(unittest.TestCase):
    """Verify positive and negative document-quality checks."""

    def test_documentation_covers_counts_evidence_and_legibility_boundaries(self) -> None:
        document = (Path(__file__).resolve().parents[1] / "docs" / "DOCUMENT_VERIFICATION.md").read_text(encoding="utf-8")
        for term in ("Page/slide count", "Citations", "Links", "Charts", "Images", "Legibility", "text_legibility_unavailable_without_render"):
            self.assertIn(term, document)

    def test_markdown_report_passes_required_checks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.md"
            path.write_text(
                "# Report\n\n![Revenue chart](chart.png)\n\nSee [source](https://example.test/source) and [1].\n\n## References\n\n[1]: https://example.test/source\n",
                encoding="utf-8",
            )
            result = verify_document(
                path,
                policy=DocumentVerificationPolicy(require_citations=True, require_links=True, require_charts=True, require_images=True),
            )
            self.assertTrue(result.valid)
            self.assertEqual(result.count, 1)
            self.assertEqual(result.findings, ())
            self.assertEqual(result.metadata["charts"], 1)

    def test_markdown_report_identifies_missing_quality_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "incomplete.md"
            path.write_text("# Draft\n\n![ ](image.png)\n", encoding="utf-8")
            result = verify_document(
                path,
                policy=DocumentVerificationPolicy(require_citations=True, require_links=True, require_charts=True, require_images=True),
            )
            self.assertFalse(result.valid)
            for finding in ("citations_missing", "links_missing", "charts_missing", "image_alt_text_missing"):
                self.assertIn(finding, result.findings)

    def test_count_and_legibility_failures_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dense.md"
            path.write_text("A" * 241 + "\n", encoding="utf-8")
            result = verify_document(path, policy=DocumentVerificationPolicy(expected_count=2))
            self.assertFalse(result.valid)
            self.assertIn("count_mismatch", result.findings)
            self.assertIn("legibility_headings_missing", result.findings)
            self.assertIn("legibility_line_too_long", result.findings)

    def test_unsupported_and_missing_files_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertIn("file_not_found", verify_document(root / "missing.pdf").findings)
            unsupported = root / "notes.txt"
            unsupported.write_text("text", encoding="utf-8")
            self.assertIn("format_unsupported", verify_document(unsupported).findings)


if __name__ == "__main__":
    unittest.main()
