from __future__ import annotations

from pathlib import Path


RECORD = Path(__file__).parents[1] / "docs" / "VERSION_CHANGE_RECORD.md"


def test_version_change_record_covers_reproducibility_dimensions() -> None:
    text = RECORD.read_text(encoding="utf-8")
    for phrase in ("Model and provider", "Connector", "Prompt", "Tool", "Dependency", "GUI", "Evidence", "SHA-256", "lockfile hash", "visual-baseline hash", "Credentials", "excluded by default"):
        assert phrase in text
