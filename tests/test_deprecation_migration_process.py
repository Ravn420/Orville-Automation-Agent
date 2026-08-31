from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESS = (ROOT / "docs" / "DEPRECATION_MIGRATION_PROCESS.md").read_text(encoding="utf-8")


def test_deprecation_process_has_required_record_fields_and_gates():
    for phrase in (
        "Record ID",
        "Component and version",
        "Owner",
        "Replacement",
        "Announced date",
        "Last-supported date",
        "Removal target",
        "Migration guide",
        "Validation",
        "Residual risk",
        "Approval/evidence",
        "support window",
        "rollback",
        "blocked",
    ):
        assert phrase in PROCESS


def test_deprecation_process_covers_all_requested_domains_without_secrets():
    for phrase in ("Provider", "Model format", "API", "MCP version", "Runtime dependency", "GUI component"):
        assert phrase in PROCESS
    assert "bearer " not in PROCESS.lower()
    assert "sk-" not in PROCESS.lower()
    assert "private endpoints" in PROCESS
