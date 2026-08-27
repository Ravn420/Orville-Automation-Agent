"""Focused contract tests for the contributor guide."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "CONTRIBUTING.md"


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def test_contributor_guide_covers_setup_development_and_tests() -> None:
    text = _read()
    for term in (
        "## Prerequisites and local setup",
        "## Repository layout",
        "## Development workflow",
        "## Testing and validation",
        "python -m venv .venv",
        "python -m pytest",
        "python -m unittest discover",
        "python -m compileall",
    ):
        assert term in text


def test_contributor_guide_covers_review_release_and_handoffs() -> None:
    text = _read()
    for term in (
        "## Review requirements",
        "## Release and deployment procedure",
        "## Handoffs and completion",
        "second verification pass",
        "CHANGELOG.md",
        "RELEASE_NOTES.md",
        "rollback targets",
        "STATE.md",
        "TASK_GRAPH.md",
    ):
        assert term in text


def test_contributor_guide_preserves_security_and_standalone_boundaries() -> None:
    text = _read()
    for term in (
        "standalone-capable",
        "credentials",
        "bearer tokens",
        "untrusted",
        "explicit approval",
        "least privilege",
        "must not authorize",
        "production",
    ):
        assert term in text.lower()
    assert "live values" in text
    assert "No provider" not in text
