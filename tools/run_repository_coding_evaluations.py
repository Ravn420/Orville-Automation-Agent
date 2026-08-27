#!/usr/bin/env python3
"""Run deterministic, offline repository-level coding evaluations."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config" / "repository-coding-evaluations.json"


def _safe_repo_path(relative_path: str) -> Path:
    candidate = (ROOT / relative_path).resolve()
    if not candidate.is_relative_to(ROOT):
        raise ValueError(f"manifest path escapes repository: {relative_path}")
    return candidate


def _redact(value: str, workspace: Path) -> str:
    return value.replace(str(workspace), "<temp-workspace>")


def _run(command: list[str], cwd: Path, env: dict[str, str], timeout: int = 60) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return {"command": command, "returncode": None, "timed_out": True, "stdout": stdout, "stderr": stderr}
    return {
        "command": command,
        "returncode": completed.returncode,
        "timed_out": False,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _assert_local_command(command: list[str]) -> None:
    if not command or command[0] not in {"python", "python3"}:
        raise ValueError(f"only Python fixture commands are permitted: {command}")
    if any(token in {"-c", "-m", "shell=True"} for token in command[1:]):
        # -m is required for unittest/compileall, while -c would allow arbitrary inline code.
        if "-c" in command[1:]:
            raise ValueError(f"inline Python is not permitted in fixture command: {command}")


def _run_case(case: dict[str, Any]) -> dict[str, Any]:
    fixture = _safe_repo_path(str(case["fixture_path"]))
    patch = fixture / str(case["patch_path"])
    requirements = fixture / str(case["dependency_manifest"])
    if not fixture.is_dir() or not patch.is_file() or not requirements.is_file():
        raise FileNotFoundError(f"incomplete fixture for {case['id']}")

    commands = [case["focused_test_command"], case["compile_command"], case["regression_command"]]
    for command in commands:
        _assert_local_command([str(token) for token in command])

    with tempfile.TemporaryDirectory(prefix="orville-coding-eval-") as temporary:
        workspace = Path(temporary) / case["id"]
        shutil.copytree(fixture, workspace)
        dependency_target = workspace / ".dependencies"
        dependency_target.mkdir()
        env = dict(os.environ)
        env["PYTHONPATH"] = f"{dependency_target}{os.pathsep}{workspace}"
        env["PYTHONHASHSEED"] = "0"

        # The requirements file is copied under a stable, non-secret name so paths are never emitted.
        (workspace / "stripped-requirements.txt").write_text(requirements.read_text(encoding="utf-8"), encoding="utf-8")
        install = _run(
            ["python3", "-m", "pip", "install", "--no-index", "--disable-pip-version-check", "--no-deps", "--requirement", "stripped-requirements.txt", "--target", str(dependency_target)],
            workspace,
            env,
        )
        baseline = _run([str(token) for token in case["focused_test_command"]], workspace, env)
        patch_check = _run(["patch", "--dry-run", "-p1", "--input", str(patch)], workspace, env)
        if patch_check["returncode"] == 0:
            apply_patch = _run(["patch", "-p1", "--input", str(patch)], workspace, env)
        else:
            apply_patch = {"command": ["patch", "-p1"], "returncode": patch_check["returncode"], "timed_out": False, "stdout": "", "stderr": "patch dry-run failed"}
        focused = _run([str(token) for token in case["focused_test_command"]], workspace, env) if apply_patch["returncode"] == 0 else None
        compiled = _run([str(token) for token in case["compile_command"]], workspace, env) if apply_patch["returncode"] == 0 else None
        regression = _run([str(token) for token in case["regression_command"]], workspace, env) if apply_patch["returncode"] == 0 else None

        records = {"install": install, "baseline": baseline, "patch_check": patch_check, "apply_patch": apply_patch, "focused": focused, "compile": compiled, "regression": regression}
        for record in records.values():
            if record is not None:
                record["stdout"] = _redact(record["stdout"], workspace)
                record["stderr"] = _redact(record["stderr"], workspace)
        passed = (
            install["returncode"] == 0
            and baseline["returncode"] not in (0, None)
            and not baseline["timed_out"]
            and patch_check["returncode"] == 0
            and apply_patch["returncode"] == 0
            and focused is not None and focused["returncode"] == 0
            and compiled is not None and compiled["returncode"] == 0
            and regression is not None and regression["returncode"] == 0
        )
        return {"id": case["id"], "title": case["title"], "passed": passed, "acceptance": case["acceptance"], "steps": records}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", action="append", dest="case_ids", help="run only the named case; repeat for multiple cases")
    parser.add_argument("--json-out", type=Path, help="write the redacted result JSON to this path")
    args = parser.parse_args()
    registry = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cases = registry["cases"]
    selected = [case for case in cases if not args.case_ids or case["id"] in args.case_ids]
    if args.case_ids and len(selected) != len(set(args.case_ids)):
        missing = sorted(set(args.case_ids) - {case["id"] for case in selected})
        parser.error(f"unknown case ID(s): {', '.join(missing)}")
    results = [_run_case(case) for case in selected]
    payload = {"registry_id": registry["registry_id"], "version": registry["version"], "passed": all(result["passed"] for result in results), "cases": results}
    rendered = json.dumps(payload, indent=2, sort_keys=True)
    if args.json_out:
        output = _safe_repo_path(str(args.json_out)) if not args.json_out.is_absolute() else args.json_out.resolve()
        if not output.is_relative_to(ROOT):
            raise ValueError("result path must remain inside the repository")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
