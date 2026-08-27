from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest import TestCase


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "poll_task_replication.py"
spec = importlib.util.spec_from_file_location("poll_task_replication", MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class PollTaskReplicationTests(TestCase):
    def test_rejects_malformed_task_id(self) -> None:
        with self.assertRaises(ValueError):
            module.validate_task_id("too-short")

    def test_retries_404_until_task_is_visible(self) -> None:
        responses = iter([
            (404, {"ok": False, "error": {"code": "not_found"}}),
            (404, {"ok": False, "error": {"code": "not_found"}}),
            (200, {"ok": True, "task": {"status": "running"}}),
        ])
        sleeps: list[float] = []
        clock = iter([0.0, 0.1, 0.2, 0.3])
        result = module.poll_until_visible(
            "A" * 22,
            "synthetic-key",
            interval_seconds=5,
            timeout_seconds=30,
            request_fn=lambda _task_id, _api_key: next(responses),
            sleep_fn=sleeps.append,
            monotonic_fn=lambda: next(clock),
        )
        self.assertEqual(result.outcome, "visible")
        self.assertEqual(result.attempts, 3)
        self.assertEqual(result.task_status, "running")
        self.assertEqual(sleeps, [5, 5])

    def test_times_out_on_persistent_404(self) -> None:
        clock_values = iter([0.0, 0.4, 1.0, 1.0])
        result = module.poll_until_visible(
            "B" * 22,
            "synthetic-key",
            interval_seconds=0.5,
            timeout_seconds=1,
            request_fn=lambda _task_id, _api_key: (404, {"ok": False, "error": {"code": "not_found"}}),
            sleep_fn=lambda _seconds: None,
            monotonic_fn=lambda: next(clock_values),
        )
        self.assertEqual(result.outcome, "timeout")
        self.assertEqual(result.http_status, 404)
        self.assertEqual(result.error_code, "not_found")

    def test_does_not_retry_terminal_permission_error(self) -> None:
        calls = 0

        def request(_task_id: str, _api_key: str) -> tuple[int, dict[str, object]]:
            nonlocal calls
            calls += 1
            return 403, {"ok": False, "error": {"code": "permission_denied"}}

        result = module.poll_until_visible(
            "C" * 22,
            "synthetic-key",
            request_fn=request,
            sleep_fn=lambda _seconds: self.fail("terminal error must not sleep"),
        )
        self.assertEqual(result.outcome, "terminal_error")
        self.assertEqual(result.http_status, 403)
        self.assertEqual(calls, 1)


if __name__ == "__main__":
    import unittest

    unittest.main()
