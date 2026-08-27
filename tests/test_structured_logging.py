from __future__ import annotations

from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

from orville_core.structured_logging import StructuredLogger, write_jsonl_event


class StructuredLoggingTests(unittest.TestCase):
    def test_nested_events_share_execution_correlation_id(self) -> None:
        stream = StringIO()
        logger = StructuredLogger(stream)
        with logger.execution("run-42", task_id="task-7", agent_id="agent-code") as correlation_id:
            record = logger.event("task.completed", execution_id="run-42", task_id="task-7", agent_id="agent-code", result={"status": "ok"})
        lines = [json.loads(line) for line in stream.getvalue().splitlines()]
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0]["correlation_id"], correlation_id)
        self.assertEqual(lines[1]["correlation_id"], correlation_id)
        self.assertEqual(record["execution_id"], "run-42")

    def test_events_are_json_and_secret_safe(self) -> None:
        stream = StringIO()
        record = StructuredLogger(stream).event(
            "provider.failed",
            execution_id="run-1",
            error={"api_key": "synthetic-test-key", "message": "bounded"},
        )
        parsed = json.loads(stream.getvalue())
        self.assertEqual(parsed, record)
        self.assertEqual(parsed["error"]["api_key"], "[redacted]")
        self.assertIn("correlation_id", parsed)
        self.assertNotIn("synthetic-test-key", stream.getvalue())

    def test_jsonl_writer_preserves_structured_record(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = write_jsonl_event(Path(directory) / "events.jsonl", {"event": "x", "correlation_id": "corr-1"})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["correlation_id"], "corr-1")

    def test_message_size_is_bounded(self) -> None:
        stream = StringIO()
        record = StructuredLogger(stream, max_message=100).event("large", execution_id="run-1", detail="x" * 500)
        self.assertLessEqual(len(record["detail"]), 100)


if __name__ == "__main__":
    unittest.main()
