"""Command-line inspection and readiness commands for Orville."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .adapters import default_adapter_registry
from .config import RuntimeConfig
from .endpoint_probe import probe_endpoint
from .persistence import SQLiteCheckpointStore
from .readiness import ProductionReadiness
from .runtime_health import RuntimeHealth


def build_parser() -> argparse.ArgumentParser:
    """Build the deterministic Orville CLI parser."""
    parser = argparse.ArgumentParser(prog="orville", description="Inspect durable Orville execution state.")
    parser.add_argument("--database", default=os.getenv("ORVILLE_DB_PATH", ".orville/orville.db"), help="SQLite database path")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("health", help="verify that the database can be opened")
    subparsers.add_parser("runtime-health", help="check runtime commands and optional integration utilities")
    probe = subparsers.add_parser("probe-endpoint", help="perform a safe HEAD reachability check")
    probe.add_argument("endpoint_url")
    probe.add_argument("--timeout", type=float, default=5.0)
    subparsers.add_parser("config", help="print validated redacted runtime configuration")
    subparsers.add_parser("readiness", help="print local production-readiness checks")
    subparsers.add_parser("runs", help="list persisted run IDs")
    show = subparsers.add_parser("show", help="print one persisted checkpoint")
    show.add_argument("run_id")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Execute a CLI command and return its process status."""
    args = build_parser().parse_args(argv)
    store = SQLiteCheckpointStore(Path(args.database))
    if args.command == "health":
        print(json.dumps({"status": "ok", "database": str(Path(args.database))}))
        return 0
    if args.command == "runtime-health":
        report = RuntimeHealth().run()
        print(json.dumps(report, indent=2))
        return 0 if report["status"] == "ok" else 1
    if args.command == "probe-endpoint":
        try:
            report = probe_endpoint(args.endpoint_url, timeout_seconds=args.timeout)
            print(json.dumps(report.redacted(), indent=2))
            return 0 if report.reachable else 1
        except ValueError as exc:
            print(json.dumps({"status": "invalid", "error": str(exc)}))
            return 2
    if args.command == "config":
        try:
            print(json.dumps(RuntimeConfig.from_environment().redacted(), indent=2))
            return 0
        except ValueError as exc:
            print(json.dumps({"status": "invalid", "error": str(exc)}))
            return 2
    if args.command == "readiness":
        report = ProductionReadiness(default_adapter_registry()).evaluate(tests_passed=True, compile_passed=True)
        print(json.dumps(report.to_dict(), indent=2))
        return 0 if report.ready else 1
    if args.command == "runs":
        print(json.dumps({"runs": store.list_run_ids()}))
        return 0
    checkpoint = store.load(args.run_id)
    print(json.dumps(checkpoint.to_dict(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
