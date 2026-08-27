"""Focused tests for the GUI-to-engine API contract."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "GUI_ENGINE_API_CONTRACT.md"


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def test_contract_covers_all_requested_resources_and_envelopes() -> None:
    text = _read()
    for term in (
        "Objective", "Task graph", "Run", "Checkpoint", "Provider", "Local model",
        "Verification record", "Artifact", "Approval", "Event stream", "api_version",
        "request_id", "payload", "resource", "events", "error",
    ):
        assert term in text


def test_contract_defines_engine_state_security_and_approval_boundaries() -> None:
    text = _read()
    for term in (
        "engine owns state transitions", "waiting_approval", "idempotency",
        "authenticate every request", "authorize the resource and operation",
        "least-privilege", "scope-matched approval", "redacted audit record",
        "blocked or partial", "Independent verification",
    ):
        assert term in text


def test_contract_defines_events_errors_compatibility_and_secret_exclusions() -> None:
    text = _read()
    for term in (
        "sequence number", "bounded and resumable", "stable error classes",
        "Additive response fields", "Unknown response fields", "API keys",
        "raw credentials", "prompts", "cookies", "sensitive paths",
        "does not claim that a deployed backend bridge or GUI wiring is complete",
    ):
        assert term in text
