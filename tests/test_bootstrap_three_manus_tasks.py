from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "bootstrap_three_manus_tasks.py"
spec = importlib.util.spec_from_file_location("bootstrap_three_manus_tasks", MODULE_PATH)
assert spec and spec.loader
bootstrap = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bootstrap
spec.loader.exec_module(bootstrap)


class BootstrapExistingTaskTests(TestCase):
    def test_supplied_task_ids_are_verified_and_bound_without_creation(self) -> None:
        with TemporaryDirectory() as raw:
            repo = Path(raw)
            (repo / "TODO.md").write_text("- [ ] first\n", encoding="utf-8")
            state_path = repo / "state.json"
            manifest_path = repo / "manifest.json"
            task_ids = ["job-3", "job-2", "job-1"]
            with patch.dict(os.environ, {"MANUS_API_KEY": "synthetic-key"}), patch.object(
                bootstrap, "verify_task", side_effect=["running", "queued", "stopped"]
            ) as verify, patch.object(bootstrap, "create_task") as create:
                with patch.object(
                    sys,
                    "argv",
                    [
                        "bootstrap_three_manus_tasks.py",
                        "--repo",
                        str(repo),
                        "--state",
                        str(state_path),
                        "--manifest",
                        str(manifest_path),
                        "--task-id",
                        task_ids[0],
                        "--task-id",
                        task_ids[1],
                        "--task-id",
                        task_ids[2],
                    ],
                ):
                    self.assertEqual(bootstrap.main(), 0)

            create.assert_not_called()
            self.assertEqual(verify.call_count, 3)
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual([item["task_id"] for item in state["active_tasks"]], task_ids)
            self.assertEqual(state["allowlist_mode"], "exactly-three-task-ids")
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["task_ids"], task_ids)
            self.assertEqual(manifest["source"], "provided-existing-task-ids")

    def test_task_id_option_requires_exactly_three_unique_values(self) -> None:
        with TemporaryDirectory() as raw:
            repo = Path(raw)
            (repo / "TODO.md").write_text("- [ ] first\n", encoding="utf-8")
            with patch.dict(os.environ, {"MANUS_API_KEY": "synthetic-key"}), patch.object(
                sys,
                "argv",
                ["bootstrap_three_manus_tasks.py", "--repo", str(repo), "--task-id", "only-one"],
            ), self.assertRaises(SystemExit) as raised:
                bootstrap.main()
            self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    import unittest

    unittest.main()
