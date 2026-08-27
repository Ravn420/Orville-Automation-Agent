import tempfile
import unittest
from pathlib import Path

from orville_core import Checkpoint, SQLiteCheckpointStore, TaskGraph, TaskNode


class PersistenceTests(unittest.TestCase):
    def test_checkpoint_survives_new_store_instance(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "orville.db"
            graph = TaskGraph("graph-1", "Durable run", [TaskNode("task-1", "One", "handler")])
            checkpoint = Checkpoint("run-1", graph, context={"marker": "persisted"})
            SQLiteCheckpointStore(database).save(checkpoint)

            restored = SQLiteCheckpointStore(database).load("run-1")
            self.assertEqual(restored.run_id, "run-1")
            self.assertEqual(restored.context["marker"], "persisted")
            self.assertEqual(SQLiteCheckpointStore(database).list_run_ids(), ["run-1"])

    def test_missing_checkpoint_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            store = SQLiteCheckpointStore(Path(directory) / "orville.db")
            with self.assertRaises(FileNotFoundError):
                store.load("missing")
            self.assertFalse(store.exists("missing"))


if __name__ == "__main__":
    unittest.main()
