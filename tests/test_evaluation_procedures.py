from __future__ import annotations

from pathlib import Path


PROCEDURES = Path(__file__).parents[1] / "docs" / "EVALUATION_PROCEDURES.md"


def test_evaluation_procedure_contract_covers_all_triggers_and_safeguards() -> None:
    text = PROCEDURES.read_text(encoding="utf-8")
    for phrase in ("Pre-release", "Post-release", "Incident-triggered", "Periodic", "Run ID", "dataset IDs", "trace comparison", "Stop condition", "blocked", "Prompt and tool-payload capture remains disabled"):
        assert phrase in text
