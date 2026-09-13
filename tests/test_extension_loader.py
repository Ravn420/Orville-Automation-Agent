import tempfile
from pathlib import Path
from orville_core.extension_loader import ExtensionLoader
from orville_core.extensions import ExtensionRegistry


def test_load_missing_extension(tmp_path):
    registry = ExtensionRegistry()
    loader = ExtensionLoader(registry, tmp_path)
    assert loader.load_extension("nonexistent") is False


def test_load_all_no_extensions(tmp_path):
    registry = ExtensionRegistry()
    loader = ExtensionLoader(registry, tmp_path)
    assert loader.load_all() == 0


def test_load_missing_main(tmp_path):
    registry = ExtensionRegistry()
    ext_dir = tmp_path / "myext"
    ext_dir.mkdir()
    (ext_dir / "manifest.json").write_text('{"id":"myext","name":"My Ext"}', encoding="utf-8")
    loader = ExtensionLoader(registry, tmp_path)
    assert loader.load_extension(ext_dir) is False
