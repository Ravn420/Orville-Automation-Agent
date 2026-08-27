"""Approval-gated TUF trust-root bootstrap and rotation command."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from orville_core.tuf_metadata import TufRepositoryVerifier, TufVerificationError


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap or rotate an Orville TUF trust root")
    parser.add_argument("--root", required=True, type=Path, help="signed root metadata JSON")
    parser.add_argument("--store", required=True, type=Path, help="destination trusted-root JSON")
    parser.add_argument("--rotate-from", type=Path, help="existing trusted-root JSON to rotate")
    parser.add_argument("--expected-sha256", help="pinned canonical JSON SHA-256 for initial bootstrap")
    parser.add_argument("--approve", action="store_true", help="explicitly approve the trust-root ceremony")
    args = parser.parse_args()
    if not args.approve:
        parser.error("--approve is required; review the root out-of-band before changing trust")
    try:
        root = json.loads(args.root.read_text(encoding="utf-8"))
        if args.rotate_from:
            verifier = TufRepositoryVerifier.load(args.rotate_from)
            verifier.rotate_root(root, approved=True)
            args.store.parent.mkdir(parents=True, exist_ok=True)
            args.store.write_text(json.dumps(verifier.root_metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(json.dumps({"status": "rotated", "version": verifier.root_metadata["signed"]["version"]}))
        else:
            verifier = TufRepositoryVerifier.bootstrap(args.store, root, approved=True, expected_sha256=args.expected_sha256)
            print(json.dumps({"status": "bootstrapped", "version": verifier.root_metadata["signed"]["version"]}))
    except (OSError, ValueError, TufVerificationError) as exc:
        print(json.dumps({"status": "rejected", "diagnostic": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
