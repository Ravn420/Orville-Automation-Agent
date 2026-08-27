from pathlib import Path

from orville_core import IDEInspector, inspect_repository


def test_ide_inspector_discovers_entries_configs_dependencies_and_shared_interfaces(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
    (tmp_path / "main.py").write_text("import json\nfrom pathlib import Path\n\nclass Provider:\n    pass\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    report = inspect_repository(tmp_path)
    assert "main.py" in report.inspected_paths
    assert "main.py" in report.entry_points
    assert "pyproject.toml" in report.configuration_files
    assert ("main.py", "json") in report.dependency_edges
    assert any(item.endswith(":Provider") for item in report.shared_interfaces)


def test_ide_inspector_skips_large_files_and_records_risk(tmp_path: Path):
    large = tmp_path / "large.txt"
    large.write_text("x" * 20, encoding="utf-8")
    report = IDEInspector(tmp_path, max_file_bytes=10).inspect()
    assert "large.txt" not in report.inspected_paths
    assert any("large.txt" in risk for risk in report.risks)
