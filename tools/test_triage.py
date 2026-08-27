from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ALLOWED_STATUSES = frozenset({"fixed", "accepted", "blocked", "not_a_bug", "duplicate"})
REQUIRED_FIELDS = ("test_id", "status", "owner", "classification", "action", "evidence")


def load_manifest(path: Path) -> list[dict[str, Any]]:
    """Load a JSON failure-triage manifest and fail closed on malformed data."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("triage manifest schema_version must be 1")
    failures = payload.get("failures")
    if not isinstance(failures, list):
        raise ValueError("triage manifest failures must be a list")
    return failures


def validate_manifest(path: Path) -> tuple[dict[str, Any], ...]:
    """Return validated triage records; no record may remain untriaged."""
    failures = load_manifest(path)
    validated: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, record in enumerate(failures):
        if not isinstance(record, dict):
            raise ValueError(f"triage record {index} must be an object")
        missing = [field for field in REQUIRED_FIELDS if not str(record.get(field, "")).strip()]
        if missing:
            raise ValueError(f"triage record {index} missing required fields: {missing}")
        test_id = str(record["test_id"])
        if test_id in seen:
            raise ValueError(f"duplicate triage test_id: {test_id}")
        seen.add(test_id)
        status = str(record["status"])
        if status not in ALLOWED_STATUSES:
            raise ValueError(f"test {test_id} has untriaged or unsupported status: {status}")
        validated.append({key: record[key] for key in REQUIRED_FIELDS})
    return tuple(validated)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate failed-test triage before release")
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args(argv)
    records = validate_manifest(args.manifest)
    print(f"PASS: {len(records)} failed-test triage records validated from {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
