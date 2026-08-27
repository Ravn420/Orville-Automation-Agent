"""Safe, platform-neutral resolution of repository-relative test references."""
from __future__ import annotations

from pathlib import Path, PurePosixPath
import re


class RepositoryReferenceError(ValueError):
    """Raised when a documentation or catalog reference is not repository-relative."""


def resolve_repository_reference(root: Path, reference: str) -> Path:
    """Resolve a canonical repository-relative reference on every supported host.

    Documentation and catalog entries use POSIX separators as their portable
    serialized form. This helper accepts legacy Windows separators as input,
    never rewrites a valid POSIX reference into an invalid literal filename,
    and rejects absolute or parent-traversal paths before filesystem access.
    """

    normalized = str(reference).strip().replace("\\", "/")
    candidate = PurePosixPath(normalized)
    if not normalized or candidate.is_absolute() or re.match(r"^[A-Za-z]:($|/)", normalized) or ".." in candidate.parts:
        raise RepositoryReferenceError("reference must be a non-empty repository-relative path without traversal")
    return root.joinpath(*candidate.parts)
