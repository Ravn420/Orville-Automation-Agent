"""Focused tests for safe handling of high-impact decision domains."""

from orville_core import TaskIntake, classify_sensitive_domains, sensitive_domain_safety
from orville_core.workflow import SoftwareObjective


def test_all_sensitive_decision_domains_are_classified() -> None:
    text = "medical legal tax financial insurance real estate gambling divorce guidance"
    assert set(classify_sensitive_domains(text)) == {
        "medical",
        "legal",
        "tax",
        "financial",
        "insurance",
        "real_estate",
        "gambling",
        "major_life_decision",
    }


def test_informational_sensitive_request_warns_without_blocking() -> None:
    safety = sensitive_domain_safety("Explain general tax filing concepts")
    assert safety["detected"] is True
    assert safety["informational_only"] is True
    assert safety["professional_review_required"] is True
    assert safety["action_confirmation_required"] is False
    gate = TaskIntake.clarification_gate(SoftwareObjective("Explain general tax filing concepts"))
    assert gate["required"] is False
    assert gate["safety"]["domains"] == ["tax"]


def test_consequential_request_requires_explicit_approval_and_review() -> None:
    objective = SoftwareObjective(
        "Diagnose my symptoms and prescribe medication",
        risk_level="high",
        acceptance_criteria=["professional review"],
    )
    gate = TaskIntake.clarification_gate(objective)
    assert gate["required"] is True
    assert gate["safety"]["action_confirmation_required"] is True
    assert any("professional review" in item.lower() for item in gate["hard_gates"])
    assert "diagnosis" in gate["safety"]["prohibited_behavior"]


def test_safe_handling_never_returns_domain_advice() -> None:
    safety = sensitive_domain_safety("Should I bet my savings on this investment?")
    assert set(safety["domains"]) == {"financial", "gambling"}
    assert "qualified professional" in safety["safe_resolution"]
    assert "placing bets" in " ".join(safety["prohibited_behavior"])
