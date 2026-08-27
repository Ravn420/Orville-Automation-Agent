import pytest

from orville_core.automation import (
    StepExecutionMode,
    WorkflowExecutor,
    WorkflowStep,
    step_execution_mode,
    validate_workflow_steps,
)


def test_steps_default_to_deterministic_mode() -> None:
    step = WorkflowStep("validate", "validate_input")
    assert step_execution_mode(step) is StepExecutionMode.DETERMINISTIC
    validate_workflow_steps((step,))


def test_agentic_step_uses_explicit_agentic_handler() -> None:
    step = WorkflowStep("draft", "draft_text", {"execution_mode": "agentic"})
    executor = WorkflowExecutor(
        agentic_handlers={"draft_text": lambda context: {"draft": "generated"}}
    )
    assert executor.execute((step,), {})["draft"] == "generated"


def test_safety_critical_agentic_step_is_rejected_before_handler_execution() -> None:
    called = False

    def handler(context: dict) -> dict:
        nonlocal called
        called = True
        return {}

    step = WorkflowStep(
        "persist",
        "save_state",
        {"execution_mode": "agentic", "safety_category": "persistence"},
    )
    with pytest.raises(PermissionError, match="must be deterministic"):
        WorkflowExecutor(agentic_handlers={"save_state": handler}).execute((step,), {})
    assert called is False


def test_unknown_execution_mode_fails_closed() -> None:
    step = WorkflowStep("step", "handler", {"execution_mode": "ambiguous"})
    with pytest.raises(ValueError, match="unsupported workflow step execution mode"):
        validate_workflow_steps((step,))


def test_all_safety_critical_categories_reject_agentic_mode() -> None:
    for category in ("safety_critical", "authorization", "validation", "persistence", "artifact_integrity"):
        step = WorkflowStep(
            f"step-{category}",
            "handler",
            {"execution_mode": "agentic", "safety_category": category},
        )
        with pytest.raises(PermissionError):
            validate_workflow_steps((step,))
