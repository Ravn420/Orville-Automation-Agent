from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = (ROOT / "docs" / "CLEAN_ENVIRONMENT_DEPLOYMENT_VALIDATION_2026-08-28.md").read_text(encoding="utf-8")


def test_clean_environment_evidence_records_topology_and_all_check_groups():
    for phrase in (
        "Standalone local Python process",
        "disposable validation target",
        "Docker Compose",
        "24 passed in 2.20 seconds",
        "Target matrix and environment contract",
        "Deployment configuration and command validation",
        "Standalone packaging/release checks",
        "Acceptance workflows",
        "Rollback planning and recovery evidence",
        "Not deployed or production-approved",
    ):
        assert phrase in EVIDENCE


def test_clean_environment_evidence_explicitly_excludes_external_actions():
    lowered = EVIDENCE.lower()
    assert "do not contact a provider" in lowered
    assert "no deployment secret or api token was used" in lowered
    assert "not evidence of a live deployment" in lowered
    assert "automatic rollback" in lowered
    assert "-----begin" not in lowered
