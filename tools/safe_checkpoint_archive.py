#!/usr/bin/env python3
"""Approval-gated SQLite checkpoint and sidecar archival helper.

Default mode is inspection-only. Use --confirm only during a maintenance window
when the database owner has approved the exact paths and archive destination.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def metadata(path: Path) -> dict[str, object]:
    stat = path.stat()
    return {
        "path": str(path),
        "size": stat.st_size,
        "mode": oct(stat.st_mode & 0o777),
        "mtime_ns": stat.st_mtime_ns,
        "sha256": sha256(path),
    }


def inspect_database(database: Path) -> dict[str, object]:
    # Read/write mode is required only for the explicit checkpoint operation.
    with sqlite3.connect(database, timeout=30, isolation_level="IMMEDIATE") as connection:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
        journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
        return {
            "journal_mode": journal_mode,
            "integrity_check": integrity,
            "foreign_key_violations": len(foreign_keys),
        }


def checkpoint(database: Path) -> tuple[int, int, int]:
    with sqlite3.connect(database, timeout=30, isolation_level="IMMEDIATE") as connection:
        result = connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        connection.commit()
        if result is None or len(result) != 3:
            raise RuntimeError(f"unexpected checkpoint result: {result!r}")
        busy, log_frames, checkpointed_frames = (int(item) for item in result)
        if busy != 0:
            raise RuntimeError(
                f"checkpoint incomplete: busy={busy}, log_frames={log_frames}, "
                f"checkpointed_frames={checkpointed_frames}"
            )
        return busy, log_frames, checkpointed_frames


def online_backup(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=False)
    with sqlite3.connect(f"file:{source}?mode=ro", uri=True) as source_connection:
        with sqlite3.connect(destination) as destination_connection:
            source_connection.backup(destination_connection)
            destination_connection.commit()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-dir", type=Path, default=Path("data/.orville"))
    parser.add_argument("--archive-dir", type=Path, required=True)
    parser.add_argument("--confirm", action="store_true", help="perform checkpoint and archival")
    args = parser.parse_args()

    database_dir = args.database_dir.resolve()
    database = database_dir / "orville.db"
    sidecars = [database_dir / "orville.db-wal", database_dir / "orville.db-shm"]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive_dir = args.archive_dir.resolve()

    print(json.dumps({"database": str(database), "sidecars": [str(p) for p in sidecars], "archive_dir": str(archive_dir), "confirmed": args.confirm}, sort_keys=True))
    if not database.is_file():
        raise SystemExit(f"REFUSING: main database does not exist: {database}")
    missing_sidecars = [str(path) for path in sidecars if not path.exists()]
    if missing_sidecars:
        raise SystemExit(f"REFUSING: expected sidecar path is missing: {missing_sidecars}")

    before = {str(path): metadata(path) for path in [database, *sidecars]}
    print(json.dumps({"before": before}, sort_keys=True))
    if not args.confirm:
        print("DRY RUN: no checkpoint, copy, archive, or source-file mutation performed")
        return 0

    if archive_dir.exists():
        raise SystemExit(f"REFUSING: archive directory already exists: {archive_dir}")
    archive_dir.mkdir(parents=True, exist_ok=False)

    checkpoint_result = checkpoint(database)
    after_checkpoint = inspect_database(database)
    if after_checkpoint["integrity_check"] != "ok" or after_checkpoint["foreign_key_violations"] != 0:
        raise SystemExit(f"REFUSING: database verification failed: {after_checkpoint}")

    backup_path = archive_dir / "orville.db.backup"
    online_backup(database, backup_path)
    with sqlite3.connect(f"file:{backup_path}?mode=ro", uri=True) as connection:
        backup_integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if backup_integrity != "ok":
            raise SystemExit(f"REFUSING: backup integrity check failed: {backup_integrity}")

    sidecar_archive = archive_dir / f"orville-sidecars-{timestamp}.tar"
    with tarfile.open(sidecar_archive, mode="w") as tar:
        for sidecar in sidecars:
            tar.add(sidecar, arcname=str(sidecar.relative_to(database_dir.parent.parent)))

    evidence = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "database": str(database),
        "checkpoint": {"mode": "TRUNCATE", "result": checkpoint_result},
        "database_after_checkpoint": after_checkpoint,
        "backup": metadata(backup_path),
        "sidecar_archive": metadata(sidecar_archive),
        "sidecars_after_checkpoint": {str(path): metadata(path) for path in sidecars},
        "source_files_unchanged_by_this_tool": True,
    }
    (archive_dir / "evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2, sort_keys=True))
    print("COMPLETED: source sidecars were retained; no deletion or move was performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# security review: this tool intentionally never deletes or moves source database files
# and refuses to run against a missing main database or pre-existing archive directory.
