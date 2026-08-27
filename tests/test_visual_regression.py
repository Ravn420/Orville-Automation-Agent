"""Focused tests for deterministic visual-regression checks."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.visual_regression import check_baseline, collect_snapshot


class VisualRegressionTests(unittest.TestCase):
    """Verify the reviewed design and critical-screen baseline is reproducible."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        cls.baseline = cls.root / "tests" / "fixtures" / "visual_regression_baseline.json"
        cls.document = (cls.root / "docs" / "VISUAL_REGRESSION.md").read_text(encoding="utf-8")

    def test_current_assets_match_committed_baseline(self) -> None:
        passed, snapshot, message = check_baseline(self.baseline, self.root)
        self.assertTrue(passed, message)
        self.assertEqual(snapshot, json.loads(self.baseline.read_text(encoding="utf-8-sig")))

    def test_snapshot_contains_design_and_critical_screen_evidence(self) -> None:
        snapshot = collect_snapshot(self.root)
        self.assertEqual(snapshot["schema"], 1)
        self.assertTrue(snapshot["design_hash"])
        self.assertTrue(snapshot["structure_hash"])
        for marker in ("aria-pressed", "max-width:790px", "prefers-reduced-motion"):
            self.assertIn(marker, snapshot["structure"]["required_markers"])

    def test_changed_baseline_fails_closed(self) -> None:
        baseline = json.loads(self.baseline.read_text(encoding="utf-8-sig"))
        baseline["structure_hash"] = "changed"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "baseline.json"
            path.write_text(json.dumps(baseline), encoding="utf-8")
            passed, _snapshot, message = check_baseline(path, self.root)
        self.assertFalse(passed)
        self.assertIn("explicitly update the baseline", message)
        for phrase in ("design system", "critical", "baseline", "review"):
            self.assertIn(phrase, self.document.lower())


if __name__ == "__main__":
    unittest.main()
