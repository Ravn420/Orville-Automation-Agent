"""Run Orville's local release gates without requiring Manus services."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from orville_core.security_release_gate import run_security_gate


def run(command: list[str], root: Path) -> None:
    print("$", " ".join(command))
    subprocess.run(command, cwd=root, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--sandbox-available", action="store_true", help="assert that a live sandbox boundary test passed")
    parser.add_argument("--required-attestation-verified", action="store_true", help="assert that required attestation verification passed")
    parser.add_argument("--audit-evidence-present", action="store_true", help="assert that sanitized audit evidence is present")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    run([sys.executable, "-m", "compileall", "-q", "orville_core", "windows_gui.py"], root)
    security = run_security_gate(root=root, sandbox_available=args.sandbox_available, required_attestation_verified=args.required_attestation_verified, audit_evidence_present=args.audit_evidence_present)
    if not security.passed:
        for diagnostic in security.diagnostics:
            print("SECURITY GATE:", diagnostic["code"], diagnostic["message"])
        return 2
    print("security gates passed:", ", ".join(name for name, passed in security.checks.items() if passed))
    if not args.skip_tests:
        run([sys.executable, "-m", "pytest", "-q"], root)
    run([sys.executable, "-m", "pip", "wheel", ".", "--no-deps", "--wheel-dir", str(root / "tmp" / "release-wheels")], root)
    print("release gates passed: compilation, regression tests, and wheel build")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
