from pathlib import Path

import pytest

from orville_core.artifacts import ArtifactStore
from orville_core.models import Checkpoint, TaskGraph
from orville_core.provenance import Citation, SourceRecord


def test_checkpoint_round_trips_source_records_and_citations() -> None:
    graph = TaskGraph("graph-1", "demo", [])
    checkpoint = Checkpoint(
        "run-1",
        graph,
        source_records=[SourceRecord("src-1", "https://example.com/article", "Example").to_dict()],
        citations=[Citation("cite-1", "src-1", "p. 2", "Supporting detail").to_dict()],
    )
    restored = Checkpoint.from_dict(checkpoint.to_dict())
    assert restored.source_records[0]["source_id"] == "src-1"
    assert restored.citations[0]["source_id"] == "src-1"


def test_artifact_manifest_retains_source_records_and_citations(tmp_path: Path) -> None:
    artifact = tmp_path / "result.md"
    artifact.write_text("generated result", encoding="utf-8")
    store = ArtifactStore(tmp_path / "artifacts")
    copied = tmp_path / "artifacts" / "result.md"
    copied.write_text(artifact.read_text(encoding="utf-8"), encoding="utf-8")
    record = store.register(
        copied,
        source_records=[SourceRecord("src-1", "https://example.com/source", "Source").to_dict()],
        citations=[Citation("cite-1", "src-1", "section-a").to_dict()],
    )
    assert record.source_records[0]["uri"] == "https://example.com/source"
    assert record.citations[0]["citation_id"] == "cite-1"
    assert store.versions("result.md")[0]["citations"][0]["source_id"] == "src-1"


def test_provenance_rejects_credentials_or_unknown_citations() -> None:
    with pytest.raises(ValueError):
        SourceRecord("src-1", "https://user:password@example.com/source")
    with pytest.raises(ValueError):
        Checkpoint("run-1", TaskGraph("graph-1", "demo", []), citations=[Citation("cite-1", "missing").to_dict()])
