from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = (ROOT / "docs" / "PRODUCTION_ACCEPTANCE_EVIDENCE_2026-08-28.md").read_text(encoding="utf-8")


def test_production_acceptance_evidence_covers_all_requested_areas():
    for phrase in (
        "Production acceptance workflows",
        "Security",
        "Accessibility",
        "Performance",
        "Repository coding evaluation",
        "Packaging and standalone release",
        "Deployment",
        "Rollback and disaster recovery",
        "51 passed, 2 failed",
        "Not production-approved",
    ):
        assert phrase in EVIDENCE


def test_production_acceptance_evidence_has_safe_boundaries():
    lowered = EVIDENCE.lower()
    assert "no production deployment" in lowered
    assert "no credentials" in lowered
    assert "-----begin" not in lowered
    assert "sk-live" not in lowered
