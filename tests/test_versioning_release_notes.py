"""Contract checks for package versioning and release notes."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_package_version_and_release_notes_are_consistent() -> None:
    package = tomllib.loads(_read("pyproject.toml"))
    version = package["project"]["version"]
    notes = _read("RELEASE_NOTES.md")
    policy = _read("docs/VERSIONING_AND_RELEASE_NOTES.md")
    assert version == "0.1.0"
    assert f"Orville {version} Release Notes" in notes
    assert f"`{version}`" in notes
    assert f"**{version}**" in policy
    assert "pyproject.toml" in policy


def test_release_notes_have_required_sections_and_validation_scope() -> None:
    notes = _read("RELEASE_NOTES.md")
    for section in ("## Added", "## Changed", "## Security and privacy", "## Validation", "## Upgrade and rollback", "## Known limitations"):
        assert section in notes
    assert "Python 3.10+" in notes
    assert "live provider" in notes.lower()
    assert "production" in notes.lower()


def test_versioning_policy_defines_semver_and_secret_safe_release_rules() -> None:
    policy = _read("docs/VERSIONING_AND_RELEASE_NOTES.md")
    assert "Semantic Versioning 2.0.0" in policy
    assert all(label in policy for label in ("Major", "Minor", "Patch"))
    assert "API keys" in policy and "never included" in policy
    assert "backup" in policy.lower() and "rollback" in policy.lower()
    assert not re.search(r"(?:sk-|AIza|Bearer\s+)[A-Za-z0-9._-]{16,}", policy + _read("RELEASE_NOTES.md"))
