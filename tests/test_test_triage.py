from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.test_triage import validate_manifest


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "config" / "test_triage_manifest.json"


class TestFailureTriageTests(unittest.TestCase):
    def write_manifest(self, payload: dict) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "triage.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_default_empty_manifest_is_valid(self) -> None:
        self.assertEqual(validate_manifest(DEFAULT_MANIFEST), ())

    def test_complete_failure_record_is_validated(self) -> None:
        path = self.write_manifest({
            "schema_version": 1,
            "failures": [{
                "test_id": "tests.test_api.TestApi.test_failure",
                "status": "fixed",
                "owner": "Worker Task 2",
                "classification": "product_defect",
                "action": "Apply and verify the scoped fix",
                "evidence": "tests/test_api.py; focused test passed",
            }],
        })
        records = validate_manifest(path)
        self.assertEqual(records[0]["status"], "fixed")

    def test_missing_fields_unsupported_status_and_duplicates_fail_closed(self) -> None:
        missing = self.write_manifest({"schema_version": 1, "failures": [{"test_id": "one", "status": "fixed"}]})
        with self.assertRaisesRegex(ValueError, "missing required fields"):
            validate_manifest(missing)
        unsupported = self.write_manifest({"schema_version": 1, "failures": [{
            "test_id": "one", "status": "untriaged", "owner": "team", "classification": "unknown", "action": "triage", "evidence": "local"
        }]})
        with self.assertRaisesRegex(ValueError, "unsupported status"):
            validate_manifest(unsupported)
        duplicate = self.write_manifest({"schema_version": 1, "failures": [
            {"test_id": "one", "status": "fixed", "owner": "team", "classification": "defect", "action": "fix", "evidence": "local"},
            {"test_id": "one", "status": "fixed", "owner": "team", "classification": "defect", "action": "fix", "evidence": "local"},
        ]})
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_manifest(duplicate)


if __name__ == "__main__":
    unittest.main()
