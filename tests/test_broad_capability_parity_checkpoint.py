from pathlib import Path


ROOT = Path(__file__).parents[1]
CHECKPOINT = ROOT / "artifacts" / "BROAD_CAPABILITY_PARITY_CHECKPOINT_2026-08-28.md"


def test_checkpoint_covers_broad_capability_families() -> None:
    text = CHECKPOINT.read_text(encoding="utf-8")
    for family in (
        "Intake, planning, orchestration, and verification",
        "Provider and model execution",
        "Coding and artifact workflows",
        "Connectors and external integrations",
        "Schedules and notifications",
        "GUI and live execution",
        "Observability and evaluation",
        "Deployment and operations",
        "Security, governance, accessibility, and recovery",
    ):
        assert family in text


def test_checkpoint_links_repository_evidence_and_validation() -> None:
    text = CHECKPOINT.read_text(encoding="utf-8")
    assert "MANUS_PARITY_REPORT.md" in text
    assert "test_broad_capability_parity_checkpoint.py" in text
    assert "python -m compileall" in text


def test_checkpoint_does_not_claim_literal_manus_parity() -> None:
    text = CHECKPOINT.read_text(encoding="utf-8")
    assert "not a claim that Orville literally reproduces" in text
    assert "are not reproduced" in text
    assert "No credential, token, cookie" in text
    assert "fail-closed" in text
