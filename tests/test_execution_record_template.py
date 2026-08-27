"""Checks for the reusable execution-record limitation template."""
from pathlib import Path


TODO = Path(__file__).resolve().parents[1] / "TODO.md"


def test_execution_record_template_requires_limitation_categories() -> None:
    text = TODO.read_text(encoding="utf-8")
    template = text[text.index("Use the following record for each future objective:"):text.index("## 20. Immediate Next Execution Sequence")]
    assert "### Known limitations" in template
    for category in (
        "Scope limitations:",
        "Environment or provider limitations:",
        "Validation limitations:",
        "Unresolved risks and follow-up dependencies:",
    ):
        assert category in template


def test_limitation_checklist_remains_a_template_placeholder() -> None:
    text = TODO.read_text(encoding="utf-8")
    assert "TODO-e22984a50c7a" in text
    assert "Known limitations recorded" in text
    assert "Use the following record for each future objective:" in text
    assert "### Known limitations" in text
