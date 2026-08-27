"""Non-destructive release migrations for Orville user data."""
from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

CURRENT_VERSION = 1


def migrate_data_root(root: str | Path) -> dict[str, object]:
    """Create required directories and record a versioned migration ledger.

    The baseline migration never deletes or rewrites user content. Before a
    future schema migration changes SQLite, the migration runner can add a
    timestamped backup to ``backups`` and then advance this ledger.
    """
    base = Path(root)
    base.mkdir(parents=True, exist_ok=True)
    for relative in (".orville/checkpoints", "artifacts", "models", "backups"):
        (base / relative).mkdir(parents=True, exist_ok=True)
    ledger_path = base / "schema-version.json"
    try:
        ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else {"version": 0, "history": []}
    except (OSError, json.JSONDecodeError):
        ledger = {"version": 0, "history": []}
    version = int(ledger.get("version", 0))
    history = list(ledger.get("history", []))
    if version < CURRENT_VERSION:
        database = base / ".orville" / "orville.db"
        if database.exists() and version == 0:
            backup = base / "backups" / f"orville.db.before-v{CURRENT_VERSION}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}.bak"
            shutil.copy2(database, backup)
        history.append({"from": version, "to": CURRENT_VERSION, "at": datetime.now(UTC).isoformat(), "mode": "non-destructive-baseline"})
        version = CURRENT_VERSION
        ledger = {"version": version, "history": history}
        ledger_path.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    return ledger
