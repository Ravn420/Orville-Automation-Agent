"""Platform adapters for Orville's process-level model sandbox contract."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from xml.sax.saxutils import escape as xml_escape
from pathlib import Path
from typing import Any

from .sandbox import SandboxExecutor, SandboxPlan, SandboxResult, SandboxUnavailable, filtered_environment


class LinuxBubblewrapExecutor:
    """Run an argv inside bubblewrap with read-only model input and no network by default."""

    def __init__(self, executable: str | None = None) -> None:
        self.executable = executable or shutil.which("bwrap") or shutil.which("bubblewrap")

    def available(self) -> bool:
        return bool(self.executable) and os.name != "nt"

    def build_argv(self, plan: SandboxPlan) -> list[str]:
        plan.validate()
        if not self.available():
            raise SandboxUnavailable("bubblewrap is unavailable on this host")
        plan.model_path.parent.mkdir(parents=True, exist_ok=True)
        plan.scratch_path.mkdir(parents=True, exist_ok=True)
        plan.output_path.mkdir(parents=True, exist_ok=True)
        argv = [self.executable, "--die-with-parent", "--new-session", "--clearenv", "--ro-bind", str(plan.model_path), "/model", "--bind", str(plan.scratch_path), "/scratch", "--bind", str(plan.output_path), "/output", "--proc", "/proc", "--dev", "/dev", "--chdir", "/scratch"]
        if not plan.policy.network:
            argv.append("--unshare-net")
        if not plan.policy.allow_gpu:
            argv.extend(("--tmpfs", "/run"))
        for key, value in filtered_environment(plan).items():
            argv.extend(("--setenv", key, value))
        argv.append("--")
        argv.extend(plan.command)
        return argv

    def run(self, plan: SandboxPlan) -> SandboxResult:
        argv = self.build_argv(plan)
        try:
            completed = subprocess.run(argv, cwd=str(plan.scratch_path), env={}, capture_output=True, text=True, timeout=plan.policy.timeout_seconds, check=False)
        except subprocess.TimeoutExpired as exc:
            return SandboxResult(plan.run_id, "timeout", diagnostics=({"code": "sandbox_timeout", "message": "sandbox worker exceeded its timeout", "severity": "error"},), stdout=str(exc.stdout or "")[: plan.policy.max_output_bytes], stderr=str(exc.stderr or "")[: plan.policy.max_output_bytes])
        except OSError as exc:
            return SandboxResult(plan.run_id, "failed", diagnostics=({"code": "sandbox_launch_failed", "message": str(exc), "severity": "error"},))
        return SandboxResult(plan.run_id, "completed" if completed.returncode == 0 else "failed", completed.returncode, completed.stdout[: plan.policy.max_output_bytes], completed.stderr[: plan.policy.max_output_bytes])

    def terminate(self, run_id: str) -> None:
        return None


class WindowsSandboxExecutor:
    """Generate and launch a minimal Windows Sandbox configuration when supported."""

    def __init__(self, executable: str | None = None) -> None:
        self.executable = executable or shutil.which("WindowsSandbox.exe")

    def available(self) -> bool:
        return bool(self.executable) and os.name == "nt"

    def build_config(self, plan: SandboxPlan, destination: Path) -> Path:
        plan.validate()
        destination = destination.expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        plan.scratch_path.mkdir(parents=True, exist_ok=True)
        plan.output_path.mkdir(parents=True, exist_ok=True)
        command = xml_escape(subprocess.list2cmdline(list(plan.command)))
        xml = f"""<Configuration>\n  <vGPU>{'Enable' if plan.policy.allow_gpu else 'Disable'}</vGPU>\n  <Networking>{'Enable' if plan.policy.network else 'Disable'}</Networking>\n  <ProtectedClient>Enable</ProtectedClient>\n  <MemoryInMB>{max(2048, plan.policy.max_memory_bytes // (1024 * 1024))}</MemoryInMB>\n  <MappedFolders>\n    <MappedFolder><HostFolder>{plan.model_path}</HostFolder><SandboxFolder>C:\\model</SandboxFolder><ReadOnly>true</ReadOnly></MappedFolder>\n    <MappedFolder><HostFolder>{plan.scratch_path}</HostFolder><SandboxFolder>C:\\scratch</SandboxFolder><ReadOnly>false</ReadOnly></MappedFolder>\n    <MappedFolder><HostFolder>{plan.output_path}</HostFolder><SandboxFolder>C:\\output</SandboxFolder><ReadOnly>false</ReadOnly></MappedFolder>\n  </MappedFolders>\n  <LogonCommand><Command>{command}</Command></LogonCommand>\n</Configuration>\n"""
        destination.write_text(xml, encoding="utf-8")
        return destination

    def run(self, plan: SandboxPlan) -> SandboxResult:
        if not self.available():
            raise SandboxUnavailable("Windows Sandbox is unavailable or not enabled on this host")
        with tempfile.TemporaryDirectory(prefix="orville-sandbox-") as temporary:
            config = self.build_config(plan, Path(temporary) / f"{plan.run_id}.wsb")
            try:
                completed = subprocess.run([self.executable, str(config)], capture_output=True, text=True, timeout=plan.policy.timeout_seconds, check=False)
            except subprocess.TimeoutExpired:
                return SandboxResult(plan.run_id, "timeout", diagnostics=({"code": "sandbox_timeout", "message": "Windows Sandbox exceeded its timeout", "severity": "error"},))
            except OSError as exc:
                return SandboxResult(plan.run_id, "failed", diagnostics=({"code": "sandbox_launch_failed", "message": str(exc), "severity": "error"},))
            return SandboxResult(plan.run_id, "completed" if completed.returncode == 0 else "failed", completed.returncode, completed.stdout[: plan.policy.max_output_bytes], completed.stderr[: plan.policy.max_output_bytes])

    def run_with_guest_marker(self, plan: SandboxPlan, marker_name: str = "worker_result.json") -> SandboxResult:
        """Launch Sandbox and require a guest-written marker before success."""
        if not self.available():
            raise SandboxUnavailable("Windows Sandbox is unavailable or not enabled on this host")
        marker = plan.output_path / marker_name
        if marker.exists():
            marker.unlink()
        result = self.run(plan)
        if result.status != "completed":
            return result
        deadline = __import__("time").monotonic() + plan.policy.timeout_seconds
        while __import__("time").monotonic() < deadline:
            if marker.is_file():
                try:
                    payload = json.loads(marker.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                    return SandboxResult(plan.run_id, "failed", result.exit_code, result.stdout, result.stderr, ({"code": "worker_marker_invalid", "message": str(exc), "severity": "error"},))
                if payload.get("run_id") not in {None, plan.run_id}:
                    return SandboxResult(plan.run_id, "failed", result.exit_code, result.stdout, result.stderr, ({"code": "worker_marker_mismatch", "severity": "error"},))
                return SandboxResult(plan.run_id, "completed", result.exit_code, result.stdout, result.stderr, result.diagnostics, {"guest_marker": payload})
            __import__("time").sleep(0.1)
        return SandboxResult(plan.run_id, "failed", result.exit_code, result.stdout, result.stderr, ({"code": "worker_marker_missing", "message": "Sandbox launcher exited without a guest completion marker", "severity": "error"},))

    def terminate(self, run_id: str) -> None:
        return None


def discover_sandbox_adapters() -> dict[str, SandboxExecutor]:
    """Return platform adapters without launching any process."""

    return {"linux_bubblewrap": LinuxBubblewrapExecutor(), "windows_sandbox": WindowsSandboxExecutor()}
