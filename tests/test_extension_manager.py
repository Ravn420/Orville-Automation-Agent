import tempfile
from pathlib import Path
from orville_core.extension_manager import ExtensionManager
from orville_core.extensions import ExtensionRegistry
import zipfile


def test_extension_manager_instantiation(tmp_path):
    registry = ExtensionRegistry()
    extensions_dir = tmp_path / "ext"
    config_dir = tmp_path / "config"
    extensions_dir.mkdir()
    config_dir.mkdir()
    manager = ExtensionManager(registry, extensions_dir, config_dir)
    assert manager is not None


def test_install_nonexistent(tmp_path):
    registry = ExtensionRegistry()
    manager = ExtensionManager(registry, tmp_path / "ext", tmp_path / "config")
    try:
        manager.install_from_archive(Path("nonexistent.orv"))
    except FileNotFoundError:
        pass
    else:
        assert False, "Expected FileNotFoundError"


def test_enable_nonexistent(tmp_path):
    registry = ExtensionRegistry()
    manager = ExtensionManager(registry, tmp_path / "ext", tmp_path / "config")
    assert manager.enable_extension("foo") is False


def test_install_and_enable(tmp_path):
    registry = ExtensionRegistry()
    extensions_dir = tmp_path / "ext"
    config_dir = tmp_path / "config"
    extensions_dir.mkdir()
    config_dir.mkdir()
    manager = ExtensionManager(registry, extensions_dir, config_dir)

    # Create dummy extension zip
    ext_dir = tmp_path / "dummy_ext"
    ext_dir.mkdir()
    (ext_dir / "manifest.json").write_text('{"id":"dummy","name":"Dummy","version":"1.0"}
# added tests coverage for ExtensionManager lifecycle', encoding="utf-8")
    zip_path = tmp_path / "dummy.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.write(ext_dir / "manifest.json", arcname="manifest.json")

    ext_id = manager.install_from_archive(zip_path)
    assert ext_id == "dummy"
    assert manager.installed_extensions[ext_id]["enabled"] is False
    assert manager.enable_extension(ext_id) is True
    assert manager.installed_extensions[ext_id]["enabled"] is True
