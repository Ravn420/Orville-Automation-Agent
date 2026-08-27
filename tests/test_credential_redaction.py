from __future__ import annotations

import json

from orville_core.checkpoint import CheckpointStore
from orville_core.models import Checkpoint, TaskGraph, TaskNode
from orville_core.persistence import SQLiteCheckpointStore
from orville_core.security import SecretRedactor


def _checkpoint() -> Checkpoint:
    graph = TaskGraph(graph_id="g1", name="test", tasks=[TaskNode(task_id="t1", title="test", handler="test", inputs={"api_key": "sk_live_should_not_persist"})])
    return Checkpoint(run_id="run-redaction", graph=graph, context={"Authorization": "Bearer tok_live_should_not_persist"})


def test_redactor_covers_query_secrets_and_exception_messages() -> None:
    value = SecretRedactor.redact("https://example.test?api_key=sk_live_secret&token=tok_live_secret")
    assert "sk_live_secret" not in value
    assert "tok_live_secret" not in value
    assert "[REDACTED]" in value
    assert "sk_live_secret" not in SecretRedactor.redact_exception(RuntimeError("api_key=sk_live_secret"))


def test_file_checkpoint_store_redacts_payload(tmp_path) -> None:
    path = CheckpointStore(tmp_path).save(_checkpoint())
    raw = path.read_text(encoding="utf-8")
    assert "sk_live_should_not_persist" not in raw
    assert "tok_live_should_not_persist" not in raw


def test_sqlite_checkpoint_store_redacts_payload(tmp_path) -> None:
    database = tmp_path / "checkpoints.sqlite"
    SQLiteCheckpointStore(database).save(_checkpoint())
    import sqlite3
    with sqlite3.connect(database) as connection:
        raw = connection.execute("SELECT payload FROM checkpoints").fetchone()[0]
    assert "sk_live_should_not_persist" not in raw
    assert "tok_live_should_not_persist" not in raw
    json.loads(raw)
