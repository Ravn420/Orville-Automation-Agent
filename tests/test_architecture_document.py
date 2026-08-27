"""Focused contract tests for the standalone Orville architecture document."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "ARCHITECTURE.md"


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def test_architecture_document_covers_requested_components() -> None:
    text = _read()
    for term in (
        "## Component model",
        "## Agents and delegation",
        "## Graph state and execution",
        "## Tools and external boundaries",
        "## Artifacts and evidence",
        "## State, persistence, and recovery",
        "## Security boundaries",
    ):
        assert term in text
    for term in ("AgentRegistry", "TaskGraph", "TaskNode", "OrchestrationEngine", "CheckpointStore", "ArtifactStore", "Independent verifiers"):
        assert term in text


def test_architecture_document_states_standalone_and_state_contracts() -> None:
    text = _read()
    assert "standalone" in text.lower()
    assert "durable" in text.lower()
    assert "resume" in text.lower()
    assert "workspace leases" in text.lower()
    assert "verification records" in text.lower()
    assert "bounded parallel workers" in text.lower()


def test_architecture_document_covers_security_and_external_side_effect_boundaries() -> None:
    text = _read()
    for term in (
        "ToolPolicy",
        "LeastPrivilegePolicy",
        "FilesystemPolicy",
        "NetworkPolicy",
        "output sanitization",
        "Untrusted-content detection",
        "explicit approval",
        "API keys",
        "must never",
        "does not silently",
    ):
        assert term in text
    assert "production" in text.lower()
