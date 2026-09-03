from __future__ import annotations

from pathlib import Path


POLICY = Path(__file__).parents[1] / "docs" / "DEPRECATION_AND_MIGRATION_POLICY.md"


def test_deprecation_policy_covers_all_surfaces_and_gates() -> None:
    text = POLICY.read_text(encoding="utf-8")
    normalized = text.casefold()
    for phrase in ("Provider", "Model format", "API", "MCP", "Runtime dependency", "GUI component", "support deadline", "compatibility check", "non-destructive conversion preview", "contract tests", "rollback", "separate approval", "Never store credentials"):
        assert phrase.casefold() in normalized
