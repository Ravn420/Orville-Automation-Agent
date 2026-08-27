from pathlib import Path

import pytest

from orville_core.local_execution import LocalModelExecutionError, LocalModelExecutionService
from orville_core.local_models import LocalModelCatalog
from orville_core.sandbox import SandboxPlan, SandboxPolicy, SandboxResult
from orville_core.sandbox_adapters import WindowsSandboxExecutor
from orville_core.worker_protocol import WorkerRequest, decode_message, encode_message


class FakeExecutor:
    def __init__(self, available=True):
        self._available = available
        self.plans = []

    def available(self):
        return self._available

    def run(self, plan):
        self.plans.append(plan)
        return SandboxResult(plan.run_id, "completed", 0, stdout="ok")

    def terminate(self, run_id):
        return None


def test_worker_protocol_round_trip_and_limits():
    request = WorkerRequest("r1", "infer", "m1", "sha256:x", "policy-1", "/model", "/output")
    assert WorkerRequest.from_dict(decode_message(encode_message(request.to_dict()))) == request
    with pytest.raises(ValueError):
        WorkerRequest.from_dict({**request.to_dict(), "protocol_version": 99})


def test_execute_local_model_requires_active_verified_catalog(tmp_path: Path):
    asset = tmp_path / "model.gguf"
    asset.write_bytes(b"model")
    catalog = LocalModelCatalog(tmp_path / "models.json")
    record = catalog.import_model(asset, model_id="m1", runtime="ollama", endpoint="http://127.0.0.1:11434")
    with pytest.raises(LocalModelExecutionError):
        LocalModelExecutionService(catalog, {"fake": FakeExecutor()}).execute_local_model("m1", command=("worker",), adapter="fake")
    record.status = "active"
    record.activation_evidence = {"verification_status": "verified"}
    catalog._write([record])
    result = LocalModelExecutionService(catalog, {"fake": FakeExecutor()}).execute_local_model("m1", command=("worker",), adapter="fake")
    assert result.status == "completed"


def test_windows_guest_marker_config_is_fail_closed(tmp_path: Path):
    executor = WindowsSandboxExecutor(executable="WindowsSandbox.exe")
    assert "<LogonCommand>" in executor.build_config(
        SandboxPlan("r1", ("cmd.exe", "/c", "worker.cmd"), tmp_path / "model", tmp_path / "scratch", tmp_path / "output", SandboxPolicy(), "sha256:x"), tmp_path / "r1.wsb"
    ).read_text(encoding="utf-8")
