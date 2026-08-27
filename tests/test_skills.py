from __future__ import annotations

import json
import zipfile

import pytest

from orville_core.extensions import PermissionSet
from orville_core.skills import SkillRegistry, SkillSecurityError


def make_skill(root, *, skill_id="release-notes"):
    root.mkdir(parents=True, exist_ok=True)
    (root / "skill.json").write_text(json.dumps({"skill_id": skill_id, "version": "1.0.0", "name": "Release Notes", "description": "Create release notes", "permissions": {"tools": ["read_file"], "network_hosts": [], "scopes": []}, "required_tools": ["read_file"]}), encoding="utf-8")
    (root / "SKILL.md").write_text("# Release Notes\nRead the changelog and summarize verified changes.", encoding="utf-8")
    return root


def test_install_requires_approval_and_persists(tmp_path):
    source = make_skill(tmp_path / "source")
    registry = SkillRegistry(tmp_path / "installed")
    grant = PermissionSet(tools=frozenset({"read_file"}))
    with pytest.raises(PermissionError, match="explicit approval"):
        registry.install(source, granted=grant)
    record = registry.install(source, granted=grant, approved=True)
    assert record.status == "installed"
    assert registry.instructions(record.skill_id).startswith("# Release Notes")
    reloaded = SkillRegistry(tmp_path / "installed")
    assert reloaded.get(record.skill_id).checksum == record.checksum


def test_permission_excess_is_rejected(tmp_path):
    source = make_skill(tmp_path / "source")
    registry = SkillRegistry(tmp_path / "installed")
    with pytest.raises(PermissionError, match="permissions exceed"):
        registry.install(source, granted=PermissionSet(), approved=True)


def test_zip_path_traversal_is_rejected(tmp_path):
    archive_path = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("../escape.txt", "unsafe")
    registry = SkillRegistry(tmp_path / "installed")
    with pytest.raises(SkillSecurityError, match="path traversal"):
        registry.install(archive_path, granted=PermissionSet(), approved=True)


def test_disable_quarantine_and_uninstall(tmp_path):
    source = make_skill(tmp_path / "source")
    registry = SkillRegistry(tmp_path / "installed")
    grant = PermissionSet(tools=frozenset({"read_file"}))
    record = registry.install(source, granted=grant, approved=True)
    registry.set_enabled(record.skill_id, False)
    with pytest.raises(PermissionError, match="not enabled"):
        registry.instructions(record.skill_id)
    quarantined = registry.quarantine(record.skill_id, "manual review")
    assert quarantined.status.startswith("quarantined:")
    registry.uninstall(record.skill_id)
    with pytest.raises(KeyError):
        registry.get(record.skill_id)
