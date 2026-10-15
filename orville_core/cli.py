"""Command-line inspection and readiness commands for Orville."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .adapters import default_adapter_registry
from .config import RuntimeConfig
from .connector_config import (
    ConnectorAuthType,
    ConnectorConfigManager,
    ConnectorManifest,
    ConnectorOperation,
    ConnectorRiskClass,
    ConnectorStatus,
)
from .endpoint_config import LocalModelSpec, ProviderEndpointSpec
from .endpoint_health import EndpointHealthMonitor
from .endpoint_monitor import EndpointMonitor, EndpointMonitorConfig
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

    # Endpoint management subcommands
    endpoint = subparsers.add_parser("endpoints", help="Manage endpoint configurations and health")
    endpoint.add_argument("--json", action="store_true", help="Output as JSON")
    endpoint_subparsers = endpoint.add_subparsers(dest="endpoint_command", required=True)

    # List all endpoints
    endpoint_subparsers.add_parser("list", help="List all monitored endpoints")

    # Add endpoint
    add = endpoint_subparsers.add_parser("add", help="Add an endpoint to monitor")
    add.add_argument("url", help="Endpoint URL to monitor")
    add.add_argument("--type", choices=["cloud", "local"], default="cloud", help="Endpoint type")
    add.add_argument("--environment", default="default", help="Environment (default, local, staging, production)")
    add.add_argument("--timeout", type=float, help="Override timeout in seconds")
    add.add_argument("--json", action="store_true", help="Output as JSON")

    # Remove endpoint
    remove = endpoint_subparsers.add_parser("remove", help="Remove an endpoint from monitoring")
    remove.add_argument("url", help="Endpoint URL to remove")
    remove.add_argument("--json", action="store_true", help="Output as JSON")

    # Check endpoint health
    check = endpoint_subparsers.add_parser("check", help="Check health of specific endpoint")
    check.add_argument("url", help="Endpoint URL to check")
    check.add_argument("--json", action="store_true", help="Output as JSON")

    # Get health report
    report = endpoint_subparsers.add_parser("report", help="Get health report for all endpoints")
    report.add_argument("--json", action="store_true", help="Output as JSON")
    report.add_argument("--environment", default="local", help="Environment to check")
    report.add_argument("--output", type=Path, help="Output report to JSON file")

    # Start monitoring
    start = endpoint_subparsers.add_parser("start", help="Start endpoint health monitoring")
    start.add_argument("--interval", type=int, default=60, help="Check interval in seconds")
    start.add_argument("--json", action="store_true", help="Output as JSON")

    # Stop monitoring
    stop = endpoint_subparsers.add_parser("stop", help="Stop endpoint health monitoring")
    stop.add_argument("--json", action="store_true", help="Output as JSON")

    # Connector management subcommands
    connector = subparsers.add_parser("connectors", help="Manage connector configurations")
    connector.add_argument("--json", action="store_true", help="Output as JSON")
    connector_subparsers = connector.add_subparsers(dest="connector_command", required=True)

    # List all connectors
    connector_subparsers.add_parser("list", help="List all connector manifests")

    # Get connector info
    get = connector_subparsers.add_parser("get", help="Get detailed information about a connector")
    get.add_argument("uid", help="Connector UID")
    get.add_argument("--json", action="store_true", help="Output as JSON")

    # Add connector manifest
    add = connector_subparsers.add_parser("add", help="Add a new connector manifest")
    add.add_argument("uid", help="Connector UID")
    add.add_argument("display_name", help="Display name")
    add.add_argument("version", help="Version (semver format)")
    add.add_argument("description", help="Connector description")
    add.add_argument("--base-url", help="Base URL for the connector")
    add.add_argument("--auth-type", choices=["api_key", "bearer", "oauth2"], help="Authentication type")
    add.add_argument("--scopes", nargs="+", help="Required scopes")
    add.add_argument("--risk-class", choices=["read", "write", "sensitive", "critical"], default="read", help="Risk classification")
    add.add_argument("--operation", action="append", nargs=2, metavar=("NAME", "METHOD"), help="Add an operation (can be used multiple times)")
    add.add_argument("--dependency", action="append", help="Add a dependency (can be used multiple times)")
    add.add_argument("--owner-id", default="local", help="Owner ID")
    add.add_argument("--task-id", help="Task ID")
    add.add_argument("--json", action="store_true", help="Output as JSON")

    # Update connector status
    update = connector_subparsers.add_parser("update", help="Update connector status")
    update.add_argument("uid", help="Connector UID")
    update.add_argument("status", choices=["configuration_required", "operational", "degraded", "unavailable", "error"], help="New status")
    update.add_argument("--json", action="store_true", help="Output as JSON")

    # Remove connector
    remove = connector_subparsers.add_parser("remove", help="Remove a connector manifest")
    remove.add_argument("uid", help="Connector UID")
    remove.add_argument("--json", action="store_true", help="Output as JSON")

    # Validate configuration
    validate = connector_subparsers.add_parser("validate", help="Validate connector configuration")
    validate.add_argument("--json", action="store_true", help="Output as JSON")

    # Show version info
    version = connector_subparsers.add_parser("version", help="Show version information for all connectors")
    version.add_argument("--json", action="store_true", help="Output as JSON")

    # Show dependencies
    deps = connector_subparsers.add_parser("dependencies", help="Show connector dependencies")
    deps.add_argument("uid", help="Connector UID")
    deps.add_argument("--json", action="store_true", help="Output as JSON")

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
    if args.command == "show":
        checkpoint = store.load(args.run_id)
        print(json.dumps(checkpoint.to_dict(), indent=2, ensure_ascii=False))
        return 0

    # Endpoint management commands
    if args.command == "endpoints":
        config_path = Path(args.database).parent / "endpoint-monitor.db"
        monitor = EndpointMonitor(EndpointMonitorConfig(database_path=config_path))

        if args.endpoint_command == "list":
            healths = monitor.get_all_health()
            if args.json:
                print(json.dumps([h.to_dict() for h in healths.values()], indent=2))
            else:
                print(f"Found {len(healths)} endpoint(s):")
                for url, health in healths.items():
                    print(f"  - {url}")
                    print(f"    Status: {health.status.value}")
                    print(f"    Last probed: {health.last_probed.isoformat()}")
                    print(f"    Consecutive failures: {health.consecutive_failures}")
                    print(f"    Consecutive successes: {health.consecutive_successes}")
                    print()

        elif args.endpoint_command == "add":
            try:
                if args.type == "cloud":
                    spec = ProviderEndpointSpec(
                        provider_id="cli-added",
                        display_name="CLI Added Endpoint",
                        provider_type="cloud",
                        endpoint_url=args.url,
                        model_identifier="model",
                        protocol="openai",
                        environment=args.environment,
                    )
                    if args.timeout:
                        spec = spec._replace(timeout_seconds=args.timeout)
                    monitor.add_endpoint(args.url)
                else:
                    spec = LocalModelSpec(
                        model_id="cli-added",
                        source_path=Path(args.url),
                        checksum_sha256="a" * 64,  # Placeholder
                        file_format="gguf",
                        environment=args.environment,
                    )
                    if args.timeout:
                        spec = spec._replace(timeout_seconds=args.timeout)
                    monitor.add_endpoint(args.url)

                if args.json:
                    print(json.dumps({"status": "success", "url": args.url, "type": args.type}))
                else:
                    print(f"Successfully added endpoint: {args.url}")

            except Exception as exc:
                print(json.dumps({"status": "error", "error": str(exc)}), file=sys.stderr)
                return 1

        elif args.endpoint_command == "remove":
            if not monitor.remove_endpoint(args.url):
                print(json.dumps({"error": f"Endpoint '{args.url}' not found"}), file=sys.stderr)
                return 1

            if args.json:
                print(json.dumps({"status": "success", "url": args.url}))
            else:
                print(f"Successfully removed endpoint: {args.url}")

        elif args.endpoint_command == "check":
            health = monitor.get_endpoint_health(args.url)
            if not health:
                print(json.dumps({"error": f"Endpoint '{args.url}' not found"}), file=sys.stderr)
                return 1

            if args.json:
                print(json.dumps(health.to_dict(), indent=2))
            else:
                print(f"Endpoint: {args.url}")
                print(f"Status: {health.status.value}")
                print(f"Last probed: {health.last_probed.isoformat()}")
                print(f"Consecutive failures: {health.consecutive_failures}")
                print(f"Consecutive successes: {health.consecutive_successes}")
                print(f"Average response time: {health.average_response_time_ms:.2f}ms")
                print(f"Probe count: {health.probe_count}")
                if health.last_error:
                    print(f"Last error: {health.last_error}")

        elif args.endpoint_command == "report":
            # Create a monitor for the specified environment
            env_monitor = EndpointHealthMonitor(environment=args.environment)
            report = env_monitor.get_report()

            if args.output:
                report.to_file(args.output)
                print(f"Report saved to: {args.output}")
            elif args.json:
                print(json.dumps(report.to_dict(), indent=2))
            else:
                summary = report.get_summary()
                print(f"Environment: {summary['environment']}")
                print(f"Overall status: {summary['overall_status']}")
                print(f"Total endpoints: {summary['summary']['total']}")
                print(f"Healthy: {summary['summary']['healthy']}")
                print(f"Degraded: {summary['summary']['degraded']}")
                print(f"Unhealthy: {summary['summary']['unhealthy']}")
                print(f"Unknown: {summary['summary']['unknown']}")
                print("\nDetails:")
                for detail in summary['details']:
                    print(f"  - {detail['url']}: {detail['status']}")
                    print(f"    Failures: {detail['consecutive_failures']}, Successes: {detail['consecutive_successes']}")
                    print(f"    Response time: {detail['average_response_time_ms']:.2f}ms")

        elif args.endpoint_command == "start":
            monitor._monitor.start_monitoring()
            if args.json:
                print(json.dumps({"status": "success", "message": "Monitoring started"}))
            else:
                print("Endpoint health monitoring started")

        elif args.endpoint_command == "stop":
            monitor._monitor.stop_monitoring()
            if args.json:
                print(json.dumps({"status": "success", "message": "Monitoring stopped"}))
            else:
                print("Endpoint health monitoring stopped")

        return 0

    # Connector management commands
    if args.command == "connectors":
        config_path = Path(args.database).parent / "connector-config.json"
        manager = ConnectorConfigManager(config_path)

        if args.connector_command == "list":
            manifests = manager.list_manifests()
            if args.json:
                print(json.dumps([m.to_dict() for m in manifests], indent=2))
            else:
                print(f"Found {len(manifests)} connector(s):")
                for manifest in manifests:
                    print(f"  - {manifest.display_name} ({manifest.uid}) v{manifest.version}")
                    print(f"    Status: {manifest.status.value}")
                    print(f"    Operations: {len(manifest.operations)}")
                    print(f"    Dependencies: {len(manifest.dependencies)}")
                    print()

        elif args.connector_command == "get":
            manifest = manager.get_manifest(args.uid)
            if not manifest:
                print(json.dumps({"error": f"Connector '{args.uid}' not found"}), file=sys.stderr)
                return 1
            if args.json:
                print(json.dumps(manifest.to_dict(), indent=2))
            else:
                print(f"Connector: {manifest.display_name} ({manifest.uid})")
                print(f"Version: {manifest.version}")
                print(f"Status: {manifest.status.value}")
                print(f"Description: {manifest.description}")
                if manifest.base_url:
                    print(f"Base URL: {manifest.base_url}")
                if manifest.auth_type:
                    print(f"Auth Type: {manifest.auth_type.value}")
                if manifest.scopes:
                    print(f"Scopes: {', '.join(manifest.scopes)}")
                print(f"Operations: {len(manifest.operations)}")
                for op in manifest.operations:
                    print(f"  - {op.name} ({op.method}) - {op.description}")
                if manifest.dependencies:
                    print(f"Dependencies: {', '.join(manifest.dependencies)}")
                print(f"Risk Class: {manifest.risk_class.value}")
                print(f"Owner: {manifest.owner_id}")
                if manifest.task_id:
                    print(f"Task: {manifest.task_id}")

        elif args.connector_command == "add":
            operations = []
            for name, method in args.operation or []:
                operations.append(ConnectorOperation(
                    name=name,
                    method=method,
                    description=f"{method} operation for {name}",
                ))

            manifest = ConnectorManifest(
                uid=args.uid,
                display_name=args.display_name,
                version=args.version,
                description=args.description,
                base_url=args.base_url,
                auth_type=ConnectorAuthType(args.auth_type) if args.auth_type else None,
                scopes=args.scopes or [],
                operations=operations,
                dependencies=args.dependency or [],
                risk_class=ConnectorRiskClass(args.risk_class),
                owner_id=args.owner_id,
                task_id=args.task_id,
            )

            errors = manager.add_manifest(manifest)
            if errors:
                print(json.dumps({"error": "Failed to add connector", "details": errors}), file=sys.stderr)
                return 1

            if args.json:
                print(json.dumps({"status": "success", "manifest": manifest.to_dict()}))
            else:
                print(f"Successfully added connector: {manifest.display_name} ({manifest.uid})")

        elif args.connector_command == "update":
            if not manager.update_status(args.uid, ConnectorStatus(args.status)):
                print(json.dumps({"error": f"Connector '{args.uid}' not found"}), file=sys.stderr)
                return 1

            if args.json:
                print(json.dumps({"status": "success", "uid": args.uid, "connector_status": args.status}))
            else:
                print(f"Successfully updated connector '{args.uid}' to status: {args.status}")

        elif args.connector_command == "remove":
            if not manager.remove_manifest(args.uid):
                print(json.dumps({"error": f"Connector '{args.uid}' not found"}), file=sys.stderr)
                return 1

            if args.json:
                print(json.dumps({"status": "success", "uid": args.uid}))
            else:
                print(f"Successfully removed connector: {args.uid}")

        elif args.connector_command == "validate":
            errors = manager.validate_all()
            if errors:
                print(json.dumps({"status": "invalid", "errors": errors}), file=sys.stderr)
                return 1
            else:
                print(json.dumps({"status": "valid", "message": "All connectors are valid"}))

        elif args.connector_command == "version":
            infos = manager.get_all_version_info()
            if args.json:
                print(json.dumps(infos, indent=2))
            else:
                print(f"Version information for {len(infos)} connector(s):")
                for info in infos:
                    print(f"  - {info['display_name']} ({info['uid']}) v{info['version']}")
                    print(f"    Status: {info['status']}")
                    print(f"    Operations: {info['operation_count']}")
                    print(f"    Dependencies: {info['dependency_count']}")
                    print()

        elif args.connector_command == "dependencies":
            deps = manager.get_dependencies(args.uid)
            if not deps:
                print(json.dumps({"error": f"Connector '{args.uid}' not found or has no dependencies"}), file=sys.stderr)
                return 1

            if args.json:
                print(json.dumps([d.to_dict() for d in deps], indent=2))
            else:
                print(f"Dependencies for {args.uid}:")
                for dep in deps:
                    print(f"  - {dep.display_name} ({dep.uid}) v{dep.version}")
                    print(f"    Status: {dep.status.value}")
                    print()

        return 0


if __name__ == "__main__":
    raise SystemExit(main())
