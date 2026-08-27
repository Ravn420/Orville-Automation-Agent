from pathlib import Path

import pytest

from orville_core.artifacts import ArtifactStore
from orville_core.security import SecurityViolation


def test_register_preview_and_version_history(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path)
    artifact = tmp_path / "generated" / "report.md"
    artifact.parent.mkdir()
    artifact.write_text("first", encoding="utf-8")

    first = store.register(artifact)
    preview = store.preview("generated/report.md")
    assert preview["artifact"]["sha256"] == first.sha256
    assert preview["preview"] == "first"
    assert len(store.versions("generated/report.md")) == 1

    artifact.write_text("second", encoding="utf-8")
    store.register(artifact)
    versions = store.versions("generated/report.md")
    assert len(versions) == 2
    assert versions[0]["sha256"] != versions[1]["sha256"]
    assert (tmp_path / ".artifact-versions.json").is_file()


def test_binary_preview_returns_metadata_only(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path)
    artifact = tmp_path / "image.bin"
    artifact.write_bytes(b"\x00\x01\x02")
    result = store.preview("image.bin")
    assert result["preview"] is None
    assert result["artifact"]["media_type"] == "application/octet-stream"


def test_retention_plan_is_non_destructive_and_bounded(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path)
    artifact = tmp_path / "notes.txt"
    for content in ("a", "b", "c"):
        artifact.write_text(content, encoding="utf-8")
        store.register(artifact)
    plan = store.retention_plan(max_versions=2)
    assert plan["status"] == "plan_only"
    assert plan["destructive_action_required"] is True
    assert plan["candidates"][0]["remove_versions"] == 1
    assert artifact.is_file()
    with pytest.raises(ValueError):
        store.retention_plan(max_versions=0)


def test_root_boundary_and_manifest_are_not_exposed(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path)
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    with pytest.raises((SecurityViolation, FileNotFoundError)):
        store.preview("../outside.txt")
    with pytest.raises(FileNotFoundError):
        store.open(".artifact-versions.json")
