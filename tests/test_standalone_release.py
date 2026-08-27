import json
from pathlib import Path

import pytest

from tools.standalone_release import backup_directory, make_plan, migrate_config, restore_directory


def test_release_actions_are_plan_only_by_default(tmp_path: Path) -> None:
    plan = make_plan("upgrade", tmp_path, "1.2.3")
    assert plan.execute is False
    assert "create a versioned data backup" in plan.steps
    assert make_plan("deploy", tmp_path, "1.2.3").steps[-1] == "run post-deployment smoke checks"


def test_config_migration_is_forward_only_and_non_secret(tmp_path: Path) -> None:
    migrated = migrate_config({"config_version": 0, "name": "local"})
    assert migrated["config_version"] == 1
    assert migrated["storage"] == {}
    assert migrated["privacy"]["local_only"] is False
    with pytest.raises(ValueError):
        migrate_config({"config_version": 2}, target_version=1)
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"config_version": 0}), encoding="utf-8")
    assert "api_key" not in config.read_text(encoding="utf-8")


def test_backup_and_restore_are_explicit_and_isolated(tmp_path: Path) -> None:
    source = tmp_path / "data"
    source.mkdir()
    (source / "state.json").write_text("v1", encoding="utf-8")
    backup = backup_directory(source, tmp_path / "backups", "1.0.0")
    (source / "state.json").write_text("v2", encoding="utf-8")
    restored = tmp_path / "restored"
    restore_directory(backup, restored)
    assert (restored / "state.json").read_text(encoding="utf-8") == "v1"
    assert (source / "state.json").read_text(encoding="utf-8") == "v2"


def test_restore_refuses_nonempty_destination(tmp_path: Path) -> None:
    backup = tmp_path / "backup"
    backup.mkdir()
    (backup / "state").write_text("safe", encoding="utf-8")
    destination = tmp_path / "destination"
    destination.mkdir()
    (destination / "existing").write_text("keep", encoding="utf-8")
    with pytest.raises(FileExistsError):
        restore_directory(backup, destination)
