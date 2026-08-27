"""Standalone packaging and safe lifecycle workflow utilities for Orville.

All filesystem mutations require ``--execute`` at the CLI boundary. The module
keeps migration and plan generation deterministic so it can run without Manus,
network credentials, or a deployment provider.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CURRENT_CONFIG_VERSION = 1


@dataclass(frozen=True)
class ReleasePlan:
    action: str
    root: str
    version: str
    execute: bool
    steps: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def migrate_config(config: dict[str, Any], *, target_version: int = CURRENT_CONFIG_VERSION) -> dict[str, Any]:
    """Apply deterministic, forward-only configuration migrations."""
    if not isinstance(config, dict):
        raise ValueError("configuration must be an object")
    version = config.get("config_version", 0)
    if not isinstance(version, int) or version < 0:
        raise ValueError("config_version must be a non-negative integer")
    if target_version < version:
        raise ValueError("downgrade migrations are not supported")
    migrated = dict(config)
    if version < 1 <= target_version:
        migrated.setdefault("storage", {})
        migrated.setdefault("providers", [])
        migrated.setdefault("privacy", {"local_only": False})
        migrated["config_version"] = 1
    migrated["config_version"] = target_version
    return migrated


def make_plan(action: str, root: Path, version: str, *, execute: bool = False) -> ReleasePlan:
    steps = {
        "package": ("validate pyproject.toml", "build a wheel into release/", "write checksums and release evidence"),
        "migrate": ("read configuration", "apply forward-only migration", "write a backup and migrated configuration"),
        "install": ("validate package and destination", "create an isolated installation", "run an entry-point smoke check"),
        "upgrade": ("create a versioned data backup", "migrate configuration", "install the new package", "run health checks"),
        "rollback": ("validate the named backup", "restore data only after explicit execution", "run health checks"),
        "deploy": ("run deployment preflight", "execute target-specific deployment only when approved", "run post-deployment smoke checks"),
    }
    if action not in steps:
        raise ValueError(f"unsupported release action: {action}")
    return ReleasePlan(action, str(root.resolve()), version, execute, steps[action])


def backup_directory(source: Path, backup_root: Path, version: str) -> Path:
    """Create a versioned copy without deleting or modifying the source."""
    source = source.resolve()
    if not source.is_dir():
        raise FileNotFoundError(source)
    backup_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    destination = backup_root / f"{version}-{stamp}"
    shutil.copytree(source, destination)
    return destination


def restore_directory(backup: Path, destination: Path) -> None:
    """Restore a named backup into an empty or nonexistent destination."""
    backup = backup.resolve()
    destination = destination.resolve()
    if not backup.is_dir():
        raise FileNotFoundError(backup)
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError("rollback destination must be empty")
    destination.mkdir(parents=True, exist_ok=True)
    for item in backup.iterdir():
        target = destination / item.name
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def migrate_file(source: Path, destination: Path) -> None:
    payload = json.loads(source.read_text(encoding="utf-8"))
    migrated = migrate_config(payload)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(migrated, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(destination)


def package(root: Path, output: Path, *, execute: bool) -> None:
    output.mkdir(parents=True, exist_ok=True)
    if not execute:
        return
    command = [sys.executable, "-m", "build", "--wheel", "--outdir", str(output)]
    completed = subprocess.run(command, cwd=root, check=False)
    if completed.returncode:
        raise RuntimeError("wheel build failed; install the local build dependency and retry")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("package", "migrate", "install", "upgrade", "rollback", "deploy"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--version", default="0.1.0")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--target", choices=("sandbox", "web-hosting", "attached-desktop", "persistent-computing"))
    parser.add_argument("--execute", action="store_true", help="permit the requested local mutation or deployment")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    plan = make_plan(args.action, root, args.version, execute=args.execute)
    if args.action == "package":
        package(root, args.destination or root / "release", execute=args.execute)
    elif args.action == "migrate":
        if not args.config:
            parser.error("migrate requires --config")
        destination = args.destination or args.config.with_suffix(args.config.suffix + ".migrated")
        if args.execute:
            migrate_file(args.config, destination)
    elif args.action == "rollback":
        if not args.backup or not args.destination:
            parser.error("rollback requires --backup and --destination")
        if args.execute:
            restore_directory(args.backup, args.destination)
    elif args.action in {"install", "upgrade"} and args.execute:
        if not args.destination:
            parser.error(f"{args.action} requires --destination when --execute is used")
        args.destination.mkdir(parents=True, exist_ok=True)
    elif args.action == "deploy":
        if not args.target:
            parser.error("deploy requires --target")
        if args.execute:
            script = root / "deploy.ps1"
            completed = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), "-Target", args.target, "-Version", args.version, "-Execute"], cwd=root, check=False)
            if completed.returncode:
                raise RuntimeError("deployment workflow failed")
    output = plan.to_dict()
    if args.json:
        print(json.dumps(output, sort_keys=True))
    else:
        print(f"{args.action}: {'executing' if args.execute else 'plan-only'}")
        for step in plan.steps:
            print(f"- {step}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
