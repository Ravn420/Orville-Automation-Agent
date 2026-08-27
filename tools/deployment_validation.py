from __future__ import annotations

import argparse
import json
import socket
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


TARGET_REQUIREMENTS = {
    "sandbox": ("pyproject.toml", "tools/project_checks.py"),
    "web-hosting": ("docker-compose.yml", "deploy/Caddyfile"),
    "attached-desktop": ("build-release.ps1", "install-orville.ps1"),
    "persistent-computing": ("docker-compose.yml", "Dockerfile"),
}


def preflight(target: str, root: Path) -> tuple[str, ...]:
    """Validate target prerequisites without loading credentials or deploying."""
    if target not in TARGET_REQUIREMENTS:
        raise ValueError(f"unsupported deployment target: {target}")
    missing = tuple(path for path in TARGET_REQUIREMENTS[target] if not (root / path).is_file())
    if missing:
        raise FileNotFoundError(f"missing {target} prerequisites: {', '.join(missing)}")
    return TARGET_REQUIREMENTS[target]


def smoke(url: str, *, path: str = "/docs", timeout: float = 5.0, allow_remote: bool = False) -> dict[str, object]:
    """Perform a bounded credential-free HTTP health check and return safe evidence."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("smoke URL must be an HTTP(S) URL with a host")
    if not allow_remote and parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("remote smoke checks require explicit --allow-remote")
    if not path.startswith("/") or "?" in path or "#" in path:
        raise ValueError("smoke path must be an absolute path without query or fragment")
    endpoint = url.rstrip("/") + path
    request = urllib.request.Request(endpoint, method="GET", headers={"Accept": "text/html, application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = int(response.status)
            response.read(256)
    except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
        raise RuntimeError(f"smoke check could not reach endpoint: {type(exc).__name__}") from exc
    if not 200 <= status < 400:
        raise RuntimeError(f"smoke check returned HTTP {status}")
    return {"status": "healthy", "http_status": status, "path": path}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run credential-free deployment validation")
    subparsers = parser.add_subparsers(dest="command", required=True)
    preflight_parser = subparsers.add_parser("preflight")
    preflight_parser.add_argument("--target", choices=sorted(TARGET_REQUIREMENTS), required=True)
    preflight_parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    smoke_parser = subparsers.add_parser("smoke")
    smoke_parser.add_argument("--url", required=True)
    smoke_parser.add_argument("--path", default="/docs")
    smoke_parser.add_argument("--timeout", type=float, default=5.0)
    smoke_parser.add_argument("--allow-remote", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "preflight":
        print(json.dumps({"status": "ready", "target": args.target, "requirements": preflight(args.target, args.root)}))
    else:
        print(json.dumps(smoke(args.url, path=args.path, timeout=args.timeout, allow_remote=args.allow_remote), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
