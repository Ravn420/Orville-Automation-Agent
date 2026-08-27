from __future__ import annotations

from pathlib import Path

import pytest

from tests.repository_references import RepositoryReferenceError, resolve_repository_reference


def test_resolve_repository_reference_accepts_portable_separator_forms(tmp_path: Path) -> None:
    expected = tmp_path / "docs" / "example.md"
    assert resolve_repository_reference(tmp_path, "docs/example.md") == expected
    assert resolve_repository_reference(tmp_path, "docs\\example.md") == expected


@pytest.mark.parametrize("reference", ("", "../outside.md", "docs/../../outside.md", "/tmp/outside.md", "C:\\outside.md"))
def test_resolve_repository_reference_rejects_unsafe_forms(tmp_path: Path, reference: str) -> None:
    with pytest.raises(RepositoryReferenceError):
        resolve_repository_reference(tmp_path, reference)
