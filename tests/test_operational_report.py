from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tools.operational_report import build_report, load_events


class OperationalReportTests(unittest.TestCase):
    def test_report_aggregates_execution_health(self) -> None:
        report = build_report(
            [
                {"execution_id": "run-1", "status": "completed", "duration_seconds": 2.0},
                {"execution_id": "run-1", "status": "failed", "level": "error", "duration_seconds": 4.0},
                {"execution_id": "run-2", "status": "completed", "duration_seconds": 1.0},
            ],
            target="attached-desktop",
        )
        self.assertEqual(report["event_count"], 3)
        self.assertEqual(report["execution_count"], 2)
        self.assertEqual(report["failure_count"], 1)
        self.assertEqual(report["success_rate"], 0.6667)
        self.assertEqual(report["duration_seconds"]["max"], 4.0)

    def test_empty_log_is_explicitly_not_an_execution_claim(self) -> None:
        report = build_report([], target="sandbox")
        self.assertEqual(report["event_count"], 0)
        self.assertEqual(report["success_rate"], 1.0)
        self.assertEqual(report["execution_count"], 0)
        self.assertTrue(report["data_quality"]["bounded"])

    def test_malformed_log_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            path.write_text('{"event":"ok"}\nnot-json\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_events(path)

    def test_all_supported_targets_are_accepted(self) -> None:
        for target in ("local", "attached-desktop", "sandbox", "web-hosting", "persistent-computing"):
            self.assertEqual(build_report([], target=target)["target"], target)


if __name__ == "__main__":
    unittest.main()
