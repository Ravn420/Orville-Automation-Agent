"""Contract checks for memory-governance boundaries."""

from pathlib import Path


DOC = Path(__file__).resolve().parents[1] / "docs" / "MEMORY_GOVERNANCE.md"


def test_memory_governance_covers_required_boundaries() -> None:
    text = DOC.read_text(encoding="utf-8").lower()
    for phrase in (
        "short-term task memory",
        "long-term project memory",
        "retention",
        "deletion",
        "isolation",
        "user editing",
        "credentials",
        "auditability",
    ):
        assert phrase in text


def test_memory_governance_is_explicitly_fail_closed() -> None:
    text = DOC.read_text(encoding="utf-8").lower()
    assert "fail-closed" in text
    assert "never eligible" in text
