"""Assign deterministic machine-readable IDs to TODO checklist records."""
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

CHECKBOX = re.compile(r"^(?P<prefix>- \[(?: |-|x|!|~)\] )(?P<body>.*?)(?P<newline>\n?)$")
ID_MARKER = re.compile(r"\s*<!--\s*task-id:(TODO-[0-9a-f]{12})\s*-->\s*$")


def assign_ids(text: str) -> tuple[str, int]:
    """Return TODO text with an ID marker on every checklist item and its count."""
    seen: dict[str, int] = {}
    output: list[str] = []
    changed = 0
    for line in text.splitlines(keepends=True):
        match = CHECKBOX.match(line)
        if not match:
            output.append(line)
            continue
        if ID_MARKER.search(match.group("body")):
            output.append(line)
            continue
        body = ID_MARKER.sub("", match.group("body")).rstrip()
        digest = hashlib.sha1(body.encode("utf-8")).hexdigest()[:12]
        seen[digest] = seen.get(digest, 0) + 1
        if seen[digest] > 1:
            digest = hashlib.sha1(f"{body}#{seen[digest]}".encode("utf-8")).hexdigest()[:12]
        marker = f" <!-- task-id:TODO-{digest} -->"
        normalized = f"{match.group('prefix')}{body}{marker}{match.group('newline')}"
        if normalized != line:
            changed += 1
        output.append(normalized)
    return "".join(output), changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("todo", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    source = args.todo.read_text(encoding="utf-8")
    updated, changed = assign_ids(source)
    if args.write:
        args.todo.write_text(updated, encoding="utf-8")
    else:
        print(updated, end="")
    print(f"\nidentified_records={sum(1 for line in updated.splitlines() if CHECKBOX.match(line))} changed={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
