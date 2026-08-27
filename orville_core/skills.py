"""Local skill package registry for Orville.

Skills are treated as untrusted extensions. This module only installs and audits
metadata/instructions; execution remains subject to the task sandbox and approval
policy. ZIP extraction is path-safe and registry metadata is atomically persisted.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .extensions import PermissionSet


def _now() -> str:
    return datetime.now(UTC).isoformat()


class SkillSecurityError(ValueError):
    pass


@dataclass(frozen=True)
class SkillRecord:
    skill_id: str
    version: str
    name: str
    description: str
    instructions_path: str
    source: str
    checksum: str
    permissions: PermissionSet = field(default_factory=PermissionSet)
    required_tools: tuple[str, ...] = ()
    status: str = "installed"
    installed_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["permissions"] = {
            "tools": sorted(self.permissions.tools),
            "network_hosts": sorted(self.permissions.network_hosts),
            "scopes": sorted(self.permissions.scopes),
        }
        data["required_tools"] = list(self.required_tools)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SkillRecord":
        raw = dict(data)
        raw["permissions"] = PermissionSet(**raw.get("permissions", {}))
        raw["required_tools"] = tuple(raw.get("required_tools", ()))
        return cls(**raw)


class SkillRegistry:
    def __init__(self, root: str | Path, *, metadata_path: str | Path | None = None) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.metadata_path = Path(metadata_path or (self.root / "skills.json")).resolve()
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        self._records: dict[str, SkillRecord] = {}
        self._load()

    def _load(self) -> None:
        if not self.metadata_path.exists():
            return
        try:
            data = json.loads(self.metadata_path.read_text(encoding="utf-8"))
            self._records = {item["skill_id"]: SkillRecord.from_dict(item) for item in data.get("skills", [])}
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise SkillSecurityError(f"skill registry cannot be loaded: {exc}") from exc

    def _save(self) -> None:
        temporary = self.metadata_path.with_suffix(self.metadata_path.suffix + ".tmp")
        temporary.write_text(json.dumps({"skills": [record.to_dict() for record in self._records.values()]}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, self.metadata_path)

    @staticmethod
    def _safe_id(value: str) -> str:
        normalized = "".join(char.lower() if char.isalnum() or char in "-_" else "-" for char in value).strip("-")
        if not normalized or len(normalized) > 100:
            raise SkillSecurityError("skill id is invalid")
        return normalized

    @staticmethod
    def _permission_set(data: dict[str, Any]) -> PermissionSet:
        if not isinstance(data, dict):
            raise SkillSecurityError("permissions must be an object")
        return PermissionSet(tools=frozenset(str(item) for item in data.get("tools", [])), network_hosts=frozenset(str(item).lower() for item in data.get("network_hosts", [])), scopes=frozenset(str(item) for item in data.get("scopes", [])))

    def _read_package(self, package_root: Path) -> tuple[dict[str, Any], Path]:
        manifest_path = package_root / "skill.json"
        instructions_path = package_root / "SKILL.md"
        manifest: dict[str, Any] = {}
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise SkillSecurityError(f"invalid skill.json: {exc}") from exc
        if not instructions_path.is_file():
            raise SkillSecurityError("skill package must contain SKILL.md")
        skill_id = self._safe_id(str(manifest.get("skill_id") or manifest.get("name") or package_root.name))
        version = str(manifest.get("version", "1.0.0"))[:40]
        if not version or any(char in version for char in "\\/\x00"):
            raise SkillSecurityError("skill version is invalid")
        permissions = self._permission_set(manifest.get("permissions", {}))
        required_tools = tuple(str(item) for item in manifest.get("required_tools", []))
        normalized = {"skill_id": skill_id, "version": version, "name": str(manifest.get("name", skill_id))[:200], "description": str(manifest.get("description", ""))[:2_000], "permissions": permissions, "required_tools": required_tools}
        return normalized, instructions_path

    @staticmethod
    def _checksum(root: Path) -> str:
        digest = hashlib.sha256()
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            digest.update(path.relative_to(root).as_posix().encode("utf-8"))
            digest.update(path.read_bytes())
        return digest.hexdigest()

    def install(self, source: str | Path, *, granted: PermissionSet, approved: bool = False) -> SkillRecord:
        source_path = Path(source).expanduser().resolve()
        if not source_path.exists():
            raise FileNotFoundError(source_path)
        temporary_root: Path | None = None
        if source_path.is_file() and source_path.suffix.lower() == ".zip":
            temporary_root = Path(tempfile.mkdtemp(prefix="orville-skill-"))
            try:
                with zipfile.ZipFile(source_path) as archive:
                    for member in archive.infolist():
                        destination = (temporary_root / member.filename).resolve()
                        if not str(destination).startswith(str(temporary_root) + os.sep):
                            raise SkillSecurityError("skill archive contains path traversal")
                        if member.is_dir():
                            destination.mkdir(parents=True, exist_ok=True)
                        else:
                            destination.parent.mkdir(parents=True, exist_ok=True)
                            with archive.open(member) as reader, destination.open("wb") as writer:
                                shutil.copyfileobj(reader, writer, length=1024 * 1024)
                candidates = [item for item in temporary_root.iterdir() if item.is_dir()]
                package_root = candidates[0] if len(candidates) == 1 and (candidates[0] / "SKILL.md").exists() else temporary_root
                return self._install_directory(package_root, source=str(source_path), granted=granted, approved=approved)
            finally:
                shutil.rmtree(temporary_root, ignore_errors=True)
        if not source_path.is_dir():
            raise SkillSecurityError("skill source must be a directory or ZIP archive")
        return self._install_directory(source_path, source=str(source_path), granted=granted, approved=approved)

    def _install_directory(self, package_root: Path, *, source: str, granted: PermissionSet, approved: bool) -> SkillRecord:
        manifest, instructions = self._read_package(package_root)
        requested = manifest["permissions"]
        if not granted.allows(requested):
            raise PermissionError(f"skill permissions exceed grant: {manifest['skill_id']}")
        if not approved:
            raise PermissionError(f"skill requires explicit approval: {manifest['skill_id']}")
        destination = self.root / manifest["skill_id"] / manifest["version"]
        if destination.exists():
            shutil.rmtree(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(package_root, destination)
        record = SkillRecord(manifest["skill_id"], manifest["version"], manifest["name"], manifest["description"], str((destination / instructions.name).relative_to(self.root)), source, self._checksum(destination), requested, manifest["required_tools"])
        self._records[record.skill_id] = record
        self._save()
        return record

    def list(self, *, include_disabled: bool = True) -> tuple[SkillRecord, ...]:
        values = tuple(self._records.values())
        return values if include_disabled else tuple(item for item in values if item.status == "installed")

    def get(self, skill_id: str) -> SkillRecord:
        try:
            return self._records[skill_id]
        except KeyError as exc:
            raise KeyError(f"skill not installed: {skill_id}") from exc

    def set_enabled(self, skill_id: str, enabled: bool) -> SkillRecord:
        current = self.get(skill_id)
        updated = SkillRecord(**{**asdict(current), "permissions": current.permissions, "required_tools": current.required_tools, "status": "installed" if enabled else "disabled"})
        self._records[skill_id] = updated
        self._save()
        return updated

    def quarantine(self, skill_id: str, reason: str = "security review") -> SkillRecord:
        current = self.get(skill_id)
        updated = SkillRecord(**{**asdict(current), "permissions": current.permissions, "required_tools": current.required_tools, "status": f"quarantined:{reason[:160]}"})
        self._records[skill_id] = updated
        self._save()
        return updated

    def uninstall(self, skill_id: str) -> None:
        current = self.get(skill_id)
        skill_root = self.root / skill_id
        if not str(skill_root).startswith(str(self.root) + os.sep):
            raise SkillSecurityError("skill path escapes registry root")
        shutil.rmtree(skill_root, ignore_errors=True)
        del self._records[current.skill_id]
        self._save()

    def instructions(self, skill_id: str) -> str:
        record = self.get(skill_id)
        if record.status != "installed":
            raise PermissionError(f"skill is not enabled: {skill_id}")
        path = (self.root / record.instructions_path).resolve()
        if not str(path).startswith(str(self.root) + os.sep) or not path.is_file():
            raise SkillSecurityError("skill instructions path is invalid")
        return path.read_text(encoding="utf-8")
