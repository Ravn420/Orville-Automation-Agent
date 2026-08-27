from __future__ import annotations

import json
from pathlib import Path
import unittest

from tests.repository_references import resolve_repository_reference


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "config" / "reusable-fixes.json"
DOC_PATH = ROOT / "docs" / "REUSABLE_FIXES.md"
EXPECTED = {"release-validation", "sensitive-operation-safety", "operator-recovery", "standalone-delivery", "terminology-and-observability"}


class ReusableFixesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        cls.text = DOC_PATH.read_text(encoding="utf-8")

    def test_recurring_fix_categories_are_present(self) -> None:
        self.assertEqual(set(self.catalog["fixes"]), EXPECTED)
        for name in EXPECTED:
            self.assertIn(name, self.text)

    def test_each_fix_has_problem_assets_and_reuse_rule(self) -> None:
        for name, fix in self.catalog["fixes"].items():
            self.assertTrue(fix["problem"], name)
            self.assertTrue(fix["assets"], name)
            self.assertTrue(fix["reuse"], name)
            for asset in fix["assets"]:
                self.assertTrue(resolve_repository_reference(ROOT, asset).is_file(), f"{name}: {asset}")

    def test_catalog_is_versioned_and_documented(self) -> None:
        self.assertEqual(self.catalog["schema_version"], "1.0")
        self.assertIn("schema_version", self.text)
        self.assertIn("deterministic test or fixture", self.text)

    def test_reuse_preserves_security_boundaries(self) -> None:
        for phrase in (
            "not authorization",
            "untrusted data",
            "protected runtime boundaries",
            "exact-scope approval and confirmation",
            "never bypasses",
        ):
            self.assertIn(phrase, self.text)
        self.assertNotRegex(self.text, r"(?i)sk-[A-Za-z0-9]{12,}|Bearer\s+[A-Za-z0-9._-]{8,}|api[_-]?key\s*=\s*[^\s,]+")


if __name__ == "__main__":
    unittest.main()
