from pathlib import Path


NARRATIVE = Path(__file__).resolve().parents[1] / "docs" / "RUN_LIFECYCLE_NARRATIVE.md"


def test_run_lifecycle_narrative_has_canonical_order_and_evidence_contract():
    text = NARRATIVE.read_text(encoding="utf-8")

    expected_sections = [
        "### Scene 1 — Establish the workspace",
        "### Scene 2 — Submit a bounded objective",
        "### Scene 3 — Reveal the plan before execution",
        "### Scene 4 — Resolve approval deliberately",
        "### Scene 5 — Start provider-backed execution",
        "### Scene 6 — Follow live progress and partial output",
        "### Scene 7 — Exercise the controlled branch",
        "### Scene 8 — Verify the generated result",
        "### Scene 9 — Hand off a durable artifact",
        "### Scene 10 — Close the run and summarize recovery",
    ]
    positions = [text.index(section) for section in expected_sections]
    assert positions == sorted(positions)
    assert "Canonical run state sequence" in text
    assert "Durable evidence" in text
    assert "Correlation" in text


def test_run_lifecycle_narrative_covers_recovery_and_safety_boundaries():
    text = NARRATIVE.read_text(encoding="utf-8")

    for branch in ("Approval rejected", "Provider unavailable", "Pause and resume", "Cancellation", "Partial stream recovery", "Verification failure"):
        assert branch in text
    for safety_term in ("credentials", "external publication", "destructive action", "fabricated provider output"):
        assert safety_term in text
    assert "Validation checklist" in text
    assert "unresolved risks" in text
