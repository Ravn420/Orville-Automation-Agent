"""Run reproducible local build, test, and preview checks for Orville."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    """Run one check from the repository root and stream its output."""
    print("$", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def build() -> None:
    """Compile Python sources and build a disposable wheel."""
    run([sys.executable, "-m", "compileall", "-q", "orville_core", "tools", "windows_gui.py"])
    wheel_dir = ROOT / "tmp" / "project-check-wheels"
    wheel_dir.mkdir(parents=True, exist_ok=True)
    run([sys.executable, "-m", "pip", "wheel", ".", "--no-deps", "--wheel-dir", str(wheel_dir)])
    wheels = sorted(wheel_dir.glob("*.whl"))
    if not wheels:
        raise RuntimeError(f"wheel build produced no artifact under {wheel_dir}")
    print(f"PASS: build produced {wheels[-1].name}")


def test() -> None:
    """Run the regression suite and require failed-test triage before release."""
    run([sys.executable, "-m", "pytest", "-q"])
    triage_manifest = ROOT / "config" / "test_triage_manifest.json"
    if not triage_manifest.is_file():
        raise FileNotFoundError(f"required test-triage manifest is missing: {triage_manifest}")
    run([sys.executable, "tools/test_triage.py", str(triage_manifest)])
    print("PASS: regression tests and failed-test triage")


def preview(api_smoke: bool = False) -> None:
    """Run local UI checks, optionally followed by the authenticated API smoke test."""
    run([sys.executable, "tools/signal_room_checks.py", "webui"])
    if api_smoke:
        script = ROOT / "test-preview-workflows.ps1"
        if not script.is_file():
            raise FileNotFoundError(script)
        if not (ROOT / ".env.production").is_file():
            raise RuntimeError("API preview smoke requires local .env.production; no credential was requested or generated")
        run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)])
    print("PASS: preview checks")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("check", choices=("build", "test", "preview", "all"))
    parser.add_argument("--api-smoke", action="store_true", help="include the local authenticated API preview smoke test")
    args = parser.parse_args(argv)
    if args.api_smoke and args.check not in {"preview", "all"}:
        parser.error("--api-smoke is only valid with preview or all")
    if args.check in {"build", "all"}:
        build()
    if args.check in {"test", "all"}:
        test()
    if args.check in {"preview", "all"}:
        preview(api_smoke=args.api_smoke)
    print(f"PASS: project check '{args.check}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
