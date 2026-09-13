from pathlib import Path

import pytest

from orville_core.project_files import ProjectFilesStore, project_slug


def test_project_slug_is_stable_and_safe():
    assert project_slug("My Space Project") == "my-space-project"
    assert project_slug("  Orville / Prime  ") == "orville-prime"
    with pytest.raises(ValueError):
        project_slug("---")


def test_files_are_isolated_by_project(tmp_path: Path):
    source = tmp_path / "result.md"
    source.write_text("project one", encoding="utf-8")
    store = ProjectFilesStore(tmp_path / "project_files")

    first = store.store("Alpha", source)
    source.write_text("project two", encoding="utf-8")
    second = store.store("Beta", source)

    assert first.relative_path == "result.md"
    assert second.relative_path == "result.md"
    assert (tmp_path / "project_files" / "alpha" / "result.md").read_text() == "project one"
    assert (tmp_path / "project_files" / "beta" / "result.md").read_text() == "project two"
    assert [item.name for item in store.list_project("Alpha")] == ["result.md"]
    assert [item.name for item in store.list_project("Beta")] == ["result.md"]


def test_nested_project_files_preview_and_manifest(tmp_path: Path):
    source = tmp_path / "report.md"
    source.write_text("# Research\n\nverified", encoding="utf-8")
    store = ProjectFilesStore(tmp_path / "project_files")
    store.store("Research Project", source, relative_name="research/report.md")

    preview = store.preview("Research Project", "research/report.md")
    manifest = store.project_manifest("Research Project")
    assert preview["preview"].startswith("# Research")
    assert manifest["project_slug"] == "research-project"
    assert manifest["files"][0]["relative_path"] == "research/report.md"


def test_relative_name_cannot_escape_project(tmp_path: Path):
    source = tmp_path / "unsafe.txt"
    source.write_text("unsafe", encoding="utf-8")
    store = ProjectFilesStore(tmp_path / "project_files")
    with pytest.raises(ValueError):
        store.store("Safe", source, relative_name="../unsafe.txt")
