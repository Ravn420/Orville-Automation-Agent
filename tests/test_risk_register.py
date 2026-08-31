from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "docs" / "RISK_REGISTER.md"
REQUIRED_COLUMNS = (
    "Risk owner",
    "Affected asset",
    "Likelihood",
    "Impact",
    "Mitigation",
    "Residual risk",
    "Review date",
    "Evidence",
)


def test_risk_register_has_required_columns_and_rows():
    text = REGISTER.read_text(encoding="utf-8")
    header = next(line for line in text.splitlines() if line.startswith("| ID |"))
    for column in REQUIRED_COLUMNS:
        assert column in header
    rows = [line for line in text.splitlines() if line.startswith("| R-")]
    assert len(rows) >= 8
    for row in rows:
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        assert len(cells) == 10
        assert all(cells)
        assert "2026-11-28" in row
        assert "`docs/" in row or "`orville_core/" in row


def test_risk_register_contains_no_secret_like_values():
    text = REGISTER.read_text(encoding="utf-8")
    assert "bearer " not in text.lower()
    assert "sk-" not in text.lower()
    assert "token value" not in text.lower()
