from pathlib import Path


DOC = Path(__file__).parents[1] / "docs" / "STANDALONE_WINDOWS_EQUIVALENTS.md"


def test_standalone_equivalents_document_covers_required_families() -> None:
    text = DOC.read_text(encoding="utf-8")
    for family in (
        "Connectors and external apps",
        "Schedules and recurring work",
        "Notifications",
        "Deployment helpers",
        "Observability",
    ):
        assert family in text


def test_document_explicitly_separates_manus_only_behavior() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert "not reproduced literally" in text
    assert "optional adapters" in text
    assert "unavailable" in text
    assert "awaiting_approval" in text


def test_standalone_contract_forbids_secret_and_silent_side_effects() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert "must not embed secrets" in text
    assert "fail closed" in text
    assert "must not deploy to a production account" in text
    assert "OTLP export is opt-in" in text
