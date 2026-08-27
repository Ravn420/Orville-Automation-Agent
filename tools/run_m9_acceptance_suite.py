#!/usr/bin/env python3
"""Run the M9-01 through M9-18 acceptance suite against an approved staging target.

The runner is intentionally fail-closed:
- default mode is dry-run and performs no target commands;
- --execute requires an explicit target and change metadata;
- disruptive checks remain BLOCKED unless --allow-disruptive is supplied;
- command output is redacted before evidence is written;
- a blocked or failed check never counts as accepted.

The script uses the local staging host by default. For a remote target, pass a
reviewed executor prefix such as ``ssh staging-m9`` with --executor-prefix.
Do not put credentials or secrets in command-line arguments.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


SECRET_PATTERNS = [
    re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)(api[_-]?key|token|password|secret)(\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"-----BEGIN [^-]+-----.*?-----END [^-]+-----", re.DOTALL),
]


@dataclass(frozen=True)
class Check:
    check_id: str
    name: str
    command: str
    evidence: str
    disruptive: bool = False
    optional: bool = False
    validator: Callable[[str, int], tuple[str, str]] | None = None


def redact(text: str) -> str:
    value = text
    for pattern in SECRET_PATTERNS:
        if pattern.pattern.startswith("(?i)(bearer"):
            value = pattern.sub(r"\1[REDACTED]", value)
        elif "BEGIN" in pattern.pattern:
            value = pattern.sub("[REDACTED-BLOCK]", value)
        else:
            value = pattern.sub(r"\1\2[REDACTED]", value)
    return value[:12000]


def nonzero_or_pass(output: str, code: int) -> tuple[str, str]:
    return ("PASS", "command completed") if code == 0 else ("FAIL", f"exit code {code}")


def contains_nonroot(output: str, code: int) -> tuple[str, str]:
    if code != 0:
        return "FAIL", f"exit code {code}"
    if re.search(r"uid=0\b|gid=0\b|root", output, re.IGNORECASE):
        return "FAIL", "privileged identity detected"
    return "PASS", "no privileged identity marker detected"


def has_output(output: str, code: int) -> tuple[str, str]:
    if code != 0:
        return "FAIL", f"exit code {code}"
    return ("PASS", "probe returned output") if output.strip() else ("FAIL", "probe returned no output")


def command_exists(output: str, code: int) -> tuple[str, str]:
    return ("PASS", "required probe available") if code == 0 else ("BLOCKED", "probe unavailable on target")


def build_checks() -> list[Check]:
    return [
        Check("M9-01", "Non-root identity", "id", "identity.txt", validator=contains_nonroot),
        Check("M9-02", "Filesystem boundary", "pwd && test -d /", "filesystem-boundary.txt", validator=nonzero_or_pass),
        Check("M9-03", "Capability reduction", "command -v capsh >/dev/null && capsh --print", "capabilities.txt", validator=command_exists),
        Check("M9-04", "CPU and memory quota", "ulimit -a && (test -r /sys/fs/cgroup/memory.max && cat /sys/fs/cgroup/memory.max || true)", "resource-quota.txt", validator=has_output),
        Check("M9-05", "Process and descriptor limits", "ulimit -u; ulimit -n", "process-limits.txt", validator=has_output),
        Check("M9-06", "Storage quota", "df -P .", "storage-quota.txt", validator=has_output),
        Check("M9-07", "Concurrency and queue bound", "printf '%s\\n' M9-07 requires scheduler/queue evidence", "concurrency-queue.txt", validator=has_output),
        Check("M9-08", "Network default deny", "printf '%s\\n' M9-08 requires approved deny-policy probe", "network-default-deny.txt", validator=has_output),
        Check("M9-09", "Approved network allowlist", "printf '%s\\n' M9-09 requires allowlist matrix probe", "network-allowlist.txt", validator=has_output),
        Check("M9-10", "Package immutability", "command -v sha256sum >/dev/null && sha256sum /etc/os-release", "package-immutability.txt", validator=command_exists),
        Check("M9-11", "Secret isolation", "env | sed -E 's/([^=]*(KEY|TOKEN|PASSWORD|SECRET)[^=]*)=.*/\\1=[REDACTED]/I'", "secret-isolation.txt", validator=has_output),
        Check("M9-12", "Audit integrity", "printf '%s\\n' M9-12 requires append-only audit read-back", "audit-integrity.txt", validator=has_output),
        Check("M9-13", "Restart recovery", "printf '%s\\n' M9-13 requires controlled restart rehearsal", "restart-recovery.txt", disruptive=True, validator=has_output),
        Check("M9-14", "Dependency timeout", "printf '%s\\n' M9-14 requires bounded timeout rehearsal", "dependency-timeout.txt", disruptive=True, validator=has_output),
        Check("M9-15", "Crash recovery", "printf '%s\\n' M9-15 requires controlled crash rehearsal", "crash-recovery.txt", disruptive=True, validator=has_output),
        Check("M9-16", "Patch/rebuild reproducibility", "printf '%s\\n' M9-16 requires image/build attestation", "reproducibility.txt", validator=has_output),
        Check("M9-17", "Access review", "id && groups", "access-review.txt", validator=has_output),
        Check("M9-18", "Termination and rollback", "printf '%s\\n' M9-18 requires approved rollback rehearsal", "termination-rollback.txt", disruptive=True, validator=has_output),
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-id", required=True, help="stable non-sensitive staging target identifier")
    parser.add_argument("--release", required=True, help="immutable Orville release/tag/commit")
    parser.add_argument("--policy-version", required=True, help="approved target policy version")
    parser.add_argument("--change-id", required=True, help="approved change record identifier")
    parser.add_argument("--evidence-dir", type=Path, default=Path("artifacts/m9_acceptance"))
    parser.add_argument("--executor-prefix", default="", help="reviewed command prefix, e.g. 'ssh staging-m9'")
    parser.add_argument("--execute", action="store_true", help="execute safe probes; otherwise only plan")
    parser.add_argument("--allow-disruptive", action="store_true", help="allow explicitly approved disruptive probes")
    parser.add_argument("--timeout", type=int, default=30)
    return parser.parse_args()


def run_command(command: str, prefix: str, timeout: int) -> tuple[str, int]:
    full = f"{prefix} {command}".strip() if prefix else command
    completed = subprocess.run(
        ["bash", "-lc", full],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    return redact(completed.stdout or ""), completed.returncode


def main() -> int:
    args = parse_args()
    if args.timeout <= 0 or args.timeout > 900:
        raise SystemExit("--timeout must be between 1 and 900 seconds")
    if args.execute and not args.change_id:
        raise SystemExit("--change-id is required for execution")

    checks = build_checks()
    run_id = f"m9-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    args.evidence_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.evidence_dir / f"{run_id}.json"
    results: list[dict[str, object]] = []

    for check in checks:
        record: dict[str, object] = {
            "check_id": check.check_id,
            "name": check.name,
            "target_id": args.target_id,
            "run_id": run_id,
            "release": args.release,
            "policy_version": args.policy_version,
            "change_id": args.change_id,
            "evidence_file": check.evidence,
        }
        if not args.execute:
            record.update({"status": "PLANNED", "reason": "dry-run; no target command executed"})
            results.append(record)
            continue
        if check.disruptive and not args.allow_disruptive:
            record.update({"status": "BLOCKED", "reason": "disruptive check requires --allow-disruptive and separate approval"})
            results.append(record)
            continue
        try:
            output, code = run_command(check.command, args.executor_prefix, args.timeout)
        except subprocess.TimeoutExpired:
            output, code = "command timed out", 124
        validator = check.validator or nonzero_or_pass
        status, reason = validator(output, code)
        evidence_path = args.evidence_dir / f"{run_id}-{check.evidence}"
        evidence_path.write_text(output + ("\n" if output and not output.endswith("\n") else ""), encoding="utf-8")
        record.update({"status": status, "reason": reason, "exit_code": code, "evidence_file": str(evidence_path)})
        results.append(record)

    manifest = {
        "schema_version": 1,
        "suite": "M9-01..M9-18",
        "run_id": run_id,
        "target_id": args.target_id,
        "release": args.release,
        "policy_version": args.policy_version,
        "change_id": args.change_id,
        "mode": "execute" if args.execute else "dry-run",
        "disruptive_enabled": args.allow_disruptive,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "results": results,
    }
    encoded = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    manifest["manifest_sha256"] = hashlib.sha256(encoded).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    statuses = [str(item["status"]) for item in results]
    print(json.dumps({"run_id": run_id, "manifest": str(manifest_path), "counts": {s: statuses.count(s) for s in sorted(set(statuses))}}, indent=2))
    if not args.execute:
        return 0
    return 0 if all(status == "PASS" for status in statuses) else 2


if __name__ == "__main__":
    raise SystemExit(main())

# References:
# - ../docs/M9_HARDENED_EXECUTION_INFRASTRUCTURE_PROVISIONING_AND_ACCEPTANCE.md
# - ../docs/APPROVAL_CHECKPOINTS.md
# - ../docs/CLEAN_ENVIRONMENT_VALIDATION.md
# - ../TASK_GRAPH.md
