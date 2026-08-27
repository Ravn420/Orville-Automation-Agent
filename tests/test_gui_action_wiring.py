"""Focused tests for GUI-to-engine lifecycle action wiring."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_gui_module():
    spec = importlib.util.spec_from_file_location("orville_windows_gui", ROOT / "windows_gui.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_requested_actions_have_explicit_engine_mappings() -> None:
    module = _load_gui_module()
    assert set(module.GUI_ENGINE_ACTIONS) >= {
        "create_run", "pause_monitor", "resume_run", "cancel_run", "approve_task",
        "retry_run", "checkpoint", "verification", "artifact_list",
    }
    assert module.build_engine_action_request("create_run") == (
        "POST", "/api/v1/objectives", None
    )
    assert module.build_engine_action_request("pause_monitor") == ("LOCAL", "", None)
    assert module.build_engine_action_request("cancel_run", "run-1") == (
        "POST", "/api/v1/runs/run-1/cancel", None
    )
    assert module.build_engine_action_request("artifact_list") == (
        "GET", "/api/v1/artifacts", None
    )


def test_run_actions_encode_ids_and_use_streaming_execute_route() -> None:
    module = _load_gui_module()
    for action in ("resume_run", "retry_run"):
        assert module.build_engine_action_request(action, "run/with space") == (
            "POST",
            "/api/v1/objectives/run%2Fwith%20space/execute",
            {"context": {"stream": True}},
        )
    assert module.build_engine_action_request("approve_task", "run-1", "task/2") == (
        "POST",
        "/api/v1/runs/run-1/tasks/task%2F2/approval",
        {"approved": True},
    )


def test_checkpoint_and_verification_are_read_projections_and_invalid_requests_fail() -> None:
    module = _load_gui_module()
    for action in ("checkpoint", "verification"):
        assert module.build_engine_action_request(action, "run-1") == (
            "GET", "/api/v1/runs/run-1", None
        )
    for action, args in (("cancel_run", ()), ("approve_task", ("run-1",))):
        try:
            module.build_engine_action_request(action, *args)
        except ValueError as exc:
            assert "requires" in str(exc)
        else:
            raise AssertionError(f"{action} accepted incomplete identifiers")
    try:
        module.build_engine_action_request("not-an-action")
    except ValueError as exc:
        assert "unsupported" in str(exc)
    else:
        raise AssertionError("unknown action was accepted")
