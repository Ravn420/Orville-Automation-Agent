from __future__ import annotations

from pathlib import Path


REGISTER = Path(__file__).parents[1] / "docs" / "RISK_REGISTER.md"
REQUIRED_COLUMNS = ("Risk owner", "Affected asset", "Likelihood", "Impact", "Mitigation", "Residual risk", "Review date", "Evidence")


def test_risk_register_contains_required_columns_and_active_blockers() -> None:
    text = REGISTER.read_text(encoding="utf-8")
    for column in REQUIRED_COLUMNS:
        assert column in text
    for marker in ("R-001", "R-002", "R-003", "R-004", "R-005", "still unavailable", "fail closed"):
        assert marker in text
