from __future__ import annotations

import importlib.util
import sys
import urllib.error
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "orville_manus_worker.py"
spec = importlib.util.spec_from_file_location("orville_worker_creation_validation", MODULE_PATH)
assert spec and spec.loader
worker = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = worker
spec.loader.exec_module(worker)


class WorkerCreationValidationTests(TestCase):
    def test_creation_validation_retries_404_until_readable(self) -> None:
        statuses = iter(["404", "running"])
        sleeps: list[float] = []

        def status(_task_id: str, _key: str) -> str:
            value = next(statuses)
            if value == "404":
                raise urllib.error.HTTPError("https://api.manus.ai/v2/task.detail", 404, "Not Found", None, None)
            return value

        valid, detail = worker.validate_create_readability(
            Path("."),
            "synthetic-key",
            retries=3,
            interval_seconds=2,
            create_fn=lambda _repo, _key: "A" * 22,
            status_fn=status,
            sleep_fn=sleeps.append,
        )
        self.assertTrue(valid)
        self.assertIn("attempts=2", detail)
        self.assertEqual(sleeps, [2])

    def test_creation_validation_fails_after_bounded_404_retries(self) -> None:
        sleeps: list[float] = []

        def status(_task_id: str, _key: str) -> str:
            raise urllib.error.HTTPError("https://api.manus.ai/v2/task.detail", 404, "Not Found", None, None)

        valid, detail = worker.validate_create_readability(
            Path("."),
            "synthetic-key",
            retries=3,
            interval_seconds=1,
            create_fn=lambda _repo, _key: "B" * 22,
            status_fn=status,
            sleep_fn=sleeps.append,
        )
        self.assertFalse(valid)
        self.assertIn("http_status=404", detail)
        self.assertEqual(sleeps, [1, 1])

    def test_creation_validation_stops_on_terminal_error(self) -> None:
        calls = 0

        def status(_task_id: str, _key: str) -> str:
            nonlocal calls
            calls += 1
            raise urllib.error.HTTPError("https://api.manus.ai/v2/task.detail", 403, "Forbidden", None, None)

        valid, detail = worker.validate_create_readability(
            Path("."),
            "synthetic-key",
            create_fn=lambda _repo, _key: "C" * 22,
            status_fn=status,
            sleep_fn=lambda _seconds: self.fail("terminal error must not retry"),
        )
        self.assertFalse(valid)
        self.assertIn("http_status=403", detail)
        self.assertEqual(calls, 1)

    def test_scaled_concurrency_requires_validation_flag(self) -> None:
        self.assertFalse(worker.validate_create_readability_gate.__doc__ is None)
        self.assertEqual(worker.DEFAULT_MAX_ACTIVE_TASKS, 10)
        # The production gate is opt-in; a three-task invocation remains usable
        # without making any task-creation request.
        self.assertEqual(worker.run_once.__defaults__[0], False)

    def test_scaled_startup_fails_closed_when_validation_fails(self) -> None:
        with TemporaryDirectory() as raw:
            repo = Path(raw)
            (repo / "TODO.md").write_text("- [ ] test\n", encoding="utf-8")
            worker.save_state(repo, {"active_tasks": [{"task_id": "existing", "todo_project": str(repo), "todo_line": 1, "todo_item": "test"}]})
            with patch.dict("os.environ", {"MANUS_API_KEY": "synthetic-key"}), patch.object(
                worker, "validate_create_readability_gate", return_value=(False, "http_status=404 attempts=3")
            ):
                result = worker.run_once(
                    repo,
                    max_active_tasks=10,
                    validate_create_readability=True,
                    enforce_validation_gate=True,
                )
            self.assertEqual(result, 2)


if __name__ == "__main__":
    import unittest

    unittest.main()
