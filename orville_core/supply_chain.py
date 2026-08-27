"""Local supply-chain review primitives for untrusted packages and artifacts."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .security import SecurityViolation


REVIEW_KINDS = frozenset({"package", "script", "artifact"})


@dataclass(frozen=True)
class SupplyChainReview:
    """Value-only review result; it never stores secrets or executes a file."""

    path: str
    kind: str
    status: str
    sha256: str | None = None
    provenance: str | None = None
    findings: tuple[str, ...] = ()
    execution_allowed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "kind": self.kind,
            "status": self.status,
            "sha256": self.sha256,
            "provenance": self.provenance,
            "findings": list(self.findings),
            "execution_allowed": self.execution_allowed,
            "metadata": dict(self.metadata),
        }


def _contained(path: Path, roots: tuple[Path, ...]) -> bool:
    return any(path == root or root in path.parents for root in roots)


def review_downloaded_file(
    path: str | Path,
    *,
    kind: str,
    allowed_roots: tuple[str | Path, ...],
    expected_sha256: str | None = None,
    provenance: str | None = None,
    reviewed: bool = False,
) -> SupplyChainReview:
    """Review a local file without importing, parsing, or executing its contents.

    Downloads require a contained path, a cryptographic digest, and provenance.
    Scripts remain non-executable unless a separate trusted review explicitly marks
    them reviewed; this function does not provide that trust decision.
    """
    if kind not in REVIEW_KINDS:
        raise ValueError(f"unsupported supply-chain review kind: {kind}")
    candidate = Path(path).expanduser().resolve()
    roots = tuple(Path(root).expanduser().resolve() for root in allowed_roots)
    if not roots or not _contained(candidate, roots):
        raise SecurityViolation(f"downloaded file is outside approved roots: {candidate}")
    if not candidate.is_file():
        raise FileNotFoundError(candidate)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    findings: list[str] = []
    if not expected_sha256:
        findings.append("cryptographic checksum is required")
    elif expected_sha256.lower() != digest:
        findings.append("cryptographic checksum does not match")
    if not provenance or not provenance.strip():
        findings.append("provenance reference is required")
    if kind == "script" and not reviewed:
        findings.append("script requires independent review before execution")

    status = "approved" if not findings else "blocked"
    return SupplyChainReview(
        path=candidate.as_posix(),
        kind=kind,
        status=status,
        sha256=digest,
        provenance=provenance.strip() if provenance else None,
        findings=tuple(findings),
        execution_allowed=bool(status == "approved" and kind != "script" or status == "approved" and reviewed),
        metadata={"content_read_for_hash_only": True, "network_accessed": False},
    )
