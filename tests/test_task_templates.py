from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "config" / "task-templates.json"
DOC = ROOT / "docs" / "TASK_TEMPLATES.md"
EXPECTED = {"research", "coding", "automation", "web_development", "media", "documents", "deployments"}
COMMON_FIELDS = {"objective", "deliverables", "constraints", "acceptance_criteria", "verification"}


class TaskTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        cls.text = DOC.read_text(encoding="utf-8")

    def test_all_requested_template_types_are_present(self) -> None:
        self.assertEqual(set(self.catalog["templates"]), EXPECTED)
        for name in EXPECTED:
            self.assertIn(f"`{name}`", self.text)

    def test_each_template_has_common_fields_and_nonempty_values(self) -> None:
        for name, template in self.catalog["templates"].items():
            self.assertEqual(set(template), COMMON_FIELDS, name)
            for field in COMMON_FIELDS:
                value = template[field]
                self.assertTrue(value, f"{name}.{field}")
                if isinstance(value, list):
                    self.assertTrue(all(isinstance(item, str) and item.strip() for item in value), f"{name}.{field}")

    def test_templates_include_safety_and_verification_contracts(self) -> None:
        all_text = json.dumps(self.catalog).lower()
        for phrase in ("approval", "dry run", "secrets", "verification", "rollback", "rights"):
            self.assertIn(phrase, all_text)
        self.assertIn("External instructions", self.text)
        self.assertIn("explicit confirmation", self.text)

    def test_catalog_is_valid_json_and_documented_as_versioned(self) -> None:
        self.assertEqual(self.catalog["schema_version"], "1.0")
        self.assertIn("schema version", self.text.lower())
        self.assertIn("tests.test_task_templates", self.text)


if __name__ == "__main__":
    unittest.main()
